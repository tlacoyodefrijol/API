# -------------------
# Imports
# -------------------

from flask import Flask, make_response, request, current_app
from datetime import datetime, timedelta
from functools import update_wrapper
import json, os, requests
from flask.ext.heroku import Heroku
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy import types
import flask.ext.restless


# -------------------
# Init
# -------------------

app = Flask(__name__)
heroku = Heroku(app)
db = SQLAlchemy(app)


# -------------------
# Settings
# -------------------

# THE_KEY = os.environ['FLASK_KEY']

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
    '''
    #Columns
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(), unique=True)
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
    events = db.relationship('Event', backref='organization', lazy='dynamic')
    stories = db.relationship('Story', backref='organization', lazy='dynamic')
    projects = db.relationship('Project', backref='organization', lazy='dynamic')

    def __init__(self, name=None, website=None, events_url=None,
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

class Story(db.Model):
    '''
        Blog posts and tweets from a Brigade.
    '''
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode())
    link = db.Column(db.Unicode())
    type = db.Column(db.Unicode())
    organization_name = db.Column(db.Unicode(), db.ForeignKey('organization.name'))

    def __init__(self, title=None, link=None, type=None, organization_name=None):
        self.title = title
        self.link = link
        self.type = type
        self.organization_name = organization_name

class Project(db.Model):
    '''
    '''
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode())
    code_url = db.Column(db.Unicode())
    link_url = db.Column(db.Unicode())
    description = db.Column(db.Unicode())
    type = db.Column(db.Unicode())
    categories = db.Column(db.Unicode())
    github_details = db.Column(JsonType())
    organization_name = db.Column(db.Unicode(), db.ForeignKey('organization.name'))
    keep = db.Column(db.Boolean())

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
    '''
    # Columns
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode())
    description = db.Column(db.Unicode())
    event_url = db.Column(db.Unicode())
    location = db.Column(db.Unicode())
    start_time = db.Column(db.DateTime())
    end_time = db.Column(db.DateTime())
    organization_name = db.Column(db.Unicode(),db.ForeignKey('organization.name'))
    keep = db.Column(db.Boolean())

    def __init__(self, name, location, event_url, start_time, created_at,
                 organization_name, end_time=None, description=None):
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
kwargs = dict(methods=['GET'], exclude_columns=['keep'], max_results_per_page=-1)
manager.create_api(Organization, collection_name='organizations', **kwargs)
manager.create_api(Story, collection_name='stories', **kwargs)
manager.create_api(Project, collection_name='projects', **kwargs)

# -------------------
# Routes
# -------------------

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
