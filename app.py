# -------------------
# Imports
# -------------------

from flask import Flask, make_response, request, current_app
from datetime import timedelta
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
    name = db.Column(db.Unicode(), primary_key=True)
    website = db.Column(db.Unicode())
    events_url = db.Column(db.Unicode())
    rss = db.Column(db.Unicode())
    projects_list_url = db.Column(db.Unicode())
    keep = db.Column(db.Boolean())
    
    def __init__(self, name=None, website=None, events_url=None,
                 rss=None, projects_list_url=None):
        self.name = name
        self.website = website
        self.events_url = events_url
        self.rss = rss
        self.projects_list_url = projects_list_url
        self.keep = True

class Project(db.Model):
    '''
    '''
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode())
    code_url = db.Column(db.Unicode())
    link_url = db.Column(db.Unicode())
    description = db.Column(db.Unicode())
    type = db.Column(db.Unicode())
    categories = db.Column(db.Unicode())
    github_details = db.Column(JsonType())
    organization = db.Column(db.Unicode)
    keep = db.Column(db.Boolean())
    
    def __init__(self, name, code_url=None, link_url=None,
                 description=None, type=None, categories=None,
                 github_details=None, organization=None, keep=None):
        self.name = name
        self.code_url = code_url
        self.link_url = link_url
        self.description = description
        self.type = type
        self.categories = categories
        self.github_details = github_details
        self.organization = organization
        self.keep = True


# -------------------
# API
# -------------------

manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)

kwargs = dict(methods=['GET'], exclude_columns=['id','keep'], max_results_per_page=-1)
manager.create_api(Organization, collection_name='organizations', **kwargs)
manager.create_api(Project, collection_name='projects', **kwargs)


# -------------------
# Routes
# -------------------

@app.route("/")
def index():
    return "HELLO WORLD"

if __name__ == "__main__":
    app.run(debug=True)
