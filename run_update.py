import json
import os
from requests import get
from csv import DictReader, Sniffer
from StringIO import StringIO
from tasks import update_project, get_people_totals, get_org_totals
from boto.s3.connection import S3Connection
from boto.s3.key import Key

BUCKET = os.environ['S3_BUCKET']
gdocs_url = 'https://docs.google.com/a/codeforamerica.org/spreadsheet/ccc?key=0ArHmv-6U1drqdGNCLWV5Q0d5YmllUzE5WGlUY3hhT2c&output=csv'

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
    
    return data

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

if __name__ == "__main__":
    update_projects()
