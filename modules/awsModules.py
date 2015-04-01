import boto.ec2, os

def connect(args):
  if args.aws_access_key:
    return boto.ec2.connect_to_region('us-west-1',aws_access_key_id=args.aws_access_key,aws_secret_access_key=args.aws_secret_key)
  else:
    return boto.ec2.connect_to_region('us-west-1',aws_access_key_id=os.environ['AWS_ACCESS_KEY'],aws_secret_access_key=os.environ['AWS_SECRET_KEY'])

def awsDir():
  return "/vagrant/.aws/"

def getPass(args, i, awsDir):
  if args.aws_access_key:
    cmd = 'ec2-get-password --region us-west-1 -O ' + str(args.aws_access_key) + ' -W ' + str(args.aws_secret_key) + ' ' + str(i.id) + ' -k ' + awsDir + str(i.tags['Name']) + '.pem'
  else:
    cmd = 'ec2-get-password --region us-west-1 ' + str(i.id) + ' -k ' + awsDir + str(i.tags['Name']) + '.pem'
  return os.popen(cmd).read().strip()
