import logging

import boto3
from botocore.exceptions import ClientError

'''
Utils for sending emails (through SES) and SMS messages (through SNS)
'''

aws_access_key_id = ''
aws_secret_access_key = ''
region = 'us-east-2'

logger = logging.getLogger(__name__)


def send_email(sender, recipient, subject, body):
    print(f'Sending email from {sender} to {recipient} with subject "{subject}"')
    client = boto3.client('ses',
                          aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key,
                          region_name=region)
    try:
        response = client.send_email(
            Source=sender,
            Destination={'ToAddresses': [recipient]},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
        print(f'Email sent with message ID: {response["MessageId"]}')
    except ClientError as e:
        print(e.response['Error']['Message'])
        return None
    return response


def send_sms(phone_number, message):
    client = boto3.client('sns',
                          aws_access_key_id=aws_access_key_id,
                          aws_secret_access_key=aws_secret_access_key,
                          region_name='your-region')
    try:
        response = client.publish(PhoneNumber=phone_number, Message=message)
    except ClientError as e:
        print(e.response['Error']['Message'])
        return None
    return response


def backup_to_s3(file_path, bucket_name, s3_file_name):
    s3 = boto3.client('s3',
                      aws_access_key_id=aws_access_key_id,
                      aws_secret_access_key=aws_secret_access_key,
                      region_name=region)
    try:
        with open(file_path, 'rb') as data:
            s3.upload_fileobj(data, bucket_name, s3_file_name)
    except Exception as e:
        print(e)
        return False
    return True
