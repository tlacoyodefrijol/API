# -------------------
# Imports
# -------------------

from flask import Flask, make_response, request, current_app
from datetime import timedelta
from functools import update_wrapper
import json
import os
import requests
from tasks import update_project
# from run_update import update_projects as update_pjs
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from flask.ext.heroku import Heroku
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSON
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

BUCKET = os.environ['S3_BUCKET']
THE_KEY = os.environ['FLASK_KEY']

def add_cors_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, PUT, PATCH, DELETE, OPTIONS'
    return response
app.after_request(add_cors_header)


# -------------------
# Models
# -------------------

class Project(db.Model):
    name = db.Column(db.Unicode(), primary_key=True)
    code_url = db.Column(db.Unicode())
    link_url = db.Column(db.Unicode())
    description = db.Column(db.Unicode())
    type = db.Column(db.Unicode())
    categories = db.Column(db.Unicode())
    github_extras = db.Column(db.Unicode())
    
    def __init__(self, name, code_url=None, link_url=None,
                 description=None, type=None, categories=None, github_extras=None):
        self.name = name
        self.code_url = code_url
        self.link_url = link_url
        self.description = description
        self.type = type
        self.categories = categories
        self.github_extras = github_extras
        self.brigade = brigade


# -------------------
# API
# -------------------

manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(Project, methods=['GET'], collection_name='projects', max_results_per_page=-1)


# -------------------
# Routes
# -------------------

# @app.route('/add-project/', methods=['POST'])
# @crossdomain(origin="*")
# def submit_project():
#     project_url = request.form.get('project_url')
#     project_details = update_project(project_url)
#     if project_details:
#         resp = make_response(json.dumps(project_details))
#         resp.headers['Content-Type'] = 'application/json'
#         return resp
#     else:
#         return make_response('The URL you submitted, %s, does not appear to be a valid Github repo' % project_url, 400)

# @app.route('/delete-project/', methods=['POST'])
# def delete_project():
#     if request.form.get('the_key') == THE_KEY:
#         project_url = request.form.get('project_url')
#         conn = S3Connection()
#         bucket = conn.get_bucket(BUCKET)
#         pj_list = Key(bucket)
#         pj_list.key = 'projects.json'
#         project_list = json.loads(pj_list.get_contents_as_string())
#         try:
#             project_list.remove(project_url)
#             pj_list.set_contents_from_string(json.dumps(project_list))
#             pj_list.set_metadata('Content-Type', 'application/json')
#             pj_list.set_acl('public-read')
#             resp = make_response('Deleted %s' % project_url)
#         except ValueError:
#             resp = make_response('%s is not in the registry', 400)
#         pj_list.close()
#     else:
#         resp = make_response("I can't do that Dave", 400)
#     return resp

# @app.route('/update-projects/', methods=['GET'])
# def update_projects():
#     update_pjs()
#     resp = make_response('Executed update task')
#     return resp

@app.route("/")
def index():
    return "HELLO WORLD"

if __name__ == "__main__":
    app.run(debug=True)
