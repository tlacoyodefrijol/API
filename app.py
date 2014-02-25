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
# Models
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

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode())
    code_url = db.Column(db.Unicode())
    link_url = db.Column(db.Unicode())
    description = db.Column(db.Unicode())
    type = db.Column(db.Unicode())
    categories = db.Column(db.Unicode())
    github_details = db.Column(JsonType())
    brigade = db.Column(db.Unicode)
    keep = db.Column(db.Boolean())
    
    def __init__(self, name, code_url=None, link_url=None,
                 description=None, type=None, categories=None, github_details=None, brigade=None, keep=None):
        self.name = name
        self.code_url = code_url
        self.link_url = link_url
        self.description = description
        self.type = type
        self.categories = categories
        self.github_details = github_details
        self.brigade = brigade
        self.keep = True


# -------------------
# API
# -------------------

manager = flask.ext.restless.APIManager(app, flask_sqlalchemy_db=db)
exclude_columns = ['id','keep']
manager.create_api(Project, methods=['GET'], exclude_columns=exclude_columns, collection_name='projects', max_results_per_page=-1)


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
