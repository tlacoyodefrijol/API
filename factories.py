import factory
from app import Organization, Project, db
from factory.alchemy import SQLAlchemyModelFactory
from sqlalchemy.orm import scoped_session, sessionmaker
from random import choice

class OrganizationFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Organization
    FACTORY_SESSION = db.session

    name = factory.Sequence(lambda n: 'Civic Organization {0}'.format(n))
    website = factory.Sequence(lambda n: 'http://www.civicorganization{0}.com'.format(n))
    events_url = factory.Sequence(lambda n: 'http://www.civicorganization{0}.com/events'.format(n))
    rss = factory.Sequence(lambda n: 'http://www.civicorganization{0}.rss'.format(n))
    projects_list_url = factory.Sequence(lambda n: 'http://www.civicorganization{0}.com/projects'.format(n))

class ProjectFactory(SQLAlchemyModelFactory):
    FACTORY_FOR = Project
    FACTORY_SESSION = db.session

    name = 'Civic Project'
    code_url = 'http://www.github.com/civic-project'
    link_url = 'http://www.civicproject.com'
    description = 'This is a description'
    type = factory.LazyAttribute(lambda n: choice(['web service', 'api', 'data standard']))
    categories = factory.LazyAttribute(lambda n: choice(['housing', 'community engagement', 'criminal justice', 'education']))
    github_details = 'something goes here'