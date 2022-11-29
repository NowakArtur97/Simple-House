import os
import json
import urllib.request
import boto3
from urllib.parse import urlparse
import cfnresponse

s3 = boto3.resource('s3')
BUCKET_NAME = os.environ['BUCKET_NAME']

def save_to_local(url):
    urlPath = urlparse(url).path
    fileName = os.path.basename(urlPath)
    filePath = '/tmp/' + fileName
    urllib.request.urlretrieve(url, filePath)
    return filePath

def copy_to_s3(url):
    filePath = save_to_local(url)
    fileName = os.path.basename(filePath)
    s3.meta.client.upload_file(filePath, BUCKET_NAME, fileName)
    s3.Object(BUCKET_NAME, fileName).put(Body=open(filePath, 'rb'), ContentType="application/zip")

def lambda_handler(event, context):
    responseData = {}
    try:    
        url = os.environ['URL']
        copy_to_s3(url)
        print("Successfully copied file from url: " + url + " to BUCKET_NAME: " + BUCKET_NAME)
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
    except Exception as e:
        print("Exception")
        print(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, responseData)