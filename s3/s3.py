import time
import hmac
import base64
import hashlib
from hashlib import sha1
import urllib
import requests

import os
from cStringIO import StringIO


AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")
S3_BUCKET = "vapordrive"


def md5_file(path):
    md5 = hashlib.md5()
    with open(path,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
             md5.update(chunk)
    return md5.hexdigest()


def _get_signed_url(object_name, method):
    assert method in ["GET", "PUT", "HEAD"]

    expires = int(time.time() + 10)
    put_request = "%s\n\n\n%d\n/%s/%s" % (method, expires, S3_BUCKET, object_name)

    signature = base64.encodestring(hmac.new(AWS_SECRET_KEY, put_request, sha1).digest())
    signature = urllib.quote_plus(signature.strip())

    url = 'https://s3.amazonaws.com/%s/%s' % (S3_BUCKET, object_name)
    signed_request = '%s?AWSAccessKeyId=%s&Expires=%d&Signature=%s' % (url, AWS_ACCESS_KEY, expires, signature)

    return signed_request


def upload(path):
    url = _get_signed_url(path, "PUT")
    progress = Progress()
    stream = FileWithCallback(path, 'rb', progress.update, path)
    r = requests.put(url, data=stream)


def download(path):
    url = _get_signed_url(path, "GET")
    r = requests.get(url, stream=True)
    with open(path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()


def head(path):
    url = _get_signed_url(path, "HEAD")
    r = requests.head(url)
    return r.headers


class Progress(object):
    def __init__(self):
        self._seen = 0.0

    def update(self, total, size, name):
        self._seen += size
        pct = (self._seen / total) * 100.0
        print '%s progress: %.2f' % (name, pct)


class FileWithCallback(file):
    def __init__(self, path, mode, callback, *args):
        file.__init__(self, path, mode)
        self.seek(0, os.SEEK_END)
        self._total = self.tell()
        self.seek(0)
        self._callback = callback
        self._args = args

    def __len__(self):
        return self._total

    def read(self, size):
        data = file.read(self, size)
        self._callback(self._total, len(data), *self._args)
        return data
