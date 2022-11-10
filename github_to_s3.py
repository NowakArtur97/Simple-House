
import os
import urllib.request
from urllib.parse import urlparse
import json
import boto3

print('Loading function')

s3 = boto3.resource('s3')

def resolve_content_type(fileName):
    extension = fileName.rsplit('.', 1)[1]
    match extension:
        case 'html':
            return "text/html"
        case 'css':
            return "text/css"

def map_to_resource(url):
    return GithubResource(url, resolve_content_type(url))

def save_to_local(resource):
    url = resource.url
    urlPath = urlparse(url).path
    fileName = os.path.basename(urlPath)
    filePath = '/tmp/' + fileName
    urllib.request.urlretrieve(url, filePath)
    return filePath

def upload_to_s3(resource, filePath, bucket):
    fileName = os.path.basename(filePath)
    s3.Object(bucket, fileName).put(Body=open(filePath, 'rb'), ContentType=resource.extension)

def copy_to_s3(resource, bucket):
    filePath = save_to_local(resource)
    upload_to_s3(resource, filePath, bucket)

def lambda_handler(event, context):
    urls = [
    "https://raw.githubusercontent.com/NowakArtur97/Simple-House/master/index.html",
    "https://raw.githubusercontent.com/NowakArtur97/Simple-House/master/about.html",
    "https://raw.githubusercontent.com/NowakArtur97/Simple-House/master/contact.html",
    "https://raw.githubusercontent.com/NowakArtur97/Simple-House/master/style.css",
    # "https://raw.githubusercontent.com/NowakArtur97/Simple-House/master/img/simple-house-01.jpg",
    ]
    resources = map(map_to_resource, urls)
    bucket = "simple-house-687fffc0"

    try:
        for resource in resources:
            copy_to_s3(resource, bucket)

    except Exception as e:
        print("Exception on copy")
        print(e)
        return

class GithubResource:
  def __init__(self, url, extension):
    self.url = url
    self.extension = extension