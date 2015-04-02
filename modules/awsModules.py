import boto.ec2, os, sqlite3

def connect(args):
  if args.aws_access_key:
    return boto.ec2.connect_to_region('us-west-1',aws_access_key_id=args.aws_access_key,aws_secret_access_key=args.aws_secret_key)
  else:
    return boto.ec2.connect_to_region('us-west-1',aws_access_key_id=os.environ['AWS_ACCESS_KEY'],aws_secret_access_key=os.environ['AWS_SECRET_KEY'])

def awsDir():
  return "/vagrant/.aws/"

def awsDB():
  return sqlite3.connect(awsDir() + 'aws.db')

def getPass(args, i, awsDir):
  baseName = i.tags['Name'].split(':')[0]
  if args.aws_access_key:
    cmd = 'ec2-get-password --region us-west-1 -O ' + args.aws_access_key + ' -W ' + args.aws_secret_key + ' ' + i.id + ' -k ' + awsDir + baseName + '.pem'
  else:
    cmd = 'ec2-get-password --region us-west-1 ' + i.id + ' -k ' + awsDir + baseName + '.pem'
  return os.popen(cmd).read().strip()
