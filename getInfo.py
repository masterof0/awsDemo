#!/usr/bin/python

import argparse, boto.ec2, os, sqlite3
from modules import awsModules
#from pprint import pprint

parser = argparse.ArgumentParser(description='Get details on images basd on reservation, instance id, hostname, or admin')
parser.add_argument('-O', '--aws-access-key', metavar='key', help='AWS Access Key ID. Defaults to the value of the AWS_ACCESS_KEY environment variable (if set)')
parser.add_argument('-W', '--aws-secret-key', metavar='key', help='AWS Secret Access Key. Defaults to the value of the AWS_SECRET_KEY environment variable (if set)')
#parser.add_argument('--update', action='store_true', default=False, help='Update database (default: %(default)s)')
megroup = parser.add_mutually_exclusive_group(required=True)
megroup.add_argument('-r', '--res-id', help='reservation id')
megroup.add_argument('-i', '--instance-id', help='image id')
args = parser.parse_args()

conn = awsModules.connect(args)
awsDir = awsModules.awsDir()
sql = sqlite3.connect(awsDir + 'aws.db')
awsDB = sql.cursor()

if args.res_id:
  awsDB.execute("delete from instances where reservation_id=?;", (args.res_id))
  reservations = conn.get_all_reservations()
  for r in reservations:
    if r.id == args.res_id:
      instances = r.instances
      for i in instances:
        passwd = awsModules.getPass(args, i, awsDir)
        awsDB.execute("insert into instances values (?,?,?,?,?,?)", (i.id, args.res_id, i.tags['Name'], i.ip_address, passwd, str(i._state)))

if args.instance_id:
  instances = conn.get_only_instances()
  for i in instances:
    if i.id == args.instance_id:
      passwd = awsModules.getPass(args, i, awsDir)
      awsDB.execute("update instances set public_ip=?, password=?, state=? where instance_id=?;", (i.ip_address, passwd, str(i._state), i.id))

sql.commit()
sql.close()

