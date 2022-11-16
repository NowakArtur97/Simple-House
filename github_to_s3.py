import os
import json
import urllib.request
import boto3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

print('Loading function')

s3 = boto3.resource('s3')

def find_all_links(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    allFiles = soup.find_all('a', href=True, class_='js-navigation-open Link--primary')
    ignored = os.environ['IGNORE_FILES']
    branch = os.environ['BRANCH']
    files = filter(lambda f: f.get_text() not in ignored, allFiles)
    links = map(lambda f: url.replace("github", "raw.githubusercontent") + "/" + branch + "/" + f.get_text(), files)
    return links

def resolve_content_type(extension):
    if extension == "html":
        return "text/html"
    elif extension == "css":
        return "text/css"
    elif extension == "js":
        return "text/javascript"
    elif extension == "png":
        return "image/png"
    else:
        return "image/jpeg"

def map_to_resource(url):
    extension = url.rsplit('.', 1)[1]
    return GithubResource(url, resolve_content_type(extension))

def save_to_local(resource):
    url = resource.url
    urlPath = urlparse(url).path
    fileName = os.path.basename(urlPath)
    filePath = '/tmp/' + fileName
    urllib.request.urlretrieve(url, filePath)
    return filePath

def resolve_key(url, fileName):
    if "/img/gallery/" in url:
        return "img/gallery/" + fileName
    elif "/img/" in url:
        return "img/" + fileName
    else:
        return fileName

def upload_to_s3(resource, filePath, bucket):
    fileName = os.path.basename(filePath)
    key = resolve_key(resource.url, fileName)
    s3.Object(bucket, key).put(Body=open(filePath, 'rb'), ContentType=resource.extension)

def copy_to_s3(resource, bucket):
    filePath = save_to_local(resource)
    upload_to_s3(resource, filePath, bucket)

def lambda_handler(event, context):
    bucket = os.environ['BUCKET_NAME']
    repositoryUrl = os.environ['REPOSITORY_URL']
    links = find_all_links(repositoryUrl)
    resources = map(map_to_resource, links)
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