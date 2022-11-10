
import os
import urllib.request
from urllib.parse import urlparse
import json
import boto3

print('Loading function')

s3 = boto3.resource('s3')


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
    # s3.Bucket(bucket).upload_file(filePath, fileName, ExtraArgs={ContentType: "text/html"})

def copy_to_s3(resource, bucket):
    filePath = save_to_local(resource)
    upload_to_s3(resource, filePath, bucket)


def lambda_handler(event, context):
    resources = [
    GithubResource("https://raw.githubusercontent.com/NowakArtur97/Simple-House/master/index.html", "text/html"),
    GithubResource("https://raw.githubusercontent.com/NowakArtur97/Simple-House/master/about.html", "text/html"),
    GithubResource("https://raw.githubusercontent.com/NowakArtur97/Simple-House/master/contact.html", "text/html"),
    GithubResource("https://raw.githubusercontent.com/NowakArtur97/Simple-House/master/style.css", "text/css"),
    # "https://raw.githubusercontent.com/NowakArtur97/Simple-House/master/img/simple-house-01.jpg",
    ]
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