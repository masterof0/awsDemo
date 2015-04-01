#! /usr/bin/python

import argparse, boto.ec2, time, datetime, os, sys, sqlite3
from modules import awsModules

parser = argparse.ArgumentParser(description="Build defensics workstations for training, or demonstrations, in AWS")
parser.add_argument('-n', '--num', type=int, default=1, help='Number of instances to deploy (default: %(default)s)')
parser.add_argument('-i', '--instance', metavar='type', default='m3.xlarge', help='Type of instance to run. For more information on instances, go to http://aws.amazon.com/ec2/instance-types (default: %(default)s)')
parser.add_argument('-O', '--aws-access-key', metavar='key', help='AWS Access Key ID. Defaults to the value of the AWS_ACCESS_KEY environment variable (if set)')
parser.add_argument('-W', '--aws-secret-key', metavar='key', help='AWS Secret Access Key. Defaults to the value of the AWS_SECRET_KEY environment variable (if set)')
parser.add_argument('-D', '--dry-run', action='store_true', default=False, help='Test command, but do not actually run command (default: %(default)s)')
parser.add_argument('admin', help='username that will administer instances (i.e. cjohnson)')
parser.add_argument('name', help='Base name of machine')
args = parser.parse_args()
#print args

reservation, instances = ([] for l in range (2))
awsDir = awsModules.awsDir()

if not os.path.isdir(awsDir):
  os.makedirs(awsDir)

#Set up connection to AWS
conn = awsModules.connect(args)

#Create key pair
if conn.get_key_pair(str(args.name)):
  if not os.path.exists(awsDir + str(args.name) + '.pem'):
    sys.exit("This name is already taken. Please launch again with new name")
else:
    key = conn.create_key_pair(str(args.name))
    key.save(awsDir)

#Create reservation
reservation = conn.run_instances('ami-ff21c0bb',max_count=args.num, key_name=args.name, security_groups=['sg_training'], instance_type=args.instance, dry_run=args.dry_run)
instances = reservation.instances
print "Your reservation id for this defensics request is: " + str(reservation.id)
print "Please note it may take up to 20 minutes for the images to launch and be fully available"
print "If you need information on your reservation, please check the local log .aws.log"

#Log instance information
sql = sqlite3.connect(awsDir + 'aws.db')
awsDB = sql.cursor()

awsDB.execute('select name from sqlite_master where type="table" and name="instances";')
if not awsDB.fetchone():
  awsDB.execute("create table instances(instance_id, reservation_id, name, public_ip, password, state);")

for index, i in enumerate(instances):
  commonName = str(args.name) + ':' + str(index) + '_' + str(reservation.id)
  awsDB.execute("insert into instances values (?,?,?,?,null,?)", (str(i.id), str(reservation.id), commonName, str(i.ip_address), str(i._state)))
  i.add_tag('Name',value=commonName)
  i.add_tag('Admin',value=args.admin)
  i.add_tag('Status',value='training')
  with open('.aws.log', 'a') as log:
    log.write(str(datetime.datetime.now()) + '\n')
    log.write('reservation id: ' + str(reservation.id) + '\n')
    log.write('base name: ' + str(args.name) + '\n')
    log.write('instances: ' + str(instances) +'\n')
    log.write('Please note it may take up to 20 minutes for the images to launch and be fully available')
    log.write('\n\n')
  log.closed

sql.commit()
sql.close()
