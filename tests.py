import unittest, requests, json, os
from datetime import datetime
from urlparse import urlparse

from app import *
from factories import OrganizationFactory, ProjectFactory, EventFactory, StoryFactory

class ApiTest(unittest.TestCase):

    def setUp(self):
        # Set up the database settings
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres@localhost/civic_json_worker_test'
        db.create_all()
        self.app = app.test_client()

    def tearDown(self):
        db.drop_all()

    # Test API -----------------------

    def test_recent_events(self):
        '''
        Test that only the two most recent events are being returned
        '''
        organization = OrganizationFactory(name='Collective of Ericas')
        db.session.flush()
        # Create multiple events with different times
        oldest_event = EventFactory(organization_name=organization.name, name="Oldest event", start_time_notz=datetime(2014, 1, 1, 0, 1, 0))
        second_most_recent_event = EventFactory(organization_name=organization.name, name="Second most recent event", start_time_notz=datetime(2014, 1, 1, 1, 1, 0))
        most_recent_event = EventFactory(organization_name=organization.name, name="Most recent event", start_time_notz=datetime(2014, 1, 2, 1, 0, 0))
        old_event = EventFactory(organization_name=organization.name, name="Old event", start_time_notz=datetime(2014, 1, 1, 1, 0, 0))

        db.session.flush()
        response = self.app.get('/api/organizations/Collective%20of%20Ericas')
        response_json = json.loads(response.data)
        self.assertEqual(len(response_json['recent_events']), 2)
        self.assertEqual(response_json['recent_events'][0]['name'], "Most recent event")
        self.assertEqual(response_json['recent_events'][1]['name'], "Second most recent event")
        self.assertEqual(response_json['recent_events'][0]['organization_name'], "Collective of Ericas")

    def test_recent_stories(self):
        '''
        Test that only the two most recent stories are being returned
        '''
        organization = OrganizationFactory(name='Collective of Ericas')
        db.session.flush()

        StoryFactory(organization_name='Collective of Ericas', title='First Story')
        StoryFactory(organization_name='Collective of Ericas', title='Second Story')
        db.session.flush()

        response = self.app.get('/api/organizations/Collective%20of%20Ericas')
        response_json = json.loads(response.data)
        self.assertEqual(response_json['recent_stories'][0]['title'], 'First Story')
        self.assertEqual(response_json['recent_stories'][1]['title'], 'Second Story')

    def test_headers(self):
        OrganizationFactory()
        db.session.flush()

        response = self.app.get('/api/organizations')
        assert response.headers['Access-Control-Allow-Origin']  == '*'
        assert response.headers['Content-Type']  == 'application/json'

    def test_brigade_name_request(self):
        OrganizationFactory(name='Code for San Francisco')
        db.session.flush()

        response = self.app.get('/api/organizations/Code for San Francisco')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        assert isinstance(response['city'], unicode)
        assert isinstance(response['recent_events'], list)
        assert isinstance(response['latitude'], float)
        assert isinstance(response['longitude'], float)
        assert isinstance(response['name'], unicode)
        assert isinstance(response['recent_projects'], list)
        assert isinstance(response['projects_list_url'], unicode)
        assert isinstance(response['rss'], unicode)
        assert isinstance(response['recent_stories'], list)
        assert isinstance(response['type'], unicode)
        assert isinstance(response['website'], unicode)

    def test_organizations(self):
        OrganizationFactory()
        db.session.flush()

        response = self.app.get('/api/organizations')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        assert isinstance(response['pages'], dict)
        assert isinstance(response['objects'], list)
        assert isinstance(response['objects'][0]['api_url'], unicode)
        assert isinstance(response['objects'][0]['city'], unicode)
        assert isinstance(response['objects'][0]['recent_events'], list)
        assert isinstance(response['objects'][0]['latitude'], float)
        assert isinstance(response['objects'][0]['longitude'], float)
        assert isinstance(response['objects'][0]['name'], unicode)
        assert isinstance(response['objects'][0]['recent_projects'], list)
        assert isinstance(response['objects'][0]['projects_list_url'], unicode)
        assert isinstance(response['objects'][0]['rss'], unicode)
        assert isinstance(response['objects'][0]['recent_stories'], list)
        assert isinstance(response['objects'][0]['type'], unicode)
        assert isinstance(response['objects'][0]['website'], unicode)

    def test_projects(self):
        ProjectFactory()
        db.session.flush()

        response = self.app.get('/api/projects')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        assert isinstance(response['pages'], dict)
        assert isinstance(response['objects'], list)
        assert isinstance(response['objects'][0]['categories'], unicode)
        assert isinstance(response['objects'][0]['code_url'], unicode)
        assert isinstance(response['objects'][0]['description'], unicode)
        assert isinstance(response['objects'][0]['github_details'], dict)
        assert isinstance(response['objects'][0]['id'], int)
        assert isinstance(response['objects'][0]['api_url'], unicode)
        assert isinstance(response['objects'][0]['link_url'], unicode)
        assert isinstance(response['objects'][0]['name'], unicode)
        assert isinstance(response['objects'][0]['organization'], dict)
        assert isinstance(response['objects'][0]['organization_name'], unicode)
        assert isinstance(response['objects'][0]['type'], unicode)

    def test_good_orgs_projects(self):
        organization = OrganizationFactory(name="Code for America")
        project = ProjectFactory(organization_name="Code for America")
        db.session.flush()

        response = self.app.get('/api/organizations/Code for America/projects')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        assert isinstance(response, dict)

    def test_bad_orgs_projects(self):
        ProjectFactory()
        db.session.flush()

        response = self.app.get('/api/organizations/Whatever/projects')
        self.assertEqual(response.status_code, 404)

    def test_stories(self):
        StoryFactory()
        db.session.flush()

        response = self.app.get('/api/stories')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        assert isinstance(response['pages'], dict)
        assert isinstance(response['objects'], list)
        assert isinstance(response['objects'][0]['id'], int)
        assert isinstance(response['objects'][0]['link'], unicode)
        assert isinstance(response['objects'][0]['organization'], dict)
        assert isinstance(response['objects'][0]['organization_name'], unicode)
        assert isinstance(response['objects'][0]['title'], unicode)
        assert isinstance(response['objects'][0]['type'], unicode)

    def test_orgs_stories(self):
        organization = OrganizationFactory(name="Code for America")
        story = StoryFactory(organization_name="Code for America")
        db.session.flush()

        response = self.app.get('/api/organizations/Code for America/stories')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        assert isinstance(response, dict)

    def test_events(self):
        EventFactory()
        db.session.flush()

        response = self.app.get('/api/events')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        assert isinstance(response['pages'], dict)
        assert isinstance(response['objects'], list)
        assert isinstance(response['objects'][0]['description'], unicode)
        assert isinstance(response['objects'][0]['end_time'], unicode)
        assert isinstance(response['objects'][0]['event_url'], unicode)
        assert isinstance(response['objects'][0]['api_url'], unicode)
        assert isinstance(response['objects'][0]['id'], int)
        assert isinstance(response['objects'][0]['location'], unicode)
        assert isinstance(response['objects'][0]['name'], unicode)
        assert isinstance(response['objects'][0]['organization'], dict)
        assert isinstance(response['objects'][0]['organization_name'], unicode)
        assert isinstance(response['objects'][0]['start_time'], unicode)

    def test_orgs_events(self):
        organization = OrganizationFactory(name="Code for America")
        event = EventFactory(organization_name="Code for America")
        db.session.flush()

        response = self.app.get('/api/organizations/Code for America/events')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        assert isinstance(response, dict)

    def test_underscores_and_spaces(self):
        organization = OrganizationFactory(name="Code for America")
        db.session.add(organization)
        db.session.commit()

        response = self.app.get('/api/organizations/Code for America')
        self.assertEqual(response.status_code,200)
        response = json.loads(response.data)
        scheme, netloc, path, _, _, _  = urlparse(response["all_events"])
        self.assertTrue("_" in path)
        self.assertFalse(" " in path)
        scheme, netloc, path, _, _, _  = urlparse(response["all_stories"])
        self.assertTrue("_" in path)
        self.assertFalse(" " in path)
        scheme, netloc, path, _, _, _  = urlparse(response["all_projects"])
        self.assertTrue("_" in path)
        self.assertFalse(" " in path)

        response = self.app.get('/api/organizations/Code_for_America')
        self.assertEqual(response.status_code,200)
        response = json.loads(response.data)
        self.assertEqual(response["name"], "Code for America")

        project = ProjectFactory(organization_name="Code for America")
        db.session.add(project)
        db.session.commit()

        response = self.app.get('/api/organizations/Code_for_America/projects')
        self.assertEqual(response.status_code,200)
        response = json.loads(response.data)
        self.assertEqual(response["objects"][0]["organization_name"], "Code for America")

        response = self.app.get('/api/organizations/Code_for_America/projects')
        self.assertEqual(response.status_code,200)
        response = json.loads(response.data)
        self.assertEqual(response["objects"][0]["organization_name"], "Code for America")

        event = EventFactory(organization_name="Code for America")
        db.session.add(event)
        db.session.commit()

        response = self.app.get('/api/organizations/Code for America/events')
        self.assertEqual(response.status_code,200)
        response = json.loads(response.data)
        self.assertEqual(response["objects"][0]["organization_name"], "Code for America")

        response = self.app.get('/api/organizations/Code_for_America/events')
        self.assertEqual(response.status_code,200)
        response = json.loads(response.data)
        self.assertEqual(response["objects"][0]["organization_name"], "Code for America")

        story = StoryFactory(organization_name="Code for America")
        db.session.add(story)
        db.session.commit()

        response = self.app.get('/api/organizations/Code for America/stories')
        self.assertEqual(response.status_code,200)
        response = json.loads(response.data)
        self.assertEqual(response["objects"][0]["organization_name"], "Code for America")

        response = self.app.get('/api/organizations/Code_for_America/stories')
        self.assertEqual(response.status_code,200)
        response = json.loads(response.data)
        self.assertEqual(response["objects"][0]["organization_name"], "Code for America")

if __name__ == '__main__':
    unittest.main()
    