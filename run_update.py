import os
import sys
from urlparse import urlparse
from csv import DictReader, Sniffer
from StringIO import StringIO
from operator import itemgetter
from itertools import groupby
from json import dumps
from requests import get

from app import db, Project

gdocs_url = 'https://docs.google.com/a/codeforamerica.org/spreadsheet/ccc?key=0ArHmv-6U1drqdGNCLWV5Q0d5YmllUzE5WGlUY3hhT2c&output=csv'

if 'GITHUB_TOKEN' in os.environ:
    github_auth = (os.environ['GITHUB_TOKEN'], '')
else:
    github_auth = None

def get_github_api(url):
    '''
        Make authenticated GitHub requests.
    '''
    print 'Asking Github for', url
    
    got = get(url, auth=github_auth)
    
    return got

def get_organizations():
    ''' 
        Get a row for each organization from the Brigade Info spreadsheet.
        Return a list of dictionaries, one for each row past the header.
    '''
    got = get(gdocs_url)
    organizations = list(DictReader(StringIO(got.text)))
    
    return organizations

def get_projects(brigade, projects_list_url):
    ''' 
        Get a list of projects from CSV, TSV, or JSON.
        Convert to a dict.
        TODO: Have this work for GDocs.
    '''
    print 'Asking for', projects_list_url
    got = get(projects_list_url)

    try:
        projects = [dict(brigade=brigade, code_url=item) for item in got.json()]

    except ValueError:
        data = got.text.splitlines()
        dialect = Sniffer().sniff(data[0])
        projects = list(DictReader(data, dialect=dialect))
        for project in projects:
            project['brigade'] = brigade
    
    map(update_project_info, projects)
    
    return projects

def update_project_info(project):
    ''' Update info from Github, if it's missing.
    
        Modify the project in-place and return nothing.

        Complete repository project details go into extras, for example
        project details from Github can be found under "github".
    '''
    if 'code_url' not in project:
        return project
    
    _, host, path, _, _, _ = urlparse(project['code_url'])
    
    if host == 'github.com':
        repo_url = 'https://api.github.com/repos' + path
        
        got = get_github_api(repo_url)
        
        if got.status_code in range(400, 499):
            raise IOError('We done got throttled')

        all_github_attributes = got.json()
        github = {}
        for field in ('contributors_url', 'created_at', 'forks_count', 'homepage',
                      'html_url', 'id', 'language', 'open_issues', 'pushed_at',
                      'updated_at', 'watchers_count','name', 'description'
                     ):
            github[field] = all_github_attributes[field]

        github['owner'] = dict()

        for field in ('avatar_url', 'html_url', 'login', 'type'):
            github['owner'][field] = all_github_attributes['owner'][field]

        project['github'] = github
        
        if 'name' not in project or not project['name']:
            project['name'] = all_github_attributes['name']
        
        if 'description' not in project or not project['description']:
            project['description'] = all_github_attributes['description']
        
        if 'link_url' not in project or not project['link_url']:
            project['link_url'] = all_github_attributes['homepage']

        #
        # Populate project contributors from github[contributors_url]
        #
        project['github']['contributors'] = []
        got = get_github_api(all_github_attributes['contributors_url'])
        
        for contributor in got.json():
            # we don't want people without email addresses?
            if contributor['login'] == 'invalid-email-address':
                break
        
            project['github']['contributors'].append(dict())
            
            for field in ('login', 'url', 'avatar_url', 'html_url', 'contributions'):
                project['github']['contributors'][-1][field] = contributor[field]
            
            # flag the owner with a boolean value
            project['github']['contributors'][-1]['owner'] \
                = bool(contributor['login'] == project['github']['owner']['login'])
        
        #
        # Populate project participation from github[url] + "/stats/participation"
        #
        got = get_github_api(all_github_attributes['url'] + '/stats/participation')
        project['github']['participation'] = got.json()['all']
        
        #
        # Populate project needs from github[issues_url] (remove "{/number}")
        #
        # project['github']['project_needs'] = []
        # url = all_github_attributes['issues_url'].replace('{/number}', '')
        # got = get(url, auth=github_auth, params=dict(labels='project-needs'))
        
        # for issue in got.json():
        #     project_need = dict(title=issue['title'], issue_url=issue['html_url'])
        #     project['github']['project_needs'].append(project_need)


if __name__ == "__main__":

    db.drop_all()
    db.create_all()

    all_projects = []

    for organization in get_organizations():
        print 'Gathering all of ' + organization['name']+ "'s projects."

        if not organization['projects_list_url']:
            continue
        
        projects = get_projects(organization['name'], organization['projects_list_url'])

        for project in projects:
            project_obj = Project(**project)
            db.session.add(project_obj)
            db.session.commit()

    db.session.close()