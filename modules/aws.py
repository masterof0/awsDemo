import boto.ec2, os, sqlite3

def connect(location, access, secret):
    return boto.ec2.connect_to_region(location,aws_access_key_id=access,aws_secret_access_key=secret)

def awsDir():
  return "/vagrant/.aws/"

def awsDB():
  return sqlite3.connect(awsDir() + 'aws.db')

def getPass(access, secret, i, awsDir):
  baseName = i.tags['Name'].split(':')[0]
  cmd = 'ec2-get-password --region us-west-1 -O ' + access + ' -W ' + secret + ' ' + i.id + ' -k ' + awsDir + baseName + '.pem'
  return os.popen(cmd).read().strip()

def delKey(pem, admin):
  location = pem.rsplit('_', 1)[1]
  connect(location,admin[0]['access'],admin[0]['secret']).delete_key_pair(pem)
  if os.path.exists(awsDir() + pem + '.pem'):
    os.remove(awsDir() + pem + '.pem')

def run_script(name):
  subprocess.call(name)
