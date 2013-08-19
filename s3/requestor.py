import requests

from decorators import retry
from util import Singleton


class Requestor(object):
	__metaclass__ = Singleton

	session = requests.Session()
	session.timeout = 80


requestor = Requestor()