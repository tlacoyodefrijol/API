# civic-json-worker

[Flask](http://flask.pocoo.org) API for tracking civic tech projects across the world. Project data is stored / output using the [civic.json](https://github.com/BetaNYC/civic.json) data standard. (Soon!)

A project by:

<br>

<div style="float: left"><a href="http://opencityapps.org"><img src="http://opengovhacknight.org/images/sponsors/open-city-sm.jpg" alt="Open City"></a></div>

<div style="float: left"><a href="http://betanyc.org"><img src="http://betanyc.us/images/apple70Gray.png" alt="Beta NYC"></a></div>

<div style="float: left"><a href="http://codeforamerica.com"><img src="http://codeforamerica.org/assets/logo.png" alt="Code for America"></a></div>

<br><br><br><br>
*For the story behind this API, [read this](https://hackpad.com/Civic.json-planning-meeting-EusFEMPgMio#:h=Chicago's-Open-Gov-Hack-Night-). For our design philosophy, [read this](https://hackpad.com/Civic.json-planning-meeting-EusFEMPgMio#:h=Civic-json-worker:-way-forward).*

## How It Works

Looking at [other civic tech listing projects](http://commons.codeforamerica.org/) like this that have [gone stale](http://digital.cityofchicago.org/index.php/open-data-applications/), the real sticking point is keeping the list of projects - and their details - up to date. The less work people have to do, the more the archive will stay up to date and useful.

The goal of this project is to make humans responsible for one thing: __deciding what gets tracked__. They submit github repo urls to this API, which curates a simple projects list:

```json
[
    "https://github.com/dssg/census-communities-usa",
    "https://github.com/open-city/open-gov-hack-night",
    ...
]
```

The rest is up to computers. When the ``/update-projects/`` endpoint is hit on API, it loops over the project urls in the list, and pings the Github API to gather the following fields for each project:

``` json
[
    {
        "contributors": [
            {
                "avatar_url": "https://0.gravatar.com/avatar/5e5eb188a0e4d3a7c8f38ee0fc3a6cbd?d=https%3A%2F%2Fidenticons.github.com%2Fd8c3ef3ed05a213a7225bf5e6e46101a.png", 
                "contributions": 51, 
                "html_url": "https://github.com/derekeder", 
                "login": "derekeder"
            }, 
            {
                "avatar_url": "https://2.gravatar.com/avatar/813d23c289052af417387a9270d0da31?d=https%3A%2F%2Fidenticons.github.com%2Ffa9357bb22fd993fc9795619c7e1d4f7.png", 
                "contributions": 46, 
                "html_url": "https://github.com/fgregg", 
                "login": "fgregg"
            }, 
            {
                "avatar_url": "https://2.gravatar.com/avatar/1d0c5faee140af87d7d6967bc946ecc6?d=https%3A%2F%2Fidenticons.github.com%2F44e80db9ed8527f429c969e804432b0f.png", 
                "contributions": 9, 
                "html_url": "https://github.com/evz", 
                "login": "evz"
            }
        ], 
        "contributors_url": "https://api.github.com/repos/datamade/csvdedupe/contributors", 
        "created_at": "2013-07-11T14:23:33Z", 
        "description": "Command line tool for deduplicating CSV files", 
        "forks_count": 2, 
        "homepage": null, 
        "html_url": "https://github.com/datamade/csvdedupe", 
        "id": 11343900, 
        "language": "Python", 
        "name": "csvdedupe", 
        "open_issues": 8, 
        "owner": {
            "avatar_url": "https://2.gravatar.com/avatar/0a89207d38feff1dcd938bdc1e4a9b5e?d=https%3A%2F%2Fidenticons.github.com%2F3424042f8cb2b04950903794ad9c8daf.png", 
            "html_url": "https://github.com/datamade", 
            "login": "datamade"
        }, 
        "updated_at": "2013-09-20T06:32:39Z", 
        "watchers_count": 26
    },
    ...
]
```

**NOTE**: these fields will eventually reflect the proposed [civic.json](https://github.com/BetaNYC/civic.json) standard (see below.)

This data is hosted on a publicly available endpoint as JSON with a CORS configuration that allows it to be loaded via 
an Ajax call, for use on [any projects list site](http://opengovhacknight.org/projects.html).

__bonus:__ anyone can use [this JSON
file](http://worker.opengovhacknight.org/data/project_details.json) for their
own purposes. Details on setting up a CORS configuration for nginx can be found
[here](https://github.com/open-city/civic-json-worker/issues/16#issuecomment-28759993)

## Civic.json data standard
[Civic.json](https://github.com/BetaNYC/civic.json) is proposed meta-data standard for describing civic tech projects. The goal is for this standard to be simple, and for the data fields that describe projects to be largely assembled programatically.

The standard is still very much in planning phases, and we [welcome discussion](https://github.com/BetaNYC/civic.json/issues). Once we settle on v1, civic-json-worker will outputs - and potentially store - project data in this format.


## Benefits

By pushing everything on to Github, we will have very little to maintain, content-wise, as administrators. Simultaneously, we will encourage people to:

* sign up for Github if they aren't already
* keep their projects open source (we can't crawl private repos)
* make sure their description and website urls are up to date
* use the issue tracker

## Installation

**NOTE**: *If you're a Code for America Brigade interested in setting up your own civic-json-worker API, hold it! Our goal is to make life easy for you: you shouldn't have to adapt, deploy, or maintain your own API, just read and write data from a single source. (This way, all the data is centralized, too!)*

If you want to help out with development, or you don't want to play nice with the other kids in the schoolyard, read on...

Propping this sucker up for oneself is pretty simple. However, there are some basic requirements which can be gotten 
in the standard Python fashion (assuming you are working in a [virtualenv](https://pypi.python.org/pypi/virtualenv)):

``` bash
$ pip install -r requirements.txt
```

Besides that, there are a few environmental variables that you'll need to set:

``` bash
$ export FLASK_KEY=[whatever you want] # This is a string that you'll check to make sure that only trusted people are deleting things
$ export GITHUB_TOKEN=[Github API token] # Read about setting that up here: http://developer.github.com/v3/oauth/
$ export S3_BUCKET=[Name of the bucket] # This is the bucket where you'll store the JSON files 
$ export AWS_ACCESS_KEY=[Amazon Web Services Key] # This will need access to the bucket above
$ export AWS_SECRET_KEY=[Amazon Web Services Secret] # This will need access to the bucket above
```

Probably easiest placed in the .bashrc (or the like) of 
the user that the app is running as rather than manually set but you get the idea...

## Contribute

Get in touch with Andrew Hyder ([andrewh@codeforamerica.org](andrewh@codeforamerica.org)) from Code for America or Eric Van Zanten ([eric.vanzanten@gmail.com](eric.vanzanten@gmail.com)) from Open City.

The issue tracker is actively watched and pull requests are welcome!
