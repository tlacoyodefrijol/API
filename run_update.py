import os, sys
from urlparse import urlparse
from csv import DictReader, Sniffer
from StringIO import StringIO
from requests import get

from app import db, Project, Organization

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

    # If projects_list_url is a json file
    try:
        projects = [dict(brigade=brigade, code_url=item) for item in got.json()]

    # If projects_list_url is a type of csv
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
    
    # Get the Github attributes
    if host == 'github.com':
        repo_url = 'https://api.github.com/repos' + path
        
        got = get_github_api(repo_url)
        
        if got.status_code in range(400, 499):
            raise IOError('We done got throttled')

        all_github_attributes = got.json()
        github_details = {}
        for field in ('contributors_url', 'created_at', 'forks_count', 'homepage',
                      'html_url', 'id', 'language', 'open_issues', 'pushed_at',
                      'updated_at', 'watchers_count','name', 'description'
                     ):
            github_details[field] = all_github_attributes[field]

        github_details['owner'] = dict()

        for field in ('avatar_url', 'html_url', 'login', 'type'):
            github_details['owner'][field] = all_github_attributes['owner'][field]

        project['github_details'] = github_details
        
        if 'name' not in project or not project['name']:
            project['name'] = all_github_attributes['name']
        
        if 'description' not in project or not project['description']:
            project['description'] = all_github_attributes['description']
        
        if 'link_url' not in project or not project['link_url']:
            project['link_url'] = all_github_attributes['homepage']

        #
        # Populate project contributors from github_details[contributors_url]
        #
        project['github_details']['contributors'] = []
        got = get_github_api(all_github_attributes['contributors_url'])
        
        # Check if there are contributors
        try:
            for contributor in got.json():
                # we don't want people without email addresses?
                if contributor['login'] == 'invalid-email-address':
                    break
            
                project['github_details']['contributors'].append(dict())
                
                for field in ('login', 'url', 'avatar_url', 'html_url', 'contributions'):
                    project['github_details']['contributors'][-1][field] = contributor[field]
                
                # flag the owner with a boolean value
                project['github_details']['contributors'][-1]['owner'] \
                    = bool(contributor['login'] == project['github_details']['owner']['login'])
        except:
            pass

        #
        # Populate project participation from github_details[url] + "/stats/participation"
        # Sometimes GitHub returns a blank dict instead of no participation.
        #
        got = get_github_api(all_github_attributes['url'] + '/stats/participation')
        try:
            project['github_details']['participation'] = got.json()['all']
        except:
            project['github_details']['participation'] = [0] * 50
        
        #
        # Populate project needs from github_details[issues_url] (remove "{/number}")
        #
        project['github_details']['project_needs'] = []
        url = all_github_attributes['issues_url'].replace('{/number}', '')
        got = get(url, auth=github_auth, params=dict(labels='project-needs'))
        
        # Check if GitHub Issues are disabled
        if all_github_attributes['has_issues']:
            for issue in got.json():
                project_need = dict(title=issue['title'], issue_url=issue['html_url'])
                project['github_details']['project_needs'].append(project_need)

def save_organization_info(session, org_dict):
    ''' Save a dictionary of organization info to the datastore session.
    
        Return an app.Organization instance.
    '''
    # Select an existing organization by name
    filter = Organization.name == org_dict['name']
    existing_org = session.query(Organization).filter(filter).first()
    
    # If this is a new organization
    if not existing_org:
        new_organization = Organization(**org_dict)
        session.add(new_organization)
        return new_organization
    
    # Mark the existing organization for safekeeping
    existing_org.keep = True

    # Update existing organization details
    for (field, value) in org_dict.items():
        setattr(existing_org, field, value)
    
    # Flush existing object, to prevent a sqlalchemy.orm.exc.StaleDataError
    session.flush()
    
    return existing_org

def save_project_info(session, proj_dict):
    ''' Save a dictionary of project info to the datastore session.
    
        Return an app.Project instance.
    '''
    # Select the current project, filtering on name AND brigade
    filter = Project.name == proj_dict['name'], Project.brigade == proj_dict['brigade']
    existing_project = session.query(Project).filter(*filter).first()

    # If this is a new project
    if not existing_project:
        new_project = Project(**proj_dict)
        session.add(new_project)
        return new_project

    # Mark the existing project for safekeeping
    existing_project.keep = True

    # Update existing project details
    for (field, value) in proj_dict.items():
        setattr(existing_project, field, value)
    
    # Flush existing object, to prevent a sqlalchemy.orm.exc.StaleDataError
    session.flush()

    return existing_project

if __name__ == "__main__":

    # Mark all projects for deletion at first.
    db.session.execute(db.update(Project, values={Project.keep: False}))
    db.session.execute(db.update(Organization, values={Organization.keep: False}))

    # Iterate over organizations and projects, saving them to db.session.
    for org_info in get_organizations():
        save_organization_info(db.session, org_info)

        if not org_info['projects_list_url']:
            continue

        print "Gathering all of %(name)s's projects." % org_info

        projects = get_projects(org_info['name'], org_info['projects_list_url'])

        for proj_info in projects:
            save_project_info(db.session, proj_info)

    # Remove everything marked for deletion.
    db.session.execute(db.delete(Project).where(Project.keep == False))
    db.session.execute(db.delete(Organization).where(Organization.keep == False))
    db.session.commit()
