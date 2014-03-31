# -------------------
# Imports
# -------------------

from flask import Flask, make_response, request, current_app, jsonify, render_template
from datetime import datetime, timedelta
from functools import update_wrapper
import json, os, requests, time
from flask.ext.heroku import Heroku
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy import types
import flask.ext.restless
from dictalchemy import make_class_dictable
from dateutil.tz import tzoffset
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
        recent_events = Event.query.filter_by(organization_name=self.name).order_by(Event.start_time_notz.desc()).limit(2).all()
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
    
    def api_id(self):
        '''
        '''
        return quote(self.name.replace(" ","_"))

    def api_url(self):
        ''' API link to itself
        '''
        scheme, host, _, _, _, _ = urlparse(request.url)
        # Make a nice org name
        organization_name = self.api_id()
        return '%s://%s/api/organizations/%s' % (scheme, host, organization_name)

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

    @staticmethod
    def include_methods():
        return ['api_url']
    
    @staticmethod
    def exclude_columns():
        return ['keep']
    
    def api_url(self):
        ''' API link to itself
        '''
        scheme, host, _, _, _, _ = urlparse(request.url)
        return '%s://%s/api/projects/%s' % (scheme, host, str(self.id))
    
    def asdict(self):
        ''' Return Project as a dictionary, with some properties tweaked.
        
            Projects are represented as dictionaries in two custom API responses:
            Under an organization's shortlist of current projects, and as part
            of an organization's complete list of projects. This method is used
            to centralize the tweaks to make each representation consistent.
        '''
        project_dict = db.Model.asdict(self)
        
        for key in Project.exclude_columns():
            del project_dict[key]

        for key in Project.include_methods():
            project_dict[key] = getattr(self, key)()

        return project_dict

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
    start_time_notz = db.Column(db.DateTime(False))
    end_time_notz = db.Column(db.DateTime(False))
    utc_offset = db.Column(db.Integer())
    keep = db.Column(db.Boolean())

    # Relationships
    organization = db.relationship('Organization')
    organization_name = db.Column(db.Unicode(), db.ForeignKey('organization.name'))

    def __init__(self, name, event_url, start_time_notz, created_at, utc_offset,
                 organization_name, location=None, end_time_notz=None, description=None):
        self.name = name
        self.description = description
        self.location = location
        self.event_url = event_url
        self.start_time_notz = start_time_notz
        self.utc_offset = utc_offset
        self.end_time_notz = end_time_notz
        self.organization_name = organization_name
        self.created_at = created_at
        self.keep = True
    
    def start_time(self):
        ''' Get a string representation of the start time with UTC offset.
        '''
        if self.start_time_notz is None:
            return None
        tz = tzoffset(None, self.utc_offset)
        st = self.start_time_notz
        dt = datetime(st.year, st.month, st.day, st.hour, st.minute, st.second, tzinfo=tz)
        return dt.strftime('%Y-%m-%d %H:%M:%S %z')
    
    def end_time(self):
        ''' Get a string representation of the end time with UTC offset.
        '''
        if self.end_time_notz is None:
            return None
        tz = tzoffset(None, self.utc_offset)
        et = self.end_time_notz
        dt = datetime(et.year, et.month, et.day, et.hour, et.minute, et.second, tzinfo=tz)
        return dt.strftime('%Y-%m-%d %H:%M:%S %z')
        
    @staticmethod
    def include_methods():
        return 'start_time', 'end_time', 'api_url'
    
    @staticmethod
    def exclude_columns():
        return 'keep', 'start_time_notz', 'end_time_notz', 'utc_offset'
    
    def api_url(self):
        ''' API link to itself
        '''
        scheme, host, _, _, _, _ = urlparse(request.url)
        return '%s://%s/api/events/%s' % (scheme, host, str(self.id))
    
    def asdict(self):
        ''' Return Event as a dictionary, with some properties tweaked.
        
            Events are represented as dictionaries in two custom API responses:
            Under an organization's shortlist of current events, and as part
            of an organization's complete list of events. This method is used
            to centralize the tweaks to make each representation consistent.
        '''
        event_dict = db.Model.asdict(self)
        
        for key in Event.exclude_columns():
            del event_dict[key]

        for key in Event.include_methods():
            event_dict[key] = getattr(self, key)()

        return event_dict

# -------------------
# API
# -------------------

manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)
kwargs = dict(exclude_columns=['keep'], max_results_per_page=None)

org_kwargs = kwargs.copy()
org_kwargs['include_methods'] = ['recent_events','recent_projects','all_stories','all_events','all_projects','api_url']
org_kwargs['exclude_columns'] = ['keep','events','projects']
manager.create_api(Organization, collection_name='organizations', **org_kwargs)

manager.create_api(Story, collection_name='stories', **kwargs)

project_kwargs = kwargs.copy()
project_kwargs.update(dict(include_methods=Project.include_methods()))
manager.create_api(Project, collection_name='projects', **project_kwargs)

event_kwargs = kwargs.copy()
event_kwargs.update(dict(include_methods=Event.include_methods(), exclude_columns=Event.exclude_columns()))
manager.create_api(Event, collection_name='events', **event_kwargs)

@app.route('/api/organizations.geojson')
def get_organizations_geojson():
    ''' GeoJSON response option for organizations.
    '''
    geojson = dict(type='GeometryCollection', features=[])

    for org in db.session.query(Organization):
        # The unique identifier of an organization.
        id = org.api_id()

        # Pick out all the properties that aren't part of the location.
        keys = org.asdict().keys()
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
    # Check org name
    organization = Organization.query.filter_by(name=organization_name).first()
    if not organization:
        return "Organization not found", 404
    # Get event objects
    events = Event.query.filter_by(organization_name=organization_name).all()
    events_dicts = [event.asdict() for event in events]
    
    response = {
        "num_results" : len(events_dicts),
        "objects" : events_dicts,
        "page" : 1,
        "total_pages" : 1
    }
    return jsonify(response)

@app.route("/api/organizations/<organization_name>/stories")
def get_orgs_stories(organization_name):
    '''
        A cleaner url for getting an organizations stories
    '''
    # Check org name
    organization = Organization.query.filter_by(name=organization_name).first()
    if not organization:
        return "Organization not found", 404
    # Get stories objects
    orgs_stories = Story.query.filter_by(organization_name=organization_name).all()
    # Convert them to dicts
    # Remove the keep column
    orgs_stories_as_dicts = []
    for story in orgs_stories:
        story = story.asdict()
        del story['keep']
        orgs_stories_as_dicts.append(story)
    response = {
        "num_results" : len(orgs_stories_as_dicts),
        "objects" : orgs_stories_as_dicts,
        "page" : 1,
        "total_pages" : 1
    }
    return jsonify(response)

@app.route("/api/organizations/<organization_name>/projects")
def get_orgs_projects(organization_name):
    '''
        A cleaner url for getting an organizations projects
    '''
    # Check org name
    organization = Organization.query.filter_by(name=organization_name).first()
    if not organization:
        return "Organization not found", 404
    # Get project objects
    projects = Project.query.filter_by(organization_name=organization_name).all()
    projects_dicts = [project.asdict() for project in projects]

    response = {
        "num_results" : len(projects_dicts),
        "objects" : projects_dicts,
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
    scheme, host, _, _, _, _ = urlparse(request.url)
    return render_template('index.html', api_base='%s://%s' % (scheme, host))

if __name__ == "__main__":
    app.run(debug=True)
