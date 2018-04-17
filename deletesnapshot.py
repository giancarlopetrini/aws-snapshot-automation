import boto3  
import re  
import datetime

#Please mention your region name
#below line code is call cross region
ec = boto3.client('ec2', region_name='us-east-1')  
iam = boto3.client('iam')

#begins lambda function
def lambda_handler(event, context):  
    account_ids = list()
    try:         
        iam.get_user()
    except Exception as e:
        # use the exception message to get the account ID the function executes under
        account_ids.append(re.search(r'(arn:aws:sts::)([0-9]+)', str(e)).groups()[1])
    
    # loop through each of the versions and run deletions
    # matching delete day + version tag
    versions = ['Daily', 'Weekly', 'Monthly', 'Quarterly']
    for version in versions:
        delete_on = datetime.date.today().strftime('%Y-%m-%d')
        filters = [
            {'Name': 'tag-key', 'Values': ['DeleteOn']},
            {'Name': 'tag-value', 'Values': [delete_on]},
            {'Name': 'tag-key', 'Values': ['Version']},
            {'Name': 'tag-value', 'Values': [version]}
        ]
        snapshot_response = ec.describe_snapshots(OwnerIds=account_ids, Filters=filters)
        for snap in snapshot_response['Snapshots']:
            print "Deleting snapshot %s" % snap['SnapshotId']
            ec.delete_snapshot(SnapshotId=snap['SnapshotId'])
