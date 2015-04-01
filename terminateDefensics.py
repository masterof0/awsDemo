#!/usr/bin/python

import argparse, boto.ec2, os, datetime, sys, sqlite3
from modules import awsModules

parser = argparse.ArgumentParser(description='Permanently delete instances from AWS')
parser.add_argument('-O', '--aws-access-key', metavar='key', help='AWS Access Key ID. Defaults to the value of the AWS_ACCESS_KEY environment variable (if set)')
parser.add_argument('-W', '--aws-secret-key', metavar='key', help='AWS Secret Access Key. Defaults to the value of the AWS_SECRET_KEY environment variable (if set)')
parser.add_argument('-D', '--dry-run', action='store_true', default=False, help='Test command, but do not actually run command (default: %(default)s)')
megroup = parser.add_mutually_exclusive_group(required=True)
megroup.add_argument('-r', '--res-id', help='reservation id')
megroup.add_argument('-i', '--instance-id', help='image id')
megroup.add_argument('-n', '--name', help='Machine name or base name. Requires admin flag to be set')
parser.add_argument('-a', '--admin', help='administrator')
args = parser.parse_args()

if args.name:
  if not args.admin:
    sys.exit("To avoid deleteing machines assigned to other admins, please provide your name using the -a/--admin flag")

conn = awsModules.connect(args)
awsDir = awsModules.awsDir()
sql = sqlite3.connect(awsDir + 'aws.db')
awsDB = sql.cursor()

def deleteKey(baseName):
  conn.delete_key_pair(baseName)
  os.remove(awsDir + baseName + '.pem')
  print "Deleting " + baseName + " keys"
  
if args.res_id:
  reservations = conn.get_all_reservations()
  for r in reservations:
    if r.id == args.res_id:
      instances = r.instances
      baseName = instances[0].tags['Name'].split(':')[0]
      for i in instances:
        conn.terminate_instances([i.id], dry_run=args.dry_run)
        print i.tags['Name'] + ' has been terminated'
      awsDB.execute("delete from instances where reservation_id='%s';" % args.res_id)
      deleteKey(baseName)
      if os.path.exists(str(args.res_id)):
        os.remove(args.res_id)

if args.name:
  instances = conn.get_only_instances()
  baseName = ''
  for i in instances:
    if i.tags['Name'].startswith(args.name + ":") and i.tags['Admin'] == args.admin:
      conn.terminate_instances([i.id], dry_run=args.dry_run)
      print i.tags['Name'] + ' has been terminated'
      awsDB.execute("delete from instances where instance_id='%s';" % i.id)
      baseName = args.name 
    if i.tags['Name'] == args.name and i.tags['Admin'] == args.admin:
      conn.terminate_instances([i.id], dry_run=args.dry_run)
      print str(i.tags['Name']) + ' has been terminated'
      awsDB.execute("delete from instances where instance_id='%s';" % i.id)
  if baseName:
    deleteKey(baseName)

sql.commit()
sql.close()
