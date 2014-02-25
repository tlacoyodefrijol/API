from boto.s3.connection import S3Connection
from boto.s3.key import Key

BUCKET = os.environ['S3_BUCKET']

def upload_json_file(json_data, object_name):
    ''' Upload a named file to S3 BUCKET, return nothing.
    '''
    s3 = S3Connection()
    bucket = s3.get_bucket(BUCKET)

    object = Key(bucket)
    object.key = object_name
    
    data = dumps(json_data, indent=2)
    args = dict(policy='public-read', headers={'Content-Type': 'application/json'})

    object.set_contents_from_string(data, **args)


def transform_for_chicago(all_projects):
    chicago_style_projects = []
    for project in all_projects:
        project = project['github']
        chicago_style_projects.append(project)
    return chicago_style_projects

def count_people_totals(all_projects):
    ''' Create a list of people details based on project details.
    
        Request additional data from Github API for each person.
    '''
    users, contributors = [], []
    for project in all_projects:
        contributors.extend(project['contributors'])
    
    #
    # Sort by login; there will be duplicates!
    #
    contributors.sort(key=itemgetter('login'))
    
    #
    # Populate users array with groups of contributors.
    #
    for (_, _contributors) in groupby(contributors, key=itemgetter('login')):
        user = dict(contributions=0, repositories=0)
        
        for contributor in _contributors:
            user['contributions'] += contributor['contributions']
            user['repositories'] += 1
            
            if 'login' in user:
                continue

            #
            # Populate user hash with Github info, if it hasn't been already.
            #
            got = get_github_api(contributor['url'])
            contributor = got.json()
            
            for field in (
                    'login', 'avatar_url', 'html_url',
                    'blog', 'company', 'location'
                    ):
                user[field] = contributor.get(field, None)
        
        users.append(user)
    
    return users
all_projects.append(project)

    chicago_style_projects = transform_for_chicago(all_projects)
    upload_json_file(chicago_style_projects, 'project_details.json')
    people = count_people_totals(chicago_style_projects)
    upload_json_file(people, 'people.json')




    # def reformat_project_info(input):
#     ''' Return a clone of the project hash, formatted for use by opengovhacknight.org.
    
#         The representation here is specifically expected to be used on this page:
#         http://opengovhacknight.org/projects.html
#     '''
#     output = dict()
    
#     for field in ('name', 'description'):
#         output[field] = input[field]
    
#     if 'github' in input:
#         try:
#             info = collect_github_project_info(input)
#         except:
#             pass
#         else:
#             output.update(info)
    
#     return output

# def collect_github_project_info(input):
#     ''' Collect Github project info, formatted for use by opengovhacknight.org.
    
#         The representation here is specifically expected to be used on this page:
#         http://opengovhacknight.org/projects.html
#     '''
#     output = dict()
#     github = input['github']

#     #
#     # Populate core Github fields.
#     #
#     for field in (
#             'contributors_url', 'created_at', 'forks_count', 'homepage',
#             'html_url', 'id', 'language', 'open_issues', 'pushed_at',
#             'updated_at', 'watchers_count'
#             ):
#         output[field] = github[field]

#     output['owner'] = dict()

#     for field in ('avatar_url', 'html_url', 'login', 'type'):
#         output['owner'][field] = github['owner'][field]
    
#     #
#     # Populate project contributors from github[contributors_url]
#     #
#     output['contributors'] = []
#     got = get_github_api(github['contributors_url'])
    
#     for contributor in got.json():
#         # we don't want people without email addresses?
#         if contributor['login'] == 'invalid-email-address':
#             break
    
#         output['contributors'].append(dict())
        
#         for field in ('login', 'url', 'avatar_url', 'html_url', 'contributions'):
#             output['contributors'][-1][field] = contributor[field]
        
#         # flag the owner with a boolean value
#         output['contributors'][-1]['owner'] \
#             = bool(contributor['login'] == output['owner']['login'])
    
#     #
#     # Populate project participation from github[url] + "/stats/participation"
#     #
#     got = get_github_api(github['url'] + '/stats/participation')
#     output['participation'] = got.json()['all']
    
#     #
#     # Populate project needs from github[issues_url] (remove "{/number}")
#     #
#     output['project_needs'] = []
#     url = github['issues_url'].replace('{/number}', '')
#     got = get(url, auth=github_auth, params=dict(labels='project-needs'))
    
#     for issue in got.json():
#         project_need = dict(title=issue['title'], issue_url=issue['html_url'])
#         output['project_needs'].append(project_need)
    
#     return output