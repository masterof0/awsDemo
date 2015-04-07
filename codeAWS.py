#!/usr/bin/python

import sqlite3
from flask import Flask, g, render_template, request, url_for
from flask_bootstrap import Bootstrap
from wtforms import BooleanField, StringField, validators
from flask_wtf import Form 
from modules import awsModules

awsDir = awsModules.awsDir()

app = Flask(__name__)
Bootstrap(app)

class updateForm(Form):
  res_id = StringField('Reservation ID', validators=[validators.Length(min=10, max=10)])

@app.before_request
def before_request():
  g.db = awsModules.awsDB()

@app.teardown_request
def teardown_request(exception):
  db = getattr(g, 'db', None)
  if db is not None:
    db.close()

@app.route('/')
def hello_world():
  return 'Hello World'

@app.route('/instances')
def show_instances():
  cur = g.db.execute('select * from instances;')
  instances = [dict(hostname=row[2], instance_id=row[0], reservation_id=row[1], public_ip=row[3], password=row[4], state=row[5]) for row in cur.fetchall()]
  return render_template('instances.html', entries=instances, pageTitle="AWS Instances")

@app.route('/update', methods=('GET', 'POST'))
def update():
  form = updateForm(csrf_enabled=False)
  return render_template('update.html', form=form)
  
@app.errorhandler(404)
def page_not_found(error):
    return 'This page does not exist', 404

if __name__ == '__main__':
  app.run(host='0.0.0.0',debug=True)

