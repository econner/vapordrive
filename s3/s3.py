import os
import hashlib

import requests

from decorators import retry
from multipart import multipart_upload
from requestor import requestor
from url import get_signed_url
from util import FileWithCallback
from util import Progress


def md5_file(path):
    md5 = hashlib.md5()
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
             md5.update(chunk)
    return md5.hexdigest()


@retry(Exception, tries=5, delay=0.1)
def upload(path):
    file_size = os.stat(path).st_size
    if file_size <= 5 * 1024 * 1024:
        url = get_signed_url(path, "PUT")
        progress = Progress()
        stream = FileWithCallback(path, 'rb', progress.update, path)
        response = requestor.session.put(url, data=stream)
        return response
    else:
        return multipart_upload(path)


@retry(Exception, tries=5, delay=0.1)
def download(path):
    url = get_signed_url(path, "GET")
    response = requestor.session.get(url, stream=True)
    with open(path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()


@retry(Exception, tries=5, delay=0.1)
def head(path):
    url = get_signed_url(path, "HEAD")
    response = requestor.session.head(url)
    return response.headers


if __name__ == "__main__":
    s3_key = 'vapor/yoga.mp4'
    upload(s3_key, multipart=True)
