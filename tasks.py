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

def update_issues(project_url):
    full_name = '/'.join(urlparse(project_url).path.split('/')[1:3])
    url = '%s/repos/%s/issues' % (GITHUB, full_name)
    headers = {'Authorization': 'token %s' % GITHUB_TOKEN}
    params = {'labels': 'project-needs'}
    r = requests.get(url, headers=headers, params=params)
    all_issues = []
    if r.status_code == 200:
        for issue in r.json():
            all_issues.append({
                'title': issue.get('title'),
                'issue_url': issue.get('html_url'),
            })
        return all_issues
    else:
        return []
