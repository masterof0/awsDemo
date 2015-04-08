#!/usr/bin/python

import sqlite3, boto.ec2, os
from flask import Flask, g, render_template, request, url_for, redirect, flash
from flask_bootstrap import Bootstrap
from wtforms import BooleanField, StringField, SelectField, validators
from flask_wtf import Form 
from modules import aws

awsDir = aws.awsDir()

app = Flask(__name__)
app.secret_key = '\xc8`\x1dB\xb9~\xb4w|\xafd\xc9%\xc9\x05\xe5!&\x062\x81h\x81\xb8'
Bootstrap(app)

class updateForm(Form):
  type = SelectField('resource', choices=[('res_id','Reservation ID'),('instance_id','Instance ID')])
  value = StringField('value')

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
  return redirect('instances', code=302)

@app.route('/instances')
def instances():
  cur = g.db.execute('select * from instances;')
  instances = [dict(hostname=row[2], instance_id=row[0], reservation_id=row[1], public_ip=row[3], password=row[4], state=row[5]) for row in cur.fetchall()]
  return render_template('instances.html', entries=instances, pageTitle="AWS Instances")

@app.route('/update', methods=['GET','POST'])
def update():
  form = updateForm()#csrf_enabled=False)
  if request.method == "GET":
    return render_template('update.html', form=form)
  if request.method == "POST":
    if form.type.data == 'res_id':
      g.db.execute("delete from instances where reservation_id='%s';" % form.value.data)
      reservations = aws.connect('','').get_all_reservations()
      for r in reservations:
        if r.id == form.value.data:
          instances = r.instances
          for i in instances:
            passwd = aws.getPass('','', i, awsDir)
            g.db.execute("insert into instances values (?,?,?,?,?,?)", (i.id, form.value.data, i.tags['Name'], i.ip_address, passwd, str(i._state)))  
      g.db.commit()
      flash('Reservation ' + form.type.data + ' has been successfully updated')
      return redirect('instances', code=302)
#      return "reservation " + form.value.data + " has been successfully updated "
 
@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404

if __name__ == '__main__':
  app.run(host='0.0.0.0',debug=True)

