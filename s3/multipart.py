import os

from bs4 import BeautifulSoup
import requests

from decorators import retry
from requestor import requestor
from url import get_signed_url


# 5 mb
CHUNK_SIZE = 5 * 1024 * 1024


def multipart_upload(path):
    """Perform a multipart upload

    Args:
        ``path``: (str) The relative path to the file to upload as well
            as the path to the file that will be stored on S3.

    """
    upload_id = init_upload(path)
    etags = upload_all(path, upload_id)
    finish_upload(path, upload_id, etags)


@retry(Exception, tries=5, delay=0.1)
def init_upload(path):
    """Initialize a multipart upload.

    See http://docs.aws.amazon.com/AmazonS3/latest/API/mpUploadInitiate.html.

    Args:
        ``path``: (str) The relative path to the file to upload as well
            as the path to the file that will be stored on S3.

    Returns:
        A string upload id from Amazon's S3 REST API.

    """
    url = get_signed_url(path, 'POST', query_params={'uploads': None})
    response = requestor.session.post(url)
    soup = BeautifulSoup(response.content)
    upload_elem = soup.find("uploadid")
    if not upload_elem:
        raise Exception("Failed to generate upload id in multi-part request!")
    return upload_elem.string


def upload_all(path, upload_id):
    """Upload all parts of the specified file using the specified upload id.

    Args:
        ``path``: (str) The relative path to the file to upload as well
            as the path to the file that will be stored on S3.
        ``upload_id``: (str) An upload id as returned by Amazon's multipart
            upload API.

    Returns:
        A dictionary {sequence number: etag (md5 hash of file part)} for
        each part successfully uploaded.

    """
    size_left = os.stat(path).st_size
    file_size = size_left
    num_parts = file_size / CHUNK_SIZE + (file_size % CHUNK_SIZE and 1)
    file_handle = open(path, 'rb')

    etags = {}
    seq_num = 1
    while True:
        buf = file_handle.read(CHUNK_SIZE)
        if len(buf) == 0:
            break
        try:
            response = upload_part(path, upload_id, buf, seq_num)
        except Exception, e:
            raise RuntimeError("Upload Failed: %s" % e)
        else:
            etag = response.headers.get('etag')
            if not etag:
                raise RuntimeError("No etag found!")
            etags[seq_num] = etag
        seq_num += 1
    return etags


@retry(Exception, tries=5, delay=0.1)
def upload_part(path, upload_id, buf, seq_num):
    """Upload a single part of a multipart upload.

    See http://docs.aws.amazon.com/AmazonS3/latest/API/mpUploadUploadPart.html.

    Args:
        ``path``: (str) The relative path to the file to upload as well
            as the path to the file that will be stored on S3.
        ``upload_id``: (str) An upload id as returned by Amazon's multipart
            upload API.
        ``buf``: (str) A byte buffer corresponding to the chunk of the file
            specified by ``seq_num``
        ``seq_num``: (int) The sequence number (beginning from 1) of the chunk
            of file being uploaded.

    Returns:
        A ``requests.Response`` object.

    """
    url = get_signed_url(path, "PUT", query_params={
        'partNumber': seq_num,
        'uploadId': upload_id
    })
    response = requestor.session.put(url, data=buf)
    return response


@retry(Exception, tries=5, delay=0.1)
def finish_upload(path, upload_id, etags):
    """Finish a multipart upload according to Amazon's API.

    See http://docs.aws.amazon.com/AmazonS3/latest/API/mpUploadComplete.html.

    Args:
        ``path``: (str) The relative path to the file to upload as well
            as the path to the file that will be stored on S3.
        ``upload_id``: (str) An upload id as returned by Amazon's multipart
            upload API.
        ``etags``: (dict) {sequence number: etag (md5 hash of file part)}

    Returns:
        A ``requests.Response`` object.

    """
    xml_etag_template = "<Part><PartNumber>%i</PartNumber><ETag>%s</ETag></Part>"
    xml_etags = [xml_etag_template % (seq_num, etag)
                 for seq_num, etag in etags.iteritems()]
    body = "<CompleteMultipartUpload>%s</CompleteMultipartUpload>"
    body = body % ("".join(xml_etags))
    url = get_signed_url(path, "POST", query_params={
        'uploadId': upload_id
    })
    response = requestor.session.post(url, data=body)
    return response
