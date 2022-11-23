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
DIRECTORY_ICON_CLASS = 'octicon'

s3 = boto3.resource('s3')

ignoredFilesAndFolders = os.environ['IGNORED_FILES_AND_FOLDERS'].split(",")
ignoredExtensions = os.environ['IGNORED_EXTENSIONS'].split(",")
branch = os.environ['BRANCH']

def find_all_resources(url, nestedPath="", resources=[]):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    wrapperElement = soup.find('div', class_=[WRAPPER_CLASS])
    allFilesElements = wrapperElement.find_all('div', class_=ELEMENT_CLASS)
    notIgnored = filter(lambda f: f.find('a', href=True, class_=LINK_CLASS).get_text() not in ignoredFilesAndFolders, allFilesElements)
    for element in notIgnored:
        isDirectory = element.find('svg', class_=DIRECTORY_ICON_CLASS)['aria-label'] == "Directory"
        resourceName = element.find('a', href=True, class_=LINK_CLASS).get_text()
        link = url + "/" + resourceName
        if isDirectory:
            if nestedPath == "":
                nestedResources = find_all_resources(link, resourceName, resources)
                flatten = flatten_list(nestedResources)
                resources.append(flatten)
            else:
                nestedResources = find_all_resources(link, nestedPath + "/" + resourceName, resources)
                flatten = flatten_list(nestedResources)
                resources.append(flatten)
        else:
            extension = link.rsplit('.', 1)[1]
            if extension in ignoredExtensions:
                continue
            contentType = resolve_content_type(extension)
            if nestedPath == "":
                resource = GithubResource(get_raw_url(link), contentType, resourceName)
                resources.append(resource)
            else:
                resource = GithubResource(get_raw_url(link), contentType, nestedPath + "/" + resourceName)
                resources.append(resource)

    return flatten_list(resources)

def flatten_list(_2d_list):
    flat_list = []
    for element in _2d_list:
        if type(element) is list:
            for item in element:
                flat_list.append(item)
        else:
            flat_list.append(element)
    return flat_list

def resolve_content_type(extension):
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

def get_raw_url(url):
    return url.replace("https://github.com", "https://raw.githubusercontent.com").replace("/tree/" + branch +"/", "/" + branch +"/")

def save_to_local(resource):
    url = resource.url
    urlPath = urlparse(url).path
    fileName = os.path.basename(urlPath)
    filePath = '/tmp/' + fileName
    urllib.request.urlretrieve(url, filePath)
    return filePath

def upload_to_s3(resource, filePath, bucket):
    fileName = os.path.basename(filePath)
    s3.Object(bucket, resource.key).put(Body=open(filePath, 'rb'), ContentType=resource.contentType)

def copy_to_s3(resource, bucket):
    filePath = save_to_local(resource)
    upload_to_s3(resource, filePath, bucket)

def lambda_handler(event, context):
    bucket = os.environ['BUCKET_NAME']
    repositoryUrl = os.environ['REPOSITORY_URL'] + "/tree/" + branch
    resources = find_all_resources(repositoryUrl)
    print("**********")
    for resource in resources:
        print(resource.url)
        print(resource.contentType)
        print(resource.key)
    try:
        for resource in resources:
            copy_to_s3(resource, bucket)
    except Exception as e:
        print("Exception on copy")
        print(e)
        return

class GithubResource:
  def __init__(self, url, contentType,  key):
    self.url = url
    self.contentType = contentType
    self.key = key
