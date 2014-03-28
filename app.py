# -------------------
# Imports
# -------------------

from flask import Flask, make_response, request, current_app, jsonify
from datetime import datetime, timedelta
from functools import update_wrapper
import json, os, requests, time
from flask.ext.heroku import Heroku
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy import types
import flask.ext.restless
from dictalchemy import make_class_dictable
from urlparse import urlparse
from urllib import quote

# -------------------
# Init
# -------------------

app = Flask(__name__)
heroku = Heroku(app)
db = SQLAlchemy(app)
make_class_dictable(db.Model)

# -------------------
# Settings
# -------------------
@app.url_value_preprocessor
def clean_urls(endpoint, values):
    '''
    Before every request, change underscores to spaces.
    /api/organizations/Code_for_America
    will search the db for Code for America
    '''
    if values:
        if "instid" in values:
            if values["instid"]:
                if "_" in values["instid"]:
                    values["instid"] = values["instid"].replace("_", " ")
        if "organization_name" in values:
            if "_" in values["organization_name"]:
                values["organization_name"] = values["organization_name"].replace("_", " ")

def add_cors_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, PATCH, DELETE, OPTIONS'
    return response
app.after_request(add_cors_header)


# -------------------
# Types
# -------------------

class JsonType(Mutable, types.TypeDecorator):
    ''' JSON wrapper type for TEXT database storage.

        References:
        http://stackoverflow.com/questions/4038314/sqlalchemy-json-as-blob-text
        http://docs.sqlalchemy.org/en/rel_0_9/orm/extensions/mutable.html
    '''
    impl = types.Unicode

    def process_bind_param(self, value, engine):
        return unicode(json.dumps(value))

    def process_result_value(self, value, engine):
        if value:
            return json.loads(value)
        else:
            # default can also be a list
            return {}


# -------------------
# Models
# -------------------

class Organization(db.Model):
    '''
        Brigades and other civic tech organizations
    '''
    #Columns
    name = db.Column(db.Unicode(), primary_key=True)
    website = db.Column(db.Unicode())
    events_url = db.Column(db.Unicode())
    rss = db.Column(db.Unicode())
    projects_list_url = db.Column(db.Unicode())
    type = db.Column(db.Unicode())
    city = db.Column(db.Unicode())
    latitude = db.Column(db.Float())
    longitude = db.Column(db.Float())
    keep = db.Column(db.Boolean())

    # Relationships
    events = db.relationship('Event')
    recent_stories = db.relationship('Story') # Stories already limited to two most recent
    projects = db.relationship('Project')

    def __init__(self, name, website=None, events_url=None,
                 rss=None, projects_list_url=None, type=None, city=None, latitude=None, longitude=None):
        self.name = name
        self.website = website
        self.events_url = events_url
        self.rss = rss
        self.projects_list_url = projects_list_url
        self.type = type
        self.city = city
        self.latitude = latitude
        self.longitude = longitude
        self.keep = True

    def recent_events(self):
        '''
            Return the two most recent events
        '''
        recent_events = Event.query.filter_by(organization_name=self.name).order_by(Event.start_time.desc()).limit(2).all()
        recent_events_json = [row.asdict() for row in recent_events]
        return recent_events_json

    def recent_projects(self):
        '''
            Return the three most recent projects
        '''
        all_projects = Project.query.filter_by(organization_name=self.name).all()
        all_projects_json = [project.asdict() for project in all_projects]
        all_projects_json.sort(key=lambda k: k['github_details']['updated_at'], reverse=True)
        recent_projects = all_projects_json[0:3]
        return recent_projects

    def all_events(self):
        ''' API link to all an orgs events
        '''
        scheme, host, _, _, _, _ = urlparse(request.url)
        # Make a nice org name
        organization_name = quote(self.name.replace(" ","_"))
        return '%s://%s/api/organizations/%s/events' % (scheme, host, organization_name)

    def all_projects(self):
        ''' API link to all an orgs projects
        '''
        scheme, host, _, _, _, _ = urlparse(request.url)
        # Make a nice org name
        organization_name = quote(self.name.replace(" ","_"))
        return '%s://%s/api/organizations/%s/projects' % (scheme, host, organization_name)

    def all_stories(self):
        ''' API link to all an orgs stories
        '''
        scheme, host, _, _, _, _ = urlparse(request.url)
        # Make a nice org name
        organization_name = quote(self.name.replace(" ","_"))
        return '%s://%s/api/organizations/%s/stories' % (scheme, host, organization_name)

class Story(db.Model):
    '''
        Blog posts from a Brigade.
    '''
    # Columns
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.Unicode())
    link = db.Column(db.Unicode())
    type = db.Column(db.Unicode())
    keep = db.Column(db.Boolean())

    # Relationships
    organization = db.relationship('Organization')
    organization_name = db.Column(db.Unicode(), db.ForeignKey('organization.name'))

    def __init__(self, title=None, link=None, type=None, organization_name=None):
        self.title = title
        self.link = link
        self.type = type
        self.organization_name = organization_name
        self.keep = True

class Project(db.Model):
    '''
        Civic tech projects on GitHub
    '''
    # Columns
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Unicode())
    code_url = db.Column(db.Unicode())
    link_url = db.Column(db.Unicode())
    description = db.Column(db.Unicode())
    type = db.Column(db.Unicode())
    categories = db.Column(db.Unicode())
    github_details = db.Column(JsonType())
    keep = db.Column(db.Boolean())

    # Relationships
    organization = db.relationship('Organization')
    organization_name = db.Column(db.Unicode(), db.ForeignKey('organization.name'))

    def __init__(self, name, code_url=None, link_url=None,
                 description=None, type=None, categories=None,
                 github_details=None, organization_name=None, keep=None):
        self.name = name
        self.code_url = code_url
        self.link_url = link_url
        self.description = description
        self.type = type
        self.categories = categories
        self.github_details = github_details
        self.organization_name = organization_name
        self.keep = True

class Event(db.Model):
    '''
        Organizations events from Meetup
    '''
    # Columns
    id  = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Unicode())
    description = db.Column(db.Unicode())
    event_url = db.Column(db.Unicode())
    location = db.Column(db.Unicode())
    created_at = db.Column(db.Unicode())
    start_time = db.Column(db.DateTime())
    end_time = db.Column(db.DateTime())
    keep = db.Column(db.Boolean())

    # Relationships
    organization = db.relationship('Organization')
    organization_name = db.Column(db.Unicode(), db.ForeignKey('organization.name'))

    def __init__(self, name, event_url, start_time, created_at,
                 organization_name, location=None, end_time=None, description=None):
        self.name = name
        self.description = description
        self.location = location
        self.event_url = event_url
        self.start_time = start_time
        self.end_time = end_time
        self.organization_name = organization_name
        self.created_at = created_at
        self.keep = True

# -------------------
# API
# -------------------
manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)
kwargs = dict(exclude_columns=['keep'], max_results_per_page=None)
org_kwargs = kwargs.copy()
org_kwargs['include_methods'] = ['recent_events','recent_projects','all_stories','all_events','all_projects']
org_kwargs['exclude_columns'] = ['keep','events','projects']
manager.create_api(Organization, collection_name='organizations', **org_kwargs)
manager.create_api(Story, collection_name='stories', **kwargs)
manager.create_api(Project, collection_name='projects', **kwargs)
manager.create_api(Event, collection_name='events', **kwargs)

@app.route('/api/organizations.geojson')
def get_organizations_geojson():
    ''' GeoJSON response option for organizations.
    '''
    geojson = dict(type='GeometryCollection', features=[])

    for org in db.session.query(Organization):
        # The unique identifier of an organization is its name.
        id = org.name

        # Pick out all the field names without an underscore as the first char.
        keys = [k for k in org.__dict__.keys() if not k.startswith('_')]

        # Pick out all the properties that aren't part of the location.
        names = [k for k in keys if k not in ('latitude', 'longitude', 'keep')]
        props = dict([(k, getattr(org, k)) for k in names])

        # GeoJSON Point geometry, http://geojson.org/geojson-spec.html#point
        geom = dict(type='Point', coordinates=[org.longitude, org.latitude])

        feature = dict(type='Feature', id=id, properties=props, geometry=geom)
        geojson['features'].append(feature)

    response = make_response(json.dumps(geojson, indent=2))
    response.headers['Content-Type'] = 'application/json'

    return response

@app.route("/api/organizations/<organization_name>/events")
def get_orgs_events(organization_name):
    '''
        A cleaner url for getting an organizations events
        Better than /api/events?q={"filters":[{"name":"organization_name","op":"eq","val":"Code for San Francisco"}]}
    '''
    orgs_events = Event.query.filter_by(organization_name=organization_name).all()
    orgs_events = [event.asdict() for event in orgs_events]
    response = {
        "num_results" : len(orgs_events),
        "objects" : orgs_events,
        "page" : 1,
        "total_pages" : 1
    }
    return jsonify(response)

@app.route("/api/organizations/<organization_name>/stories")
def get_orgs_stories(organization_name):
    '''
        A cleaner url for getting an organizations stories
    '''
    orgs_stories = Story.query.filter_by(organization_name=organization_name).all()
    orgs_stories = [story.asdict() for story in orgs_stories]
    response = {
        "num_results" : len(orgs_stories),
        "objects" : orgs_stories,
        "page" : 1,
        "total_pages" : 1
    }
    return jsonify(response)

@app.route("/api/organizations/<organization_name>/projects")
def get_orgs_projects(organization_name):
    '''
        A cleaner url for getting an organizations projects
    '''
    orgs_projects = Project.query.filter_by(organization_name=organization_name).all()
    orgs_projects = [project.asdict() for project in orgs_projects]
    response = {
        "num_results" : len(orgs_projects),
        "objects" : orgs_projects,
        "page" : 1,
        "total_pages" : 1
    }
    return jsonify(response)


# -------------------
# Routes
# -------------------

@app.route('/.well-known/status')
def well_known_status():
    ''' Return status information for Engine Light.

        http://engine-light.codeforamerica.org
    '''
    try:
        org = db.session.query(Organization).limit(1).first()
        project = db.session.query(Project).limit(1).first()

        if not hasattr(project, 'name'):
            status = 'Sample project is missing a name'

        elif not hasattr(org, 'name'):
            status = 'Sample project is missing a name'

        else:
            status = 'ok'

    except Exception, e:
        status = 'Error: ' + str(e)

    state = dict(status=status, updated=int(time.time()), resources=[])
    state.update(dict(dependencies=['Meetup', 'Github', 'PostgreSQL']))

    response = make_response(json.dumps(state, indent=2))
    response.headers['Content-Type'] = 'application/json'

    return response

@app.route("/")
def index():
    return '''<html>
<head>
    <title>Civic Tech Movement API</title>
</head>
<body>
    <p>Read more about me at <a href="https://github.com/codeforamerica/civic-json-worker#readme">codeforamerica/civic-json-worker</a>.</p>
    <p>Some data:</p>
    <ul>
    <li><a href="api/projects">Projects</a></li>
    </ul>
</body>
</html>'''

if __name__ == "__main__":
    app.run(debug=True)
