import os
import json
import urllib.request
import boto3
from urllib.parse import urlparse
import cfnresponse

s3 = boto3.resource('s3')
bucket = os.environ['BUCKET_NAME']

def resolve_content_type(url):
    extension = url.rsplit('.', 1)[1]
    if extension == "html":
        return "text/html"
    elif extension == "css":
        return "text/css"
    elif extension == "js":
        return "text/javascript"
    elif extension == "py":
        return "text/x-python"
    elif extension in ["jpeg", "jpg"]:
        return "image/jpeg"
    elif extension == "png":
        return "image/png"
    elif extension == "tiff":
        return "image/tiff"
    elif extension == "bmp":
        return "image/bmp"
    elif extension == "gif":
        return "image/gif"
    elif extension in ["svg", "xml"]:
        return "image/svg+xml"
    elif extension in ["mp3", "wav", "ogg"]:
        return "audio/mpeg"
    elif extension == "pdf":
        return "application/pdf"
    elif extension == "zip":
        return "application/zip"
    elif extension in ["yaml"]:
        return "binary/octet-stream"
    else:
        return "text/plain"

def save_to_local(url):
    urlPath = urlparse(url).path
    fileName = os.path.basename(urlPath)
    filePath = '/tmp/' + fileName
    urllib.request.urlretrieve(url, filePath)
    return filePath

def upload_to_s3(resource, filePath):
    s3.Object(bucket, resource.key).put(Body=open(filePath, 'rb'), ContentType=resource.contentType)

def copy_to_s3(url):
    filePath = save_to_local(url)
    fileName = os.path.basename(filePath)
    contentType = resolve_content_type(url)
    resource = Resource(url, contentType, fileName)
    upload_to_s3(resource, filePath)

def lambda_handler(event, context):
    responseData = {}
    try:    
        urls = os.environ['URLS'].split(",")
        try:
            for url in urls:
                copy_to_s3(url)
                print("Successfully copied file from url: " + url + " to bucket: " + bucket)
        except Exception as e:
            print("Exception on copy")
            print(e)
            cfnresponse.send(event, context, cfnresponse.FAILED, responseData)
            return
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
    except Exception as e:
        print("Exception")
        print(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, responseData)

class Resource:
  def __init__(self, url, contentType,  key):
    self.url = url
    self.contentType = contentType
    self.key = key
