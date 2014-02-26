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

def build_user(user):
    user_info = {}
    user_info['login'] = user.keys()[0]
    repos = user.values()[0]
    user_info['repositories'] = len(repos)
    try:
        user_info['contributions'] = sum([c['contributions'] for c in repos])
    except KeyError:
        pass
    user_info['avatar_url'] = repos[0]['avatar_url']
    user_info['html_url'] = repos[0]['html_url']
    headers = {'Authorization': 'token %s' % GITHUB_TOKEN}
    user_details = requests.get('%s/users/%s' % (GITHUB, user_info['login']), headers=headers)
    if user_details.status_code == 200:
        user_info['name'] = user_details.json().get('name')
        user_info['company'] = user_details.json().get('company')
        user_info['blog'] = user_details.json().get('blog')
        user_info['location'] = user_details.json().get('location')
    return user_info

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
