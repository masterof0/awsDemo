import boto.ec2, os

def connect(args):
  if args.aws_access_key:
    return boto.ec2.connect_to_region('us-west-1',aws_access_key_id=args.aws_access_key,aws_secret_access_key=args.aws_secret_key)
  else:
    return boto.ec2.connect_to_region('us-west-1',aws_access_key_id=os.environ['AWS_ACCESS_KEY'],aws_secret_access_key=os.environ['AWS_SECRET_KEY'])

def awsDir():
  return "/vagrant/.aws/"
