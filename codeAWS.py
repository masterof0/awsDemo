#!/usr/bin/python

import sqlite3
from flask import Flask, g, render_template, request, url_for
from modules import awsModules

app = Flask(__name__)
awsDir = awsModules.awsDir()

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
  return str(instances)

if __name__ == '__main__':
  app.run(host='0.0.0.0',debug=True)

