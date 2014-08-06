\c cfapi;

alter table story 
  drop constraint story_organization_name_fkey;

alter table story 
  add constraint story_organization_name_fkey 
  foreign key (organization_name) references organization(name) on delete cascade;

alter table project
  drop constraint project_organization_name_fkey ;

alter table project 
  add constraint project_organization_name_fkey 
  foreign key (organization_name) references organization(name) on delete cascade;

alter table event 
  drop constraint event_organization_name_fkey; 

alter table event 
  add constraint event_organization_name_fkey 
  foreign key (organization_name) references organization(name) on delete cascade;

alter table issue
  drop constraint issue_project_id_fkey ;

alter table issue 
  add constraint issue_project_id_fkey 
  foreign key (project_id) references project(id) on delete cascade;

alter table label
  drop constraint label_issue_id_fkey ;

alter table label
  add constraint label_issue_id_fkey 
  foreign key (issue_id) references issue(id) on delete cascade;

