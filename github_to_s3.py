import os
import json
import urllib.request
import boto3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

print('Loading function')

WRAPPER_CLASS = 'Box mb-3'
ELEMENT_CLASS = 'Box-row Box-row--focus-gray py-2 d-flex position-relative js-navigation-item'
LINK_CLASS = 'Link--primary'

s3 = boto3.resource('s3')

ignored = os.environ['IGNORE_FILES']
branch = os.environ['BRANCH']

def find_all_resources(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    wrapperElement = soup.find_all('div', class_= [WRAPPER_CLASS])[0]
    allFilesElements = wrapperElement.find_all('div', class_= ELEMENT_CLASS)
    notIgnored = filter(lambda f: f.find('a', href=True, class_= LINK_CLASS).get_text() not in ignored, allFilesElements)
    return map(lambda fileElement: map_to_resource(fileElement, get_raw_url(url, branch)), notIgnored)

def get_raw_url(url, branch):
    return url.replace("github", "raw.githubusercontent") + "/" + branch + "/"

def map_to_resource(fileElement, url):
    isFolder = fileElement.find('svg', class_='octicon')['aria-label'] == "Directory"
    link = url + fileElement.find('a', href=True, class_='Link--primary').get_text()
    extension = resolve_content_type(link)
    return GithubResource(link, extension, isFolder)

def resolve_content_type(url):
    extension = url.rsplit('.', 1)[1]
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
    resources = find_all_resources(repositoryUrl)
    for resource in resources:
        print(resource.url)
        print(resource.extension)
        print(resource.isFolder)
    # try:
    #     for resource in resources:
    #         copy_to_s3(resource, bucket)
    # except Exception as e:
    #     print("Exception on copy")
    #     print(e)
    #     return

class GithubResource:
  def __init__(self, url, extension, isFolder):
    self.url = url
    self.extension = extension
    self.isFolder = isFolder