#!/usr/bin/python

import argparse
import boto.ec2
import os
from pprint import pprint

parser = argparse.ArgumentParser(description='Get details on images basd on reservation, instance id, hostname, or admin')
parser.add_argument('-O', '--aws-access-key', metavar='key', help='AWS Access Key ID. Defaults to the value of the AWS_ACCESS_KEY environment variable (if set)')
parser.add_argument('-W', '--aws-secret-key', metavar='key', help='AWS Secret Access Key. Defaults to the value of the AWS_SECRET_KEY environment variable (if set)')
megroup = parser.add_mutually_exclusive_group(required=True)
megroup.add_argument('-r', '--res-id', help='reservation id')
megroup.add_argument('-i', '--instance-id', help='image id')
#megroup.add_argument('-a', '--admin', help='administrator')
#parser.add_argument('name', help='Name of instances')
args = parser.parse_args()

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
      with open(str(r.id), 'w') as log:
        print '\n{:<25} {:<17} {:<17} {:<17} {:<17}'.format( 'Hostname', 'Instance ID', 'Public IP', 'Password', 'State' )
        print '{:#<93}'.format('')
        log.write('\n{:<25} {:<17} {:<17} {:<17} {:<17}'.format( 'Hostname', 'Instance ID', 'Public IP', 'Password', 'State' ) + '\n')
        log.write('{:#<93}'.format('') + '\n')
        for i in instances:
#          pprint(i.__dict__)
          if args.aws_access_key:
            cmd = 'ec2-get-password --region us-west-1 -O ' + str(args.aws_access_key) + ' -W ' + str(args.aws_secret_key) + ' ' + str(i.id) + ' -k .aws/' + str(commonName) + ".pem"
          else:
            cmd = 'ec2-get-password --region us-west-1 ' + str(i.id) + ' -k .aws/' + str(commonName) + ".pem"
          passwd = os.popen(cmd).read().strip()
          print '{:<25} {:<17} {:<17} {:<17} {:<17}'.format( i.tags['Name'], i.id, i.ip_address , passwd, i._state ) 
          log.write('{:<25} {:<17} {:<17} {:<17} {:<17}'.format( i.tags['Name'], i.id, i.ip_address , passwd, i._state) + '\n')
        log.write('\n')
        print
      log.closed
