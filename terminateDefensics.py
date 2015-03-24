#!/usr/bin/python

import argparse
import boto.ec2
import os
import datetime
import sys
from pprint import pprint

parser = argparse.ArgumentParser(description='Permanently delete instances from AWS')
parser.add_argument('-O', '--aws-access-key', metavar='key', help='AWS Access Key ID. Defaults to the value of the AWS_ACCESS_KEY environment variable (if set)')
parser.add_argument('-W', '--aws-secret-key', metavar='key', help='AWS Secret Access Key. Defaults to the value of the AWS_SECRET_KEY environment variable (if set)')
parser.add_argument('-D', '--dry-run', action='store_true', default=False, help='Test command, but do not actually run command (default: %(default)s)')
megroup = parser.add_mutually_exclusive_group(required=True)
megroup.add_argument('-r', '--res-id', help='reservation id')
megroup.add_argument('-i', '--instance-id', help='image id')
megroup.add_argument('-n', '--name', help='Base machine name. Requires admin flag to be set')
parser.add_argument('-a', '--admin', help='administrator')
args = parser.parse_args()

if args.name:
  if not args.admin:
    sys.exit("To avoid deleteing machines assigned to other admins, please provide your name using the -a/--admin flag")

if args.aws_access_key:
  conn = boto.ec2.connect_to_region('us-west-1',aws_access_key_id=args.aws_access_key,aws_secret_access_key=args.aws_secret_key)
else:
  conn = boto.ec2.connect_to_region('us-west-1',aws_access_key_id=os.environ['AWS_ACCESS_KEY'],aws_secret_access_key=os.environ['AWS_SECRET_KEY'])

if args.res_id:
  reservations = conn.get_all_reservations()
  for r in reservations:
    if r.id == args.res_id:
      instances = r.instances
      commonName = instances[0].tags['Name'].split(':')[0]
      for i in instances:
        conn.terminate_instances([str(i.id)], dry_run=args.dry_run)
        print str(i.tags['Name']) + ' has been terminated'
      conn.delete_key_pair(commonName)
      os.remove(str(args.res_id))
      os.remove('.aws/' + commonName + '.pem')

if args.name:
  instances = conn.get_only_instances()
  for i in instances:
    if i.tags['Name'].startswith(args.name + ":") and i.tags['Admin'] == args.admin:
      conn.terminate_instances([str(i.id)], dry_run=args.dry_run)
      conn.delete_key_pair(args.name)
      os.remove('.aws/' + args.name + '.pem')
      print str(i.tags['Name']) + ' has been terminated'
