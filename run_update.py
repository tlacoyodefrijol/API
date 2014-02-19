import json
import os
from urlparse import urlparse
from csv import DictReader, Sniffer
from StringIO import StringIO
from operator import itemgetter
from itertools import groupby
from time import sleep
from json import dumps

from requests import get
from boto.s3.connection import S3Connection
from boto.s3.key import Key

from app import db, Project

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

def get_organizations():
    ''' Get a row for each organization from the Brigade Info spreadsheet.

        Return a list of dictionaries, one for each row past the header.
    '''
    got = get(gdocs_url)
    organizations = list(DictReader(StringIO(got.text)))
    
    return organizations

def load_projects(projects_list_url):
    ''' Load a list of projects from a given URL.
    '''
    print projects_list_url
    got = get(projects_list_url)

    try:
        projects_details = [dict(code_url=item) for item in got.json()]

    except ValueError:
        data = got.text.splitlines()
        dialect = Sniffer().sniff(data[0])
        projects_details = list(DictReader(data, dialect=dialect))

    return [update_project_info(project_detail) for project_detail in projects_details]

def update_project_info(project_detail):
    ''' Update info from Github, if it's missing.
    
        Modify the project_detail in-place with new info and return it.

        Complete repository project details go into extras, for example
        project details from Github can be found under "github_extras".
    '''
    if 'code_url' not in project_detail:
        return project_detail
    
    _, host, path, _, _, _ = urlparse(project_detail['code_url'])
    
    if host == 'github.com':
        repo_url = 'https://api.github.com/repos' + path
        
        print repo_url
        got = get_github_api(repo_url)
        
        if got.status_code in range(400, 499):
            raise IOError('We done got throttled')

        github_project_info = got.json()
        
        if 'name' not in project_detail or not project_detail['name']:
            project_detail['name'] = github_project_info['name']
        
        if 'description' not in project_detail or not project_detail['description']:
            project_detail['description'] = github_project_info['description']
        
        if 'link_url' not in project_detail or not project_detail['link_url']:
            project_detail['link_url'] = github_project_info['homepage']
        
        project_detail['github_extras'] = unicode(github_project_info)
    
    return project_detail

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

def count_people_totals(all_project_details):
    ''' Create a list of people details based on project details.
    
        Request additional data from Github API for each person.
    '''
    users, contributors = [], []

    for project_details in all_project_details:
        contributors.extend(project_details['contributors'])
    
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

    db.drop_all()
    db.create_all()

    all_project_details = []

    for organization in get_organizations():
        print organization['name']
        if not organization['projects_list_url']:
            continue
        
        org_projects_details = load_projects(organization['projects_list_url'])

        for project_details in org_projects_details:
            project = Project(**project_details)
            db.session.add(project)
            db.session.commit()
            # all_project_details.append(reformat_project_info(project_details))
            # print dumps(project, indent=2)


    upload_json_file(all_project_details, 'project_details.json')
    people = count_people_totals(all_project_details)
    upload_json_file(people, 'people.json')
