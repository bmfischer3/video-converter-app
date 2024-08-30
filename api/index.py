
import awsgi
import os
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    session
)
import datetime
from pprint import pprint


import logging

import requests


logging.basicConfig()

app = Flask(__name__, template_folder='templates')

app.secret_key = 'secret key'


# From https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html
def create_presigned_post(bucket_name, object_name,
                          fields=None, conditions=None, expiration=500):
    """Generate a presigned URL S3 POST request to upload a file

    :param bucket_name: string
    :param object_name: string
    :param fields: Dictionary of prefilled form fields
    :param conditions: List of conditions to include in the policy
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """

    # Generate a presigned S3 POST URL
    # Don't forget to configure this to the needed profile. 
    aws_session = boto3.Session(profile_name='dev')
    s3_client = aws_session.client('s3')
    
    try:
        response = s3_client.generate_presigned_post(bucket_name,
                                                     object_name,
                                                     Fields=fields,
                                                     Conditions=conditions,
                                                     ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL and required fields
    return response



@app.route('/', methods=['GET', 'POST'])
def home():

    # TODO: Will need to determine a way to dynamically pass the CloudFormation generated bucket name to the below variable, since the S3 bucket name must be globally unique.
    # Bucket can stay private, Boto3 gets the access keys and the presigned URL provides temp access.

    bucket_name = 'testing-bucket-dev-567483498'

    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime('%H:%M:S')

    # TODO: Figure out how to get the file extensions. 
    # TODO: So in short, I'm going to need to get the file information first, then request the pre-signed URL. 
    # Probably want to avoid javascript, User may have to click two buttons or something....

    object_name = str('user_submitted_file' + '_' + formatted_time + '.mp4')

    presigned_post = create_presigned_post(bucket_name, object_name)

    if presigned_post == None:
        logging.info(f"Failed to get presigned URL from S3 bucket.")
        return "Failed to generated presigned URL", 500
    
    else:
        return render_template('home.html',
                        url=presigned_post['url'],
                        fields=presigned_post['fields']
        )


def handler(event, context):
    # list_name = event["queryStringParameters"]["list_name"]
    # path = event["queryStringParameters"]["path"]
    return awsgi.response(app, event, context)


# Not in lambda, run flask app. 
if not os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
    app.run('127.0.0.1', 8080, os.environ.get("APP_DEBUG") != "")

