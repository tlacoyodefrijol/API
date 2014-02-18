import json
import os
from requests import get
from urlparse import urlparse
from csv import DictReader, Sniffer
from StringIO import StringIO
from tasks import update_project, get_people_totals, get_org_totals
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from operator import itemgetter
from itertools import groupby
from time import sleep
from json import dumps

BUCKET = os.environ['S3_BUCKET']
gdocs_url = 'https://docs.google.com/a/codeforamerica.org/spreadsheet/ccc?key=0ArHmv-6U1drqdGNCLWV5Q0d5YmllUzE5WGlUY3hhT2c&output=csv'

if 'GITHUB_TOKEN' in os.environ:
    github_auth = (os.environ['GITHUB_TOKEN'], '')
else:
    github_auth = None

def get_github_api(url):
    '''
    '''
    got = get(url, auth=github_auth)
    
    if github_auth is None:
        sleep(1) # be nice to Github
    
    return got

def get_orgs():
    ''' Get a row for each organization from the Brigade Info spreadsheet.

        Return a list of dictionaries, one for each row past the header.
    '''
    got = get(gdocs_url)
    data = list(DictReader(StringIO(got.text)))
    
    return data

def load_projects(projects_url):
    ''' Load a list of projects from a given URL.
    '''
    got = get(projects_url)

    try:
        data = [dict(code_url=item) for item in got.json()]

    except ValueError:
        projects = got.text.splitlines()
        dialect = Sniffer().sniff(projects[0])
        data = list(DictReader(projects, dialect=dialect))
    
    return [update_project_info(row) for row in data]

def update_project_info(row):
    ''' Update info from Github, if it's missing.
    
        Modify the row in-place with new info and return it.

        Complete repository project details go into extras, for example
        project details from Github can be found under "github_extras".
    '''
    if 'code_url' not in row:
        return row
    
    _, host, path, _, _, _ = urlparse(row['code_url'])
    
    if host == 'github.com':
        repo_url = 'https://api.github.com/repos' + path
        
        got = get_github_api(repo_url)
        
        if got.status_code in range(400, 499):
            raise IOError('We done got throttled')
        
        repo = got.json()
        
        if 'name' not in row or not row['name']:
            row['name'] = repo['name']
        
        if 'description' not in row or not row['description']:
            row['description'] = repo['description']
        
        if 'link_url' not in row or not row['link_url']:
            row['link_url'] = repo['homepage']
        
        row['github_extras'] = repo
    
    return row

def reformat_project_info(input):
    ''' Return a clone of the project hash, formatted for use by opengovhacknight.org.
    
        The representation here is specifically expected to be used on this page:
        http://opengovhacknight.org/projects.html
    '''
    output = dict()
    
    for field in ('name', 'description'):
        output[field] = input[field]
    
    if 'github_extras' in input:
        try:
            info = collect_github_project_info(input)
        except:
            pass
        else:
            output.update(info)
    
    return output

def collect_github_project_info(input):
    ''' Collect Github project info, formatted for use by opengovhacknight.org.
    
        The representation here is specifically expected to be used on this page:
        http://opengovhacknight.org/projects.html
    '''
    output = dict()
    github = input['github_extras']

    #
    # Populate core Github fields.
    #
    for field in (
            'contributors_url', 'created_at', 'forks_count', 'homepage',
            'html_url', 'id', 'language', 'open_issues', 'pushed_at',
            'updated_at', 'watchers_count'
            ):
        output[field] = github[field]

    output['owner'] = dict()

    for field in ('avatar_url', 'html_url', 'login', 'type'):
        output['owner'][field] = github['owner'][field]
    
    #
    # Populate project contributors from github[contributors_url]
    #
    output['contributors'] = []
    got = get_github_api(github['contributors_url'])
    
    for contributor in got.json():
        # we don't want people without email addresses?
        if contributor['login'] == 'invalid-email-address':
            break
    
        output['contributors'].append(dict())
        
        for field in ('login', 'url', 'avatar_url', 'html_url', 'contributions'):
            output['contributors'][-1][field] = contributor[field]
        
        output['contributors'][-1]['owner'] \
            = bool(contributor['login'] == output['owner']['login'])
    
    #
    # Populate project participation from github[url] + "/stats/participation"
    #
    got = get(github['url'] + '/stats/participation', auth=github_auth)
    output['participation'] = got.json()['all']
    
    #
    # Populate project needs from github[issues_url] (remove "{/number}")
    #
    output['project_needs'] = []
    url = github['issues_url'].replace('{/number}', '')
    got = get(url, auth=github_auth, params=dict(labels='project-needs'))
    
    for issue in got.json():
        project_need = dict(title=issue['title'], issue_url=issue['html_url'])
        output['project_needs'].append(project_need)
    
    return output

def update_projects():
    conn = S3Connection()
    bucket = conn.get_bucket(BUCKET)
    pj_list = Key(bucket)
    pj_list.key = 'projects.json'
    project_list = json.loads(pj_list.get_contents_as_string())
    pj_list.close()
    details = []
    for project_url in project_list:
        try:
            pj_details = update_project(project_url)
        except IOError:
            return 'Github is throttling. Just gonna try again after limit is reset.'
        if pj_details:
            details.append(pj_details)
    pj_details = Key(bucket)
    pj_details.key = 'project_details.json'
    pj_details.set_contents_from_string(json.dumps(details))
    pj_details.set_metadata('Content-Type', 'application/json')
    pj_details.set_acl('public-read')
    pj_details.close()
    people_list = Key(bucket)
    people_list.key = 'people.json'
    people_list.set_contents_from_string(json.dumps(get_people_totals(details)))
    people_list.set_metadata('Content-Type', 'application/json')
    people_list.set_acl('public-read')
    people_list.close()
    org_list = Key(bucket)
    org_list.key = 'organizations.json'
    org_list.set_contents_from_string(json.dumps(get_org_totals(details)))
    org_list.set_metadata('Content-Type', 'application/json')
    org_list.set_acl('public-read')
    org_list.close()
    return 'Updated'

def upload_json_file(json_data, object_name):
    ''' Upload a named file to S3 BUCKET, return nothing.
    '''
    s3 = S3Connection()
    bucket = s3.get_bucket(BUCKET)

    object = Key(bucket)
    object.key = object_name
    
    data = dumps(json_data, indent=2)
    args = dict(policy='public-read', headers={'Content-Type': 'application/json'})

    object.set_contents_from_string(data, **args)

def count_people_totals(project_details):
    ''' Create a list of people details based on project details.
    
        Request additional data from Github API for each person.
    '''
    users, contributors = [], []

    for project in project_details:
        contributors.extend(project['contributors'])
    
    #
    # Sort by login; there will be duplicates!
    #
    contributors.sort(key=itemgetter('login'))
    
    #
    # Populate users array with groups of contributors.
    #
    for (_, _contributors) in groupby(contributors, key=itemgetter('login')):
        user = dict(contributions=0, repositories=0)
        
        for contributor in _contributors:
            user['contributions'] += contributor['contributions']
            user['repositories'] += 1
            
            if 'login' in user:
                continue

            #
            # Populate user hash with Github info, if it hasn't been already.
            #
            got = get_github_api(contributor['url'])
            contributor = got.json()
            
            for field in (
                    'login', 'avatar_url', 'html_url',
                    'blog', 'company', 'location'
                    ):
                user[field] = contributor.get(field, None)
        
        users.append(user)
    
    return users

if __name__ == "__main__":

    project_details = []

    for org in get_orgs():
        if not org['projects_url']:
            continue
    
        for project in load_projects(org['projects_url']):
            project_details.append(reformat_project_info(project))
            print dumps(project, indent=2)
    
    upload_json_file(project_details, 'project_details.json')

    people = count_people_totals(project_details)
    upload_json_file(people, 'people.json')

    exit(0)

    update_projects()
