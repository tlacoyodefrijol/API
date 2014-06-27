# The Code for America API

### What the CFAPI is
Code for America has developed this API to track all the activity across the civic technology movement. Our goal is to measure and motivate the movement by recognizing participation. The CFAPI describes an organization's projects, stories, and events. 

The tools that the Brigades and other groups use to do their fine deeds are all different. The CFAPI does the difficult job of being able to track these activities no matter what tools an organization is using. The participants don't need to change their activities to be included.

### Projects powered by the CFAPI
The Code for America Brigade website
<img src="http://i.imgur.com/C96yBLE.png" width="500px">

### Example Response
See the full documentation at http://codeforamerica.org/api

```
{
	all_events: "http://codeforamerica.org/api/organizations/Code_for_San_Francisco/events",
	all_projects: "http://codeforamerica.org/api/organizations/Code_for_San_Francisco/projects",
	all_stories: "http://codeforamerica.org/api/organizations/Code_for_San_Francisco/stories",
	api_url: "http://codeforamerica.org/api/organizations/Code_for_San_Francisco",
	city: "San Francisco, CA",
	current_events: [
		{
			api_url: "http://codeforamerica.org/api/events/2010",
			created_at: "2014-02-26 21:05:21",
			description: "<p>Join Code for San Francisco for our weekly hack night focused on open government and civic tech in San Francisco. </p> ...",
			end_time: null,
			event_url: "http://www.meetup.com/Code-for-San-Francisco-Civic-Hack-Night/events/174976312/",
			id: 2010,
			location: null,
			name: "Weekly Civic Hack Night",
			organization_name: "Code for San Francisco",
			start_time: "2014-04-09 18:30:00 -0700"
		},
	    ...
	],
	current_projects: [
		{
			api_url: "http://codeforamerica.org/api/projects/216",
			categories: null,
			code_url: "https://github.com/sfbrigade/open_ballot",
			description: "An educational tool around ballot measures",
			github_details: {},
			id: 216,
			link_url: null,
			name: "open_ballot",
			organization_name: "Code for San Francisco",
			type: null
		},
		...
	],
	current_stories: [
		{
			api_url: "http://codeforamerica.org/api/stories/4",
			id: 4,
			link: "https://groups.google.com/d/msg/code-for-san-francisco/sqkerXsrntY/yMhnsPhN6LwJ",
			organization_name: "Code for San Francisco",
			title: "Ethical Hacking with Guru99",
			type: "blog"
		},
		...
	],
	events_url: "http://www.meetup.com/Code-for-San-Francisco-Civic-Hack-Night/",
	last_updated: 1396969394,
	latitude: 37.7749,
	longitude: -122.4194,
	name: "Code for San Francisco",
	past_events: "http://codeforamerica.org/api/organizations/Code_for_San_Francisco/past_events",
	projects_list_url: "https://github.com/sfbrigade",
	rss: "https://groups.google.com/forum/feed/code-for-san-francisco/msgs/rss.xml?num=15",
	type: "Brigade",
	upcoming_events: "http://codeforamerica.org/api/organizations/Code_for_San_Francisco/upcoming_events",
	website: "http://codeforsanfrancisco.org/"
}
```

### History
The need for a way to show off good civic tech projects was apparent. Several Brigades had all started working on ways to track their projects. They were working separately on the same idea at the same time. The CFAPI is a generalization of the great work done by:

<a href="http://opencityapps.org"><img src="http://opengovhacknight.org/images/sponsors/open-city-sm.jpg" alt="Open City"> Open City </a>

<a href="http://betanyc.org"><img src="http://betanyc.us/images/apple70Gray.png" alt="Beta NYC"> Beta NYC </a>

<a href="http://www.meetup.com/Code-for-Boston/"><img src="http://i.imgur.com/HlsvNQY.png" alt="Code for Boston"> Code for Boston </a>

*For the full story behind this API, [read this](https://hackpad.com/Civic.json-planning-meeting-EusFEMPgMio#:h=Chicago's-Open-Gov-Hack-Night-).

This repository is forked from [Open City's Civic Json Worker](https://github.com/open-city/civic-json-worker)

### How to add your Brigade to the API

##### Brigade Information
The new site will be powered by this [Brigade Information](https://docs.google.com/spreadsheet/ccc?key=0ArHmv-6U1drqdGNCLWV5Q0d5YmllUzE5WGlUY3hhT2c&usp=sharing) Google Spreadsheet. This way you don't need yet another account for our Brigade site. Just keep your Brigade's info up to date and you're good. The columns are:
* Name
* Website
* Events Url - Point us to where ever you schedule your events. Only Meetup.com events are working right now.
* RSS - If you have a blog, point us to it. It's pretty smart and can find the feed on its own. To show off your Google Group discussions, use a link like `https://groups.google.com/forum/feed/code-for-san-francisco/msgs/rss.xml?num=15`
* Projects List Url - Can either be a GitHub organization url like `https://github.com/sfbrigade` or a link to a list of project urls, described below.


##### Projects List
This projects list you point us to will need the following columns:
* name - filled in by GitHub if left blank
* description - filled in by GitHub if left blank
* link_url - filled in by GitHub if left blank
* code_url - Only GitHub links work for now. Others will be added as needed later.
* type - Is this project an app, an open data policy, a webservice?
* categories - Write your own separated by commas. "Education, digital literacy"

An example:
```
name, description, link_url, code_url, type, categories
South Bend Voices, "A redeploy of CityVoice for South Bend, IN.", http://www.southbendvoices.com/, https://github.com/codeforamerica/cityvoice, web service, "community engagement, housing"
```

That projects list URL can be any flavor of csv. The easiest way is to make a Google Spreadsheet like [my example](https://docs.google.com/spreadsheet/ccc?key=0ArHmv-6U1drqdDBzNXpSZkVzRDJUQnpOS0RJM0FDWGc&usp=sharing) and then ```File > Publish it to the web```. Grab the published link and change ```?output=html to ?output=csv```. Put that in the Brigade Information sheet and you're done.

The projects list URL can also be a JSON file, with a list of strings containing Github project URLs.

Lastly, the projects list URL can be a Github organization URL, like http://github.com/codeforamerica.

### Civic.json data standard
The `/projects` endpoint is structure is influenced by [Civic.json](https://github.com/BetaNYC/civic.json), a proposed meta-data standard for describing civic tech projects. The goal is for this standard to be simple, and for the data fields that describe projects to be largely assembled programatically.

The standard is still very much in planning phases, and we [welcome discussion](https://github.com/BetaNYC/civic.json/issues).

### Installation

The CFAPI is built on [Flask](http://flask.pocoo.org/) and Python. The `app.py` file describes the models and routes. The `run_update.py` file runs once an hour and collects all the data about the different Brigades. Both `tests.py` and `run_update_test.py` are automatically run by [Travis-CI](https://travis-ci.org/codeforamerica/cfapi) whenever a new commit is made. The production service lives on Heroku. Please contact Andrew and Eric in the "Contribute" section below to get involved.

* Prerequirements - Set your environmental variables.

* `DATABASE_URL=[db connection string]` — On Heroku with Postgres, this will be set for you. My local example is `postgres://hackyourcity@localhost/cfapi` When testing locally, “sqlite:///data.db” is a great way to skip Postgres installation.
* `GITHUB_TOKEN=[Github API token]` — Read about setting that up here: http://developer.github.com/v3/oauth/
* `MEETUP_KEY=[Meetup API Key]` — Read about setting that up here: https://secure.meetup.com/meetup_api/key/

Set these environment variables in your `.bash_profile`. Then run `source ~/.bash_profile`.

Here's how to get set up for development:

* Set up a [virtualenv](https://pypi.python.org/pypi/virtualenv)

```
pip install virtualenv
virtualenv venv-cfapi
source venv-cfapi/bin/activate
```

* Install the required libraries 

```
$ pip install -r requirements.txt
```

* Set up a new database

```
createdb cfapi
python -c 'from app import db; db.create_all()'
```

* Run the updater

The `run_update.py` script will be run on Heroku once an hour and populate the database. To run locally, try:

``` 
python run_update.py
```
There is a line near the top of run_update.py that sets the `gdocs_url` variable. Change it to the testing one for a faster testing run through.

* Start the API

```
python app.py
```

* Visit http://localhost:5000/api/organizations/Code_for_America to see your results.


### Tests
`python run_update_test.py` to test the run_update process.
`python tests.py` to test the API.



Contacts
--------

* Andrew Hyder ([ondrae](https://github.com/ondrae))
* Erica Kwan ([pui](https://github.com/pui))
* Michal Migurski ([migurski](https://github.com/migurski))


Contributing
------------

Here are some ways *you* can contribute:

* by reporting bugs
* by suggesting new features
* by translating to a new language
* by writing or editing documentation
* by writing code (**no patch is too small**: fix typos, add comments, clean up
  inconsistent whitespace)
* by refactoring code
* by closing [issues][]
* by reviewing patches
* [financially][]

[issues]: https://github.com/codeforamerica/brigade-alpha/issues
[financially]: https://secure.codeforamerica.org/page/contribute


Submitting an Issue
-------------------

We use the [GitHub issue tracker][issues] to track bugs and features. Before
submitting a bug report or feature request, check to make sure it hasn't
already been submitted. You can indicate support for an existing issue by
voting it up. When submitting a bug report, please include a [Gist][] that
includes a stack trace and any details that may be necessary to reproduce the
bug.

[gist]: https://gist.github.com/

Submitting a Pull Request
-------------------------

1. Fork the project.
2. Create a topic branch.
3. Implement your feature or bug fix.
4. Commit and push your changes.
5. Submit a pull request.


Copyright
---------

Copyright (c) 2014 Code for America.
