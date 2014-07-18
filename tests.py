#!/usr/bin/env python
# -*- coding: utf8 -*-

import unittest, requests, json, os
from datetime import datetime, timedelta
from urlparse import urlparse

from app import app, db
from factories import OrganizationFactory, ProjectFactory, EventFactory, StoryFactory, IssueFactory

class ApiTest(unittest.TestCase):

    def setUp(self):
        # Set up the database settings
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://postgres@localhost/civic_json_worker_test'
        db.create_all()
        self.app = app.test_client()

    def tearDown(self):
        db.drop_all()

    # Test API -----------------------
    def test_current_projects(self):
        '''
        Show three most recently updated github projects
        '''
        organization = OrganizationFactory(name='Code for San Francisco')
        db.session.flush()

        ProjectFactory(organization_name=organization.name, name="Project 1", github_details={"updated_at":"2014-12-31T00:00:00Z"})
        ProjectFactory(organization_name=organization.name, name="Project 2", github_details={"updated_at":"2014-11-31T00:00:00Z"})
        ProjectFactory(organization_name=organization.name, name="Non Github Project", github_details=None)
        ProjectFactory(organization_name=organization.name, name="Project 3", github_details={"updated_at":"2014-09-31T00:00:00Z"})
        db.session.flush()

        response = self.app.get('/api/organizations/Code for San Francisco')
        response = json.loads(response.data)

        self.assertEqual(len(response['current_projects']), 3)
        self.assertEqual(response['current_projects'][0]['name'], "Project 1")
        self.assertEqual(response['current_projects'][1]['name'], "Project 2")
        self.assertEqual(response['current_projects'][2]['name'], "Project 3")

    def test_current_events(self):
        '''
        The three soonest upcoming events should be returned.
        If there are no events in the future, no events will be returned
        '''
        # Assuming today is Christmas...
        organization = OrganizationFactory(name='Collective of Ericas')
        db.session.flush()

        # Create multiple events, some in the future, one in the past
        EventFactory(organization_name=organization.name, name="Christmas Eve", start_time_notz=datetime.now() - timedelta(1))
        EventFactory(organization_name=organization.name, name="New Years", start_time_notz=datetime.now() + timedelta(7))
        EventFactory(organization_name=organization.name, name="MLK Day", start_time_notz=datetime.now() + timedelta(25))
        EventFactory(organization_name=organization.name, name="Cesar Chavez Day", start_time_notz=datetime.now() + timedelta(37))
        db.session.flush()

        response = self.app.get('/api/organizations/Collective%20of%20Ericas')
        response_json = json.loads(response.data)

        self.assertEqual(len(response_json['current_events']), 2)
        self.assertEqual(response_json['current_events'][0]['name'], "New Years")
        self.assertEqual(response_json['current_events'][1]['name'], "MLK Day")
        self.assertEqual(response_json['current_events'][0]['organization_name'], "Collective of Ericas")

    def test_all_upcoming_events(self):
        '''
        Test the /events/upcoming_events end point.
        '''
        # World Cup teams
        organization = OrganizationFactory(name='USA USA USA')
        db.session.flush()

        # Create multiple events, some in the future, one in the past
        EventFactory(organization_name=organization.name, name="Past Event", start_time_notz=datetime.now() - timedelta(1000))
        EventFactory(organization_name=organization.name, name="Event One", start_time_notz=datetime.now() + timedelta(10))
        EventFactory(organization_name=organization.name, name="Event Four", start_time_notz=datetime.now() + timedelta(100))
        EventFactory(organization_name=organization.name, name="Event Seven", start_time_notz=datetime.now() + timedelta(1000))
        db.session.flush()

        # World Cup teams
        organization = OrganizationFactory(name='Brazil')
        db.session.flush()

        # Create multiple events, some in the future, one in the past
        EventFactory(organization_name=organization.name, name="Past Event", start_time_notz=datetime.now() - timedelta(2000))
        EventFactory(organization_name=organization.name, name="Event Two", start_time_notz=datetime.now() + timedelta(20))
        EventFactory(organization_name=organization.name, name="Event Five", start_time_notz=datetime.now() + timedelta(200))
        EventFactory(organization_name=organization.name, name="Event Eight", start_time_notz=datetime.now() + timedelta(2000))
        db.session.flush()

        # World Cup teams
        organization = OrganizationFactory(name='GER')
        db.session.flush()

        # Create multiple events, some in the future, one in the past
        EventFactory(organization_name=organization.name, name="Past Event", start_time_notz=datetime.now() - timedelta(3000))
        EventFactory(organization_name=organization.name, name="Event Three", start_time_notz=datetime.now() + timedelta(30))
        EventFactory(organization_name=organization.name, name="Event Six", start_time_notz=datetime.now() + timedelta(300))
        EventFactory(organization_name=organization.name, name="Event Nine", start_time_notz=datetime.now() + timedelta(3000))
        db.session.flush()

        response = self.app.get('/api/events/upcoming_events')
        response_json = json.loads(response.data)

        self.assertEqual(len(response_json['objects']), 9)
        self.assertEqual(response_json['objects'][0]['name'], "Event One")
        self.assertEqual(response_json['objects'][1]['name'], "Event Two")
        self.assertEqual(response_json['objects'][8]['name'], "Event Nine")

    def test_current_stories(self):
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
        self.assertEqual(response_json['current_stories'][0]['title'], 'First Story')
        self.assertEqual(response_json['current_stories'][1]['title'], 'Second Story')

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
        assert isinstance(response['current_events'], list)
        assert isinstance(response['latitude'], float)
        assert isinstance(response['longitude'], float)
        assert isinstance(response['name'], unicode)
        assert isinstance(response['current_projects'], list)
        assert isinstance(response['projects_list_url'], unicode)
        assert isinstance(response['rss'], unicode)
        assert isinstance(response['current_stories'], list)
        assert isinstance(response['type'], unicode)
        assert isinstance(response['website'], unicode)

    def test_organizations(self):
        OrganizationFactory()
        db.session.flush()

        response = self.app.get('/api/organizations')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        assert isinstance(response['pages'], dict)
        assert isinstance(response['total'], int)
        assert isinstance(response['objects'], list)
        assert isinstance(response['objects'][0]['api_url'], unicode)
        assert isinstance(response['objects'][0]['city'], unicode)
        assert isinstance(response['objects'][0]['current_events'], list)
        assert isinstance(response['objects'][0]['latitude'], float)
        assert isinstance(response['objects'][0]['longitude'], float)
        assert isinstance(response['objects'][0]['name'], unicode)
        assert isinstance(response['objects'][0]['current_projects'], list)
        assert isinstance(response['objects'][0]['projects_list_url'], unicode)
        assert isinstance(response['objects'][0]['rss'], unicode)
        assert isinstance(response['objects'][0]['current_stories'], list)
        assert isinstance(response['objects'][0]['type'], unicode)
        assert isinstance(response['objects'][0]['website'], unicode)
        assert isinstance(response['objects'][0]['last_updated'], float)
        assert isinstance(response['objects'][0]['started_on'], unicode)

    def test_projects(self):
        ProjectFactory()
        db.session.flush()

        response = self.app.get('/api/projects')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        assert isinstance(response['pages'], dict)
        assert isinstance(response['total'], int)
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

    def test_pagination(self):
        ProjectFactory()
        ProjectFactory()
        ProjectFactory()
        db.session.flush()

        response = self.app.get('/api/projects?per_page=2')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        self.assertEqual(len(response['objects']), 2)
        self.assertEqual(response['pages']['next'], 'http://localhost/api/projects?per_page=2&page=2')
        self.assertEqual(response['pages']['last'], 'http://localhost/api/projects?per_page=2&page=2')
        self.assertNotIn('first', response['pages'])
        self.assertNotIn('prev', response['pages'])

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
        assert isinstance(response['total'], int)
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
        '''
        Return all events past/future ordered by oldest to newest
        '''
        EventFactory()
        db.session.flush()

        response = self.app.get('/api/events')
        response = json.loads(response.data)
        assert isinstance(response, dict)
        assert isinstance(response['pages'], dict)
        assert isinstance(response['total'], int)
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

    def test_utf8_characters(self):
        organization = OrganizationFactory(name=u"Cöde for Ameriça")
        db.session.add(organization)
        db.session.commit()

        response = self.app.get(u'/api/organizations/Cöde for Ameriça')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        assert isinstance(response['name'], unicode)

        response = self.app.get(u'/api/organizations/Cöde-for-Ameriça')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        assert isinstance(response['name'], unicode)

        response = self.app.get('/api/organizations/C%C3%B6de for Ameri%C3%A7a')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        assert isinstance(response['name'], unicode)

        response = self.app.get('/api/organizations/C%C3%B6de-for-Ameri%C3%A7a')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        assert isinstance(response['name'], unicode)

    def test_underscores_and_spaces(self):
        organization = OrganizationFactory(name="Code for America")
        db.session.add(organization)
        db.session.commit()

        response = self.app.get('/api/organizations/Code for America')
        self.assertEqual(response.status_code,200)
        response = json.loads(response.data)
        scheme, netloc, path, _, _, _  = urlparse(response["all_events"])
        self.assertTrue("-" in path)
        self.assertFalse("_" in path)
        self.assertFalse(" " in path)
        scheme, netloc, path, _, _, _  = urlparse(response["all_stories"])
        self.assertTrue("-" in path)
        self.assertFalse("_" in path)
        self.assertFalse(" " in path)
        scheme, netloc, path, _, _, _  = urlparse(response["all_projects"])
        self.assertTrue("-" in path)
        self.assertFalse("_" in path)
        self.assertFalse(" " in path)

        response = self.app.get('/api/organizations/Code-for-America')
        self.assertEqual(response.status_code,200)
        response = json.loads(response.data)
        self.assertEqual(response["name"], "Code for America")

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

    def test_dashes_in_slugs(self):
        organization = OrganizationFactory(name="Code for America")
        event = EventFactory(organization_name="Code for America")
        db.session.flush()

        response = self.app.get('/api/organizations/Code-for-America')
        self.assertEqual(response.status_code,200)
        response = json.loads(response.data)
        self.assertEqual(response["name"], "Code for America")

    def test_org_upcoming_events(self):
        '''
        Only return events occurring in the future
        Make sure that they are ordered from most recent to
        furthest away in the future
        '''
        # Assuming today is Christmas...
        organization = OrganizationFactory(name="International Cat Association")
        db.session.flush()

        # Create multiple events, some in the future, one in the past
        EventFactory(organization_name=organization.name, name="Christmas Eve", start_time_notz=datetime.now() - timedelta(1))
        EventFactory(organization_name=organization.name, name="New Years", start_time_notz=datetime.now() + timedelta(7))
        EventFactory(organization_name=organization.name, name="MLK Day", start_time_notz=datetime.now() + timedelta(25))
        db.session.flush()

        # Check that future events are returned in the correct order
        response = self.app.get('/api/organizations/International Cat Association/upcoming_events')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        self.assertEqual(response['total'], 2)
        self.assertEqual(response['objects'][0]['name'], 'New Years')
        self.assertEqual(response['objects'][1]['name'], 'MLK Day')

    def test_past_events(self):
        '''
        Only return events that occurred in the past
        Make sure they are ordered from most recent to
        furthest in the past
        '''
        # Assuming today is Christmas...
        organization = OrganizationFactory(name="International Cat Association")
        db.session.flush()

        # Create multiple events, one in the future, some in the past
        EventFactory(organization_name=organization.name, name="Thanksgiving", start_time_notz=datetime.now() - timedelta(30))
        EventFactory(organization_name=organization.name, name="Christmas Eve", start_time_notz=datetime.now() - timedelta(1))
        EventFactory(organization_name=organization.name, name="New Years", start_time_notz=datetime.now() + timedelta(7))
        db.session.flush()

        # Check that past events are returned in the correct order
        response = self.app.get('/api/organizations/International Cat Association/past_events')
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        self.assertEqual(response['total'], 2)
        self.assertEqual(response['objects'][0]['name'], 'Christmas Eve')
        self.assertEqual(response['objects'][1]['name'], 'Thanksgiving')

    def test_issues(self):
        '''
        Test that issues have everything we expect.
        Make sure linked issues are not included in the linked project
        '''
        organization = OrganizationFactory()
        db.session.add(organization)
        db.session.commit()
        project = ProjectFactory(organization_name=organization.name)
        db.session.add(project)
        db.session.commit()
        issue = IssueFactory(project_id=project.id)
        db.session.add(issue)
        db.session.commit()

        response = self.app.get('/api/issues', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)

        self.assertEqual(response['total'], 1)
        self.assertEqual(response['objects'][0]['title'], 'Civic Issue 1')
        self.assertEqual(response['objects'][0]['body'], 'Civic Issue blah blah blah 1')

        # Check for linked issues in linked project
        self.assertTrue('project' in response['objects'][0])
        self.assertFalse('issues' in response['objects'][0])

        #Check that project_id is hidden
        self.assertTrue('project_id' not in response['objects'][0])

        # Check for linked project issues on single issue
        response = self.app.get('/api/issues/1', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        self.assertTrue('project' in response)
        self.assertTrue('issues' not in response['project'])

    def test_single_organization_query_filter(self):
        '''
        Test that organization query params work as expected.
        '''
        brigade = OrganizationFactory(name="Brigade Organization", type="Brigade")
        meetup = OrganizationFactory(name="Meetup Organization", type="Meetup")

        db.session.add(meetup)
        db.session.add(brigade)
        db.session.commit()

        response = self.app.get('/api/organizations?type=Brigade', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        self.assertEqual(response['total'], 1)

        response = self.app.get('/api/organizations?type=SomeType', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        self.assertEqual(response['total'], 0)

    def test_single_organization_query_filter(self):
        '''
        Test that project query params work as expected.
        '''
        web_project = ProjectFactory(name="Random Web App", type="web service")
        non_web_project = ProjectFactory(name="Random Other App", type="other service")

        db.session.add(web_project)
        db.session.add(non_web_project)
        db.session.commit()

        response = self.app.get('/api/projects?type=web%20service', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        self.assertEqual(response['total'], 1)

        response = self.app.get('/api/projects?type=different%20service', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        response = json.loads(response.data)
        self.assertEqual(response['total'], 0)

if __name__ == '__main__':
    unittest.main()
