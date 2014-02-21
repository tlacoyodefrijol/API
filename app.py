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
import flask.ext.restless

BUCKET = os.environ['S3_BUCKET']
THE_KEY = os.environ['FLASK_KEY']

app = Flask(__name__)
heroku = Heroku(app)
db = SQLAlchemy(app)

class Project(db.Model):
    name = db.Column(db.Unicode(), primary_key=True)
    code_url = db.Column(db.Unicode())
    link_url = db.Column(db.Unicode())
    description = db.Column(db.Unicode())
    type = db.Column(db.Unicode())
    categories = db.Column(db.Unicode())
    github_extras = db.Column(db.Unicode())
    keep = db.Column(db.Boolean())
    
    def __init__(self, name, code_url=None, link_url=None,
                 description=None, type=None, categories=None, github_extras=None):
        self.name = name
        self.code_url = code_url
        self.link_url = link_url
        self.description = description
        self.type = type
        self.categories = categories
        self.github_extras = github_extras
        self.keep = True

manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)
manager.create_api(Project, methods=['GET'], collection_name='projects', max_results_per_page=-1)

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

@app.route('/add-project/', methods=['POST'])
@crossdomain(origin="*")
def submit_project():
    project_url = request.form.get('project_url')
    project_details = update_project(project_url)
    if project_details:
        resp = make_response(json.dumps(project_details))
        resp.headers['Content-Type'] = 'application/json'
        return resp
    else:
        return make_response('The URL you submitted, %s, does not appear to be a valid Github repo' % project_url, 400)

@app.route('/delete-project/', methods=['POST'])
def delete_project():
    if request.form.get('the_key') == THE_KEY:
        project_url = request.form.get('project_url')
        conn = S3Connection()
        bucket = conn.get_bucket(BUCKET)
        pj_list = Key(bucket)
        pj_list.key = 'projects.json'
        project_list = json.loads(pj_list.get_contents_as_string())
        try:
            project_list.remove(project_url)
            pj_list.set_contents_from_string(json.dumps(project_list))
            pj_list.set_metadata('Content-Type', 'application/json')
            pj_list.set_acl('public-read')
            resp = make_response('Deleted %s' % project_url)
        except ValueError:
            resp = make_response('%s is not in the registry', 400)
        pj_list.close()
    else:
        resp = make_response("I can't do that Dave", 400)
    return resp

@app.route('/update-projects/', methods=['GET'])
def update_projects():
    update_pjs()
    resp = make_response('Executed update task')
    return resp

@app.route("/")
def index():
    return "HELLO WORLD"

if __name__ == "__main__":
    app.run(debug=True, port=6666)
