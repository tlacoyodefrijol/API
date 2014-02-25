# civic-json-worker

A [Flask](http://flask.pocoo.org) API generalizing [OpenCity Chicago's similar app](https://github.com/open-city/civic-json-worker) to track civic tech projects around the world. Project data is stored / output using the [civic.json](https://github.com/BetaNYC/civic.json) data standard. (Soon!)

A project by:

<a href="http://opencityapps.org"><img src="http://opengovhacknight.org/images/sponsors/open-city-sm.jpg" alt="Open City"></a>

<a href="http://betanyc.org"><img src="http://betanyc.us/images/apple70Gray.png" alt="Beta NYC"></a>

<a href="http://codeforamerica.com"><img src="http://codeforamerica.org/assets/logo.png" alt="Code for America"></a>


*For the story behind this API, [read this](https://hackpad.com/Civic.json-planning-meeting-EusFEMPgMio#:h=Chicago's-Open-Gov-Hack-Night-). For our design philosophy, [read this](https://hackpad.com/Civic.json-planning-meeting-EusFEMPgMio#:h=Civic-json-worker:-way-forward).*

## How It Works

Looking at [other civic tech listings](http://commons.codeforamerica.org/), projects like this that have [gone stale](http://digital.cityofchicago.org/index.php/open-data-applications/), the real sticking point seems to be keeping the list of projects - and their details - up to date.

The goal of this project is to minimize the work needed from civic hacking organizations to track their projects, and share project information with the world in a structured way.

Below is the current **draft** workflow: please [contribute your thoughts on this by adding an issue!](https://github.com/codeforamerica/civic-json-worker/issues)

### Organizations List

The current approach is for there to be "One True List" of participating civic hacking organizations (such as Code for America Brigades) stored in a Google Spreadsheet.

An organization will contribute their information by adding a row to the GSpreadsheet.

Each organization will be defined here by:

`name, url, events_url, rss, projects_list_url`

### Events List
Coming Soon!

### RSS
Coming Soon!

### Projects List

The `projects_list_url` provided by an organization in the above doc will point to a file with a list of projects the org is working on. A variety of common formats will be supported (Google Spreadsheet, JSON, CSV/TSV.)

Each project in `projects_list` will be defined by:

`name, description, live_url, code_url, type, categories`

#### Auto-Populating Data from GitHub URLs

If `code_url` points to a GitHub repository, and `name` and `description` are blank, these two fields will be auto-populated by hitting the GitHub API.


### Output Data

#### API

Code for America will maintain a restful API of all of the Brigades' (CfA's volunteer civic hacking groups) activities. This API is under heavy development, with current focus on the /projects endpoint. Current output is formatted like:

```Javascript
{
    num_results: 493,
    objects: [
        {
            categories: "community engagement, housing",
            code_url: "https://github.com/codeforamerica/cityvoice",
            description: "A redeployment of CityVoice in South Bend, Indiana.",
            github_details: "{...}",
            link_url: "http://www.southbendvoices.com/",
            name: "South Bend Voices",
            type: "service"
        },
        ...
    ],
    page: 1,
    total_pages: 1
}
```

This API is built with the [Flask-Restless](http://flask-restless.readthedocs.org/en/latest/) plugin. Refer to its documentation for specifics.

#### TODO: civic.json files

`civic-json-worker` will also output data in the civic.json standard (see below) to a [public JSON File on S3](https://s3-us-west-2.amazonaws.com/project-list/projects.json) with CORS enabled, allowing it to be loaded with only 
an Ajax call.

This way, it can be used for any project listing site ([for a good example, see Chicago's](http://opengovhacknight.org/projects.html).)


## Civic.json data standard
[Civic.json](https://github.com/BetaNYC/civic.json) is proposed meta-data standard for describing civic tech projects. The goal is for this standard to be simple, and for the data fields that describe projects to be largely assembled programatically.

The standard is still very much in planning phases, and we [welcome discussion](https://github.com/BetaNYC/civic.json/issues).

Once we settle on v1, `civic-json-worker` will output - and potentially store - project data in this format.

## Installation

Development is in very early stages, and specs are likely to change, so please contact Andrew and Eric in the "Contribute" section below to get involved.

Here's how to get set up for development:

There are some basic requirements which can be gotten 
in the standard Python fashion (assuming you are working in a [virtualenv](https://pypi.python.org/pypi/virtualenv)):

``` bash
$ pip install -r requirements.txt
```

### Create and prepare a database
For a new postgres db, run:

    createdb civicjsonworker

Run this Python command to create a fresh database schema:

    python -c 'from app import db; db.create_all()'

Besides that, there are a few environmental variables that you'll need to set:

* `DATABASE_URL=[db connection string]` — On Heroku with Postgres, this will be set for you. My local example is `postgres://hackyourcity@localhost/civicjsonworker` When testing locally, “sqlite:///data.db” is a great way to skip Postgres installation.
* `FLASK_KEY=[whatever you want]` — This is a string that you'll check to make sure that only trusted people are deleting things
* `GITHUB_TOKEN=[Github API token]` — Read about setting that up here: http://developer.github.com/v3/oauth/
* `S3_BUCKET=[Name of the bucket]` — This is the bucket where you'll store the JSON files
* `AWS_ACCESS_KEY_ID=[Amazon Web Services Key]` — Amazon access key for the bucket above, see also [boto config](https://code.google.com/p/boto/wiki/BotoConfig).
* `AWS_SECRET_ACCESS_KEY=[Amazon Web Services Secret]` — Amazon secret key for the bucket above, see also [boto config](https://code.google.com/p/boto/wiki/BotoConfig).

Probably easiest placed in the .bashrc (or the like) of 
the user that the app is running as rather than manually set but you get the idea...


## Running the updater

The ``run_update.py`` script will be run on Heroku once an hour and populate the database. To run locally, try:

``` bash 
$ python run_update.py
```


## Contribute

Get in touch with Andrew Hyder ([ondrae])(http://github.com/ondrae) ([andrewh@codeforamerica.org](andrewh@codeforamerica.org)) from Code for America or Eric Van Zanten ([eric.vanzanten@gmail.com](eric.vanzanten@gmail.com)) from Open City.

The issue tracker is actively watched and pull requests are welcome!
