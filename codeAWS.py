#!/usr/bin/python

import sqlite3, boto.ec2, os, glob
from flask import Flask, g, render_template, request, url_for, redirect, flash
from flask_bootstrap import Bootstrap
from wtforms import StringField, SelectField, IntegerField, validators
from flask_wtf import Form 
from modules import aws

app = Flask(__name__)
app.secret_key = '\xc8`\x1dB\xb9~\xb4w|\xafd\xc9%\xc9\x05\xe5!&\x062\x81h\x81\xb8'
Bootstrap(app)

#Check for .aws directory and create if needed
if not os.path.isdir(aws.awsDir()):
  os.makedirs(aws.awsDir())

class userSetup(Form):
  username = StringField('username')
  accessKey = StringField('accessKey')
  secretKey = StringField('secretKey')

class reservation(Form):
  num = IntegerField('num', [validators.Required(), validators.NumberRange(min=1, max=10)])
  iType = SelectField('iType', choices=[('t2.micro', 'T2 Micro (preferred)'), ('t2.medium', 'T2 Medium'), ('m3.xlarge', 'M3 X-Large (training)')])
  name = StringField('name', [validators.Required()])

def getCreds():
  cur = g.db.execute('select * from admins;')
  return [dict(username=row[0], access=row[1], secret=row[2]) for row in cur.fetchall()]

@app.before_request
def before_request():
  g.db = aws.awsDB()

@app.teardown_request
def teardown_request(exception):
  db = getattr(g, 'db', None)
  if db is not None:
    db.close()

@app.route('/')
def index():
  #Check for database and create table if not created
  cur = g.db.execute('select name from sqlite_master where type="table" and name="instances";')
  if not cur.fetchone():
    g.db.execute("create table instances(instance_id, reservation_id, name, public_ip, password, state, key, type);")
  cur = g.db.execute('select name from sqlite_master where type="table" and name="admins";')
  if not cur.fetchone():
    g.db.execute("create table admins(user, access_key, secret_key);")
  return redirect('instances', code=302)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
  form = userSetup()
  if request.method == "GET":
    return render_template('setup.html', form=form, pageTitle="AWS Setup")
  if request.method == "POST":
#    g.db.execute("delete from admins where user='%s';" % form.username.data)
    g.db.execute("drop table admins")
    g.db.execute("create table admins(user, access_key, secret_key);")
    g.db.execute("insert into admins values (?,?,?)", (form.username.data,form.accessKey.data, form.secretKey.data))
    g.db.commit()
    flash("User " + form.username.data + " has been added")
    return redirect('instances', code=302)

@app.route('/instances', methods=['GET', 'POST'])
def instances():
  if request.method == "POST":
    admin = getCreds()
    action = request.form['action']
#    resType = request.form['resType']
#    resValue = request.form['resValue']
    if action == 'update':
      resType = request.form['resType']
      resValue = request.form['resValue']
      if resType == 'instance_id':
        instances = aws.connect(admin[0]['access'],admin[0]['secret']).get_only_instances(instance_ids=[resValue])
        for i in instances: 
          passwd = aws.getPass(admin[0]['access'],admin[0]['secret'], i, aws.awsDir())
          g.db.execute("update instances set public_ip=?, password=?, state=?, type=? where instance_id=?;", (i.ip_address, passwd, str(i._state), i.instance_type, i.id))
          flash('Instance ' + i.tags['Name'] + ' has been successfully updated')
      g.db.commit()
    if action == "updateAll":
      instances = aws.connect(admin[0]['access'],admin[0]['secret']).get_only_instances()
      for i in instances:
        if i.tags['Admin'] == admin[0]['username'] and i.tags['Status'] == 'training':
          passwd = aws.getPass(admin[0]['access'],admin[0]['secret'], i, aws.awsDir())
          g.db.execute("update instances set public_ip=?, password=?, state=?, type=? where instance_id=?;", (i.ip_address, passwd, str(i._state), i.instance_type, i.id))
          flash('Instance ' + i.tags['Name'] + ' has been successfully updated')
      g.db.commit()
    if action == 'terminate':
      resValue = request.form['resValue']
      aws.connect(admin[0]['access'],admin[0]['secret']).terminate_instances([resValue])
      g.db.execute("delete from instances where instance_id='%s';" % resValue)
      g.db.commit()
      flash('Instance ' + resValue + ' has been successfully terminated')
    if action == "terminateAll":
      instances = aws.connect(admin[0]['access'],admin[0]['secret']).get_only_instances()
      for i in instances:
        if i.tags['Admin'] == admin[0]['username'] and i.tags['Status'] == 'training':
          aws.connect(admin[0]['access'],admin[0]['secret']).terminate_instances([i.id])
          g.db.execute("delete from instances where instance_id='%s';" % i.id)
          flash('Instance ' + i.tags['Name'] + ' has been successfully terminated')
      g.db.commit()
    return redirect('instances', code=302)
  if request.method == "GET":
    cur = g.db.execute('select * from instances;')
    instances = [dict(hostname=row[2], instance_id=row[0], reservation_id=row[1], public_ip=row[3], password=row[4], state=row[5], itype=row[7]) for row in cur.fetchall()]
    return render_template('instances.html', entries=instances, pageTitle="AWS Instances")

@app.route('/reservation', methods=['GET', 'POST'])
def makeReservation():
  form = reservation()
  admin = getCreds()
  if request.method == "GET":
    return render_template('reservation.html', form=form, pageTitle="AWS Reservation")
  if request.method == "POST":
    #Check for existing keys and create if needed
    if aws.connect(admin[0]['access'],admin[0]['secret']).get_key_pair(form.name.data):
      if not os.path.exists(aws.awsDir() + form.name.data + '.pem'): 
        return ("This name is already taken. Please try again with new name")
    else:
      key = aws.connect(admin[0]['access'],admin[0]['secret']).create_key_pair(form.name.data)
      key.save(aws.awsDir())
    #Create reservations
    res = aws.connect(admin[0]['access'],admin[0]['secret']).run_instances('ami-ff21c0bb',max_count=form.num.data, key_name=form.name.data, security_groups=['sg_training'], instance_type=form.iType.data)
    flash("Your reservation id for this defensics request is: " + str(res.id))
    flash("Please note it may take up to 30 minutes for the images to launch and be fully available")
    instances = res.instances
    #Write instance information to database and add appropriate tags
    for index, i in enumerate(instances):
      commonName = form.name.data + ':' + str(index) + '_' + res.id
      g.db.execute("insert into instances values (?,?,?,?,null,?,?,?)", (i.id, res.id, commonName, i.ip_address, str(i._state), form.name.data, i.instance_type))
      i.add_tag('Name',value=commonName)
      i.add_tag('Admin',value=admin[0]['username'])
      i.add_tag('Status',value='training')
    g.db.commit()
    return redirect('instances', code=302)

@app.route('/keys', methods=["GET", "POST"])
def manageKeys():
  if request.method == "GET":
    os.chdir('/vagrant/.aws')
    pems = []
    for file in glob.glob("*.pem"):
      pems.append(os.path.splitext(file)[0])
    return render_template('keys.html', keys=pems, pageTitle="AWS Keys")
  if request.method == "POST":
    key = request.form['key']
    admin = getCreds()
    aws.connect(admin[0]['access'],admin[0]['secret']).delete_key_pair(key)
    flash ("Successfully deleted remote key: " + key)
    if os.path.exists(aws.awsDir() + key + '.pem'):
      os.remove(aws.awsDir() + key + '.pem')
    flash ("Successfully deleted local key: " + key + ".pem")
    return redirect('keys', code=302)

@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404

if __name__ == '__main__':
  app.run(host='0.0.0.0',debug=True)

