import os, sys
from urlparse import urlparse
from csv import DictReader, Sniffer
from itertools import groupby
from operator import itemgetter
from StringIO import StringIO
from requests import get
from datetime import datetime
import requests
from feeds import extract_feed_links, get_first_working_feed_link
import feedparser
from urllib2 import HTTPError
from app import db, app, Project, Organization, Story, Event
from urlparse import urlparse
from re import match

# Production
gdocs_url = 'https://docs.google.com/a/codeforamerica.org/spreadsheet/ccc?key=0ArHmv-6U1drqdGNCLWV5Q0d5YmllUzE5WGlUY3hhT2c&output=csv'

# Testing
# gdocs_url = "https://docs.google.com/spreadsheet/pub?key=0ArHmv-6U1drqdEVkTUtZNVlYRE5ndERLLTFDb2RqQlE&output=csv"


if 'GITHUB_TOKEN' in os.environ:
    github_auth = (os.environ['GITHUB_TOKEN'], '')
else:
    github_auth = None

if 'MEETUP_KEY' in os.environ:
    meetup_key = (os.environ['MEETUP_KEY'], '')
else:
    meetup_key = None

def get_github_api(url):
    '''
        Make authenticated GitHub requests.
    '''
    app.logger.info('Asking Github for', url)

    got = get(url, auth=github_auth)

    return got

def format_date(time_in_milliseconds):
    '''
        Create a datetime object from a time in milliseconds from the epoch
    '''
    return datetime.fromtimestamp(time_in_milliseconds/1000.0)

def format_location(venue):
    address = venue['address_1']
    if('address_2' in venue.keys() and venue['address_2'] != ''):
        address = address + ', ' + venue['address_2']

    return "{address}, {city}, {state}, {country}".format(address=address,
                city=venue['city'], state=venue['state'], country=venue['country'])

def get_meetup_events(organization, group_urlname):
    '''
        Get events associated with a group
    '''
    meetup_url = "https://api.meetup.com/2/events?status=past,upcoming&format=json&group_urlname={0}&sig_id={1}".format(group_urlname, meetup_key)
    got = get(meetup_url)
    if got.status_code == 404:
        app.logger.error("%s's meetup page cannot be found" % organization.name)
        return None
    else:
        results = got.json()['results']
        events = [dict(organization_name=organization.name, name=event['name'], description=event['description'],
                       event_url=event['event_url'], start_time=format_date(event['time']),
                       location=format_location(event['venue']), created_at=format_date(event['created']))
                    for event in results]
        return events

def get_organizations():
    '''
        Get a row for each organization from the Brigade Info spreadsheet.
        Return a list of dictionaries, one for each row past the header.
    '''
    got = get(gdocs_url)
    organizations = list(DictReader(StringIO(got.text)))

    return organizations

def get_stories(organization):
    '''
    '''
    # If there is no given rss link, try the website url.
    if organization.rss:
        rss = organization.rss
    else:
        rss = organization.website
    try:
        url = get_first_working_feed_link(rss)
    except (HTTPError, ValueError):
        url = None

    # If no blog found then give up
    if not url:
        return None

    d = feedparser.parse(url)
    if d.entries:
        # Grab the two most recent stories.
        for i in range(0,2):
            print d.entries[i].title
            print d.entries[i].link
            # Search for the same story
            filter = Story.title == d.entries[i].title
            existing_story = db.session.query(Story).filter(filter).first()
            if existing_story:
                continue
            else:
                story_dict = dict(title=d.entries[i].title, link=d.entries[i].link, type="blog", organization_name=organization.name)
                new_story = Story(**story_dict)
                db.session.add(new_story)


def get_projects(organization):
    '''
        Get a list of projects from CSV, TSV, or JSON.
        Convert to a dict.
        TODO: Have this work for GDocs.
    '''
    app.logger.info('Asking for', organization.projects_list_url)
    got = get(organization.projects_list_url)

    # If projects_list_url is a json file
    try:
        projects = [dict(organization_name=organization.name, code_url=item)
                    for item in got.json()]

    # If projects_list_url is a type of csv
    except ValueError:
        data = got.text.splitlines()
        dialect = Sniffer().sniff(data[0])
        projects = list(DictReader(data, dialect=dialect))
        for project in projects:
            project['organization_name'] = organization.name

    map(update_project_info, projects)

    return projects

def update_project_info(project):
    ''' Update info from Github, if it's missing.

        Modify the project in-place and return nothing.

        Complete repository project details go into extras, for example
        project details from Github can be found under "github_details".

        Github_details is specifically expected to be used on this page:
        http://opengovhacknight.org/projects.html
    '''
    if 'code_url' not in project:
        return project

    _, host, path, _, _, _ = urlparse(project['code_url'])

    # Get the Github attributes
    if host == 'github.com':
        repo_url = 'https://api.github.com/repos' + path

        got = get_github_api(repo_url)

        if got.status_code in range(400, 499):
            if got.status_code == 404:
                app.logger.error(repo_url + ' doesn\'t exist.')
                return project
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

def reformat_project_info_for_chicago(all_projects):
    ''' Return a clone of the project list, formatted for use by opengovhacknight.org.

        The representation here is specifically expected to be used on this page:
        http://opengovhacknight.org/projects.html

        See discussion at
        https://github.com/codeforamerica/civic-json-worker/issues/18
    '''
    return [project['github_details'] for project in all_projects]

def count_people_totals(all_projects):
    ''' Create a list of people details based on project details.

        Request additional data from Github API for each person.

        See discussion at
        https://github.com/codeforamerica/civic-json-worker/issues/18
    '''
    users, contributors = [], []
    for project in all_projects:
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

def save_organization_info(session, org_dict):
    ''' Save a dictionary of organization info to the datastore session.

        Return an app.Organization instance.
    '''
    # Select an existing organization by name.
    filter = Organization.name == org_dict['name']
    existing_org = session.query(Organization).filter(filter).first()

    # If this is a new organization, save and return it.
    if not existing_org:
        new_organization = Organization(**org_dict)
        session.add(new_organization)
        # session.commit()
        return new_organization

    # Mark the existing organization for safekeeping
    existing_org.keep = True

    # Update existing organization details.
    for (field, value) in org_dict.items():
        setattr(existing_org, field, value)

    # Flush existing object, to prevent a sqlalchemy.orm.exc.StaleDataError.
    session.flush()

    return existing_org

def save_project_info(session, proj_dict):
    ''' Save a dictionary of project info to the datastore session.

        Return an app.Project instance.
    '''
    # Select the current project, filtering on name AND organization.
    filter = Project.name == proj_dict['name'], Project.organization_name == proj_dict['organization_name']
    existing_project = session.query(Project).filter(*filter).first()

    # If this is a new project, save and return it.
    if not existing_project:
        new_project = Project(**proj_dict)
        session.add(new_project)
        return new_project

    # Mark the existing project for safekeeping.
    existing_project.keep = True

    # Update existing project details
    for (field, value) in proj_dict.items():
        setattr(existing_project, field, value)

    # Flush existing object, to prevent a sqlalchemy.orm.exc.StaleDataError.
    session.flush()

    return existing_project

def save_event_info(session, event_dict):
    '''
        Save a dictionary of event into to the datastore session then return
        that event instance
    '''
    # Select the current event, filtering on name AND organization.
    filter = Event.name == event_dict['name'], Event.organization_name == event_dict['organization_name']
    existing_event = session.query(Event).filter(*filter).first()

    # If this is a new event, save and return it.
    if not existing_event:
        new_event = Event(**event_dict)
        session.add(new_event)
        return new_event

    # Mark the existing event for safekeeping.
    existing_event.keep = True

    # Update existing event details
    for (field, value) in event_dict.items():
        setattr(existing_event, field, value)

    # Flush existing object, to prevent a sqlalchemy.orm.exc.StaleDataError.
    session.flush()

def get_event_group_identifier(events_url):
    parse_result = urlparse(events_url)
    url_parts = parse_result.path.split('/')
    identifier = url_parts.pop()
    if not identifier:
        identifier = url_parts.pop()
    if(match('^[A-Za-z0-9-]+$', identifier)):
        return identifier
    else:
        return None

def main():
    # Mark everything for deletion at first.
    db.session.execute(db.update(Event, values={Event.keep: False}))
    db.session.execute(db.update(Project, values={Project.keep: False}))
    db.session.execute(db.update(Organization, values={Organization.keep: False}))

    # Iterate over organizations and projects, saving them to db.session.
    for org_info in get_organizations():
        organization = save_organization_info(db.session, org_info)

        get_stories(organization)

        if not organization.projects_list_url:
            continue

        app.logger.info("Gathering all of %s's projects." % organization.name)

        projects = get_projects(organization)

        for proj_info in projects:
            save_project_info(db.session, proj_info)

        app.logger.info("Gathering all of %s's events." % organization.name)

        identifier = get_event_group_identifier(organization.events_url)
        if identifier is None:
            app.logger.error("%s does not have a valid events url" % organization.name)
        else:
            events = get_meetup_events(organization, identifier)
            if events is not None:
                for event in events:
                    save_event_info(db.session, event)

    # Remove everything marked for deletion.
    db.session.execute(db.delete(Event).where(Event.keep == False))
    db.session.execute(db.delete(Project).where(Project.keep == False))
    db.session.execute(db.delete(Organization).where(Organization.keep == False))
    db.session.commit()

if __name__ == "__main__":
    main()
