import sqlite3
from flask import Flask, g
from modules import awsModules

awsDir = awsModules.awsDir()

@app.before_reqst
def before_request():
  g.db = awsModules.awsDB()

@app.teardown_request
def teardown_request(exception):
  db = getattr(g, 'db', None)
  if db is not None:
    db.close()

if __name__ == '__main__':
  app.run(host='0.0.0.0')

