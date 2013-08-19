import time
import hmac
import base64
import hashlib
from hashlib import sha1
import urllib
import os

import requests

S3_BUCKET = "vapordrive"
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")


def get_signed_url(object_name, method, query_params=None):
    assert method in ["GET", "PUT", "HEAD", "POST"]

    expires = int(time.time() + 10)

    query_str = ""
    if query_params:
        # Handle query params with no set value (e.g. ?uploads)
        query_parts = ['%s=%s' % (k, v) if v is not None else '%s' % k
                       for k, v in query_params.iteritems()]
        query_str = "&".join(query_parts)

    object_path = "%s?%s" % (urllib.quote_plus(object_name), query_str)
    put_request = "%s\n\n\n%d\n/%s/%s" % (method, expires, S3_BUCKET, object_path)

    signature = base64.encodestring(hmac.new(AWS_SECRET_KEY, put_request, sha1).digest())
    signature = urllib.quote_plus(signature.strip())

    url = 'https://s3.amazonaws.com/%s/%s' % (S3_BUCKET, object_path)
    if not url[-1] == "?":
        url += "&"
    url += "AWSAccessKeyId=%s&Expires=%d&Signature=%s" % (AWS_ACCESS_KEY, expires, signature)

    return url