import unittest, requests, json, os

from app import *

class cfapi_tests(unittest.TestCase):
    
    def setUp(self):
        # Set up the database settings
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://hackyourcity@localhost/civic_json_worker_test'
        db.create_all()
        self.app = app.test_client()
        
        # Fill up the DB
        self.test_organization = {
            "city": "San Francisco, CA",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "name": "Code for San Francisco",
            "projects_list_url": "https://github.com/sfbrigade",
            "rss": "https://groups.google.com/forum/feed/code-for-san-francisco/msgs/rss.xml?num=15",
            "type": "Brigade",
            "website": "http://codeforsanfrancisco.org/"
        }
        test_organization_obj = Organization(**self.test_organization)
        db.session.add(test_organization_obj)

        self.test_story = {
            "link": "http://www.codeforamerica.org/blog/2014/03/14/four-great-years/",
            "title": "Four Great Years",
            "type": "blog",
            "organization_name": "Code for San Francisco",
        }
        test_story_obj = Story(**self.test_story)
        db.session.add(test_story_obj)

        self.test_event = {
            "description": '<p>To contribute code, see our "repo": <a href="https://github.com/sfbrigade" class="linkified">"https"://github.com/sfbrigade</a></p> <p>We are on irc.freenode.net #sfbrigade</p>',
            "created_at": "2013-01-01T01:00:00",
            "end_time": "2013-04-04T01:00:00",
            "event_url": "http://www.meetup.com/Code-for-San-Francisco-Civic-Hack-Night/events/110712692/",
            "location": "155 9th St., San Francisco, CA, us",
            "name": "Weekly Civic Hack Night - Planning Meeting!",
            "start_time": "2013-04-04T01:00:00",
            "organization_name": "Code for San Francisco"
        }
        test_event_obj = Event(**self.test_event)
        db.session.add(test_event_obj)

        self.test_project = {
            "categories": "",
            "code_url": "https://github.com/BetaNYC/ReinventNYC.gov",
            "description": "Before BetaNYC was an organization, we were an award winning hackathon project. This is our submission to the Reinvent NYC.gov hackathon.",
            "github_details": {},
            "link_url": "http://google.com",
            "name": "ReinventNYC.gov",
            "type": "",
            "organization_name": "Code for San Francisco"
        }
        test_project_obj = Project(**self.test_project)
        db.session.add(test_project_obj)

        db.session.commit()

        self.headers = [('Content-Type', 'application/json')]

    def tearDown(self):
        db.drop_all()


    # Test API -----------------------

    def test_headers(self):
        response = self.app.get('/api/organizations')
        assert response.headers['Access-Control-Allow-Origin']  == '*'
        assert response.headers['Content-Type']  == 'application/json'

    def test_brigade_name_request(self):
        response = self.app.get('/api/organizations/Code for San Francisco')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        assert isinstance(response['city'], unicode)
        assert isinstance(response['events'], list)
        assert isinstance(response['latitude'], float)
        assert isinstance(response['longitude'], float)
        assert isinstance(response['name'], unicode)
        assert isinstance(response['projects'], list)
        assert isinstance(response['projects_list_url'], unicode)
        assert isinstance(response['rss'], unicode)
        assert isinstance(response['stories'], list)
        assert isinstance(response['type'], unicode)
        assert isinstance(response['website'], unicode)

    def test_organizations(self):
        response = self.app.get('/api/organizations')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        assert isinstance(response['objects'], list)
        assert isinstance(response['objects'][0]['city'], unicode)
        assert isinstance(response['objects'][0]['events'], list)
        assert isinstance(response['objects'][0]['latitude'], float)
        assert isinstance(response['objects'][0]['longitude'], float)
        assert isinstance(response['objects'][0]['name'], unicode)
        assert isinstance(response['objects'][0]['projects'], list)
        assert isinstance(response['objects'][0]['projects_list_url'], unicode)
        assert isinstance(response['objects'][0]['rss'], unicode)
        assert isinstance(response['objects'][0]['stories'], list)
        assert isinstance(response['objects'][0]['type'], unicode)
        assert isinstance(response['objects'][0]['website'], unicode)

    def test_projects(self):
        response = self.app.get('/api/projects')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        assert isinstance(response['objects'], list)
        assert isinstance(response['objects'][0]['categories'], unicode)
        assert isinstance(response['objects'][0]['code_url'], unicode)
        assert isinstance(response['objects'][0]['description'], unicode)
        assert isinstance(response['objects'][0]['github_details'], dict)
        assert isinstance(response['objects'][0]['id'], int)
        assert isinstance(response['objects'][0]['link_url'], unicode)
        assert isinstance(response['objects'][0]['name'], unicode)
        assert isinstance(response['objects'][0]['organization'], dict)
        assert isinstance(response['objects'][0]['organization_name'], unicode)
        assert isinstance(response['objects'][0]['type'], unicode)

    def test_stories(self):
        response = self.app.get('/api/stories')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        assert isinstance(response['objects'], list)
        assert isinstance(response['objects'][0]['id'], int)
        assert isinstance(response['objects'][0]['link'], unicode)
        assert isinstance(response['objects'][0]['organization'], dict)
        assert isinstance(response['objects'][0]['organization_name'], unicode)
        assert isinstance(response['objects'][0]['title'], unicode)
        assert isinstance(response['objects'][0]['type'], unicode)

    def test_events(self):
        response = self.app.get('/api/events')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        assert isinstance(response['objects'], list)
        assert isinstance(response['objects'][0]['description'], unicode)
        assert isinstance(response['objects'][0]['end_time'], unicode)
        assert isinstance(response['objects'][0]['event_url'], unicode)
        assert isinstance(response['objects'][0]['id'], int)
        assert isinstance(response['objects'][0]['location'], unicode)
        assert isinstance(response['objects'][0]['name'], unicode)
        assert isinstance(response['objects'][0]['organization'], dict)
        assert isinstance(response['objects'][0]['organization_name'], unicode)
        assert isinstance(response['objects'][0]['start_time'], unicode)

if __name__ == '__main__':
    unittest.main()
    