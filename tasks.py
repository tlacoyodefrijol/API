import os
import json
import requests
from urlparse import urlparse
from operator import itemgetter
from itertools import groupby
from datetime import datetime
from boto.s3.connection import S3Connection
from boto.s3.key import Key

BUCKET = os.environ['S3_BUCKET']

GITHUB = 'https://api.github.com'
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
