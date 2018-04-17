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
        
    versions = ["Daily", "Weekly", "Monthly", "Quarterly"]
    
    for version in versions:
        delete_on = datetime.date.today().strftime('%Y-%m-%d')
        filters = [
            {'Name': 'tag-key', 'Values': ['DeleteOn']},
            {'Name': 'tag-value', 'Values': [delete_on]},
            {'Name': 'tag-key', 'Values': ['Version']},
            {'Name': 'tag-value', 'Values': [version]},
        ]
        # get snapshots that match filters
        snapshot_response = ec.describe_snapshots(OwnerIds=account_ids, Filters=filters)
        # loop through response dict, grabbing snapshots list
        for snap in snapshot_response['Snapshots']:
            for tag in snap['Tags']:
                if tag['Key'] == 'Version':
                    versionTag = tag['Value']
                    # filter for weekly tag on snap object
                    # and only process if within first week of the monthy
                    if versionTag == 'Weekly' and datetime.datetime.today().day <= 7:
                        # get 30 days from time of creation
                        createdDate = (snap['StartTime']).date()
                        monthlyDate =  (createdDate + datetime.timedelta(days=30))
                        # if date function executes is 1 month from snapshot's creation 
                        if monthlyDate == datetime.date.today():
                            #set new delete date, 3 months out
                            new_delete_date = (datetime.date.today() + datetime.timedelta(days=90))
                            new_delete_date = new_delete_date.strftime('%Y-%m-%d')
                            # update version and delete on tags to monthly, with a date 3 months out
                            ec.create_tags(Resources=[snap['SnapshotId']],
                            Tags=[{
                                'Key': 'Version',
                                'Value': 'Monthly'
                            }, {
                                'Key': 'DeleteOn',
                                'Value': new_delete_date 
                            }])
                    elif versionTag == 'Monthly':
                        # get 90 days from time of creation to convert to quarterly
                        createdDate = (snap['StartTime']).date()
                        quarterlyDate = (createdDate + datetime.timedelta(days=90))
                        if quarterlyDate == datetime.date.today():
                            # set new delete date, 6 months out
                            new_delete_date = (datetime.date.today() + datetime.timedelta(days=180))
                            new_delete_date = new_delete_date.strftime('%Y-%m-%d')
                            # update version tag to quarterly and deletion date to 6 m/180 days
                            ec.create_tags(Resources=[snap['SnapshotId']],
                            Tags=[{
                                'Key': 'Version',
                                'Value': 'Quarterly'
                            }, {
                                'Key': 'DeleteOn',
                                'Value': new_delete_date
                            }])
                    elif versionTag == 'Quarterly ':
                        print "Snapshot, %s marked for final deletion..." %snap['SnapshotId']
                    else:
                        print "Snapshot, %s marked for final deletion..." %snap['SnapshotId']
