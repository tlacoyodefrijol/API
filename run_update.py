import json
from tasks import update_project, get_people_totals, get_org_totals

def update_projects():
    f = open('data/projects.json', 'rb')
    project_list = json.loads(f.read())
    f.close()
    details = []
    for project_url in project_list:
        try:
            pj_details = update_project(project_url)
        except IOError:
            return 'Github is throttling. Just gonna try again after limit is reset.'
        if pj_details:
            details.append(pj_details)
    f = open('data/project_details.json', 'wb')
    f.write(json.dumps(details, indent=4))
    f.close()
    f = open('data/people.json', 'wb')
    f.write(json.dumps(get_people_totals(details), indent=4))
    f.close()
    orgs = [d for d in details if d['owner']['type'] == 'Organization']
    f = open('data/organizations.json', 'wb')
    f.write(json.dumps(get_org_totals(orgs), indent=4))
    f.close()
    return 'Updated'

if __name__ == "__main__":
    update_projects()
