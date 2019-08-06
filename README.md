# OpenRefine Python Client with extended command line interface

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/33129bd15cdc4ece88c8012caab8d347)](https://www.codacy.com/app/felixlohmeier/openrefine-client?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=opencultureconsulting/openrefine-client&amp;utm_campaign=Badge_Grade)

The [OpenRefine Python Client Library from PaulMakepeace](https://github.com/PaulMakepeace/refine-client-py) provides an interface to communicating with an [OpenRefine](http://openrefine.org) server. This fork extends the command line interface (CLI) and supports communication between docker containers.

## Download

One-file-executables:

* Linux: [openrefine-client_0-3-4_linux-64bit](https://github.com/opencultureconsulting/openrefine-client/releases/download/v0.3.4/openrefine-client_0-3-4_linux-64bit) (4,7 MB)
* Windows: [openrefine-client_0-3-4_windows.exe](https://github.com/opencultureconsulting/openrefine-client/releases/download/v0.3.4/openrefine-client_0-3-4_windows.exe) (4,9 MB)
* Mac: [openrefine-client_0-3-4_mac](https://github.com/opencultureconsulting/openrefine-client/releases/download/v0.3.4/openrefine-client_0-3-4_mac) (4,4 MB)

For native Python installation on Windows, Mac or Linux see [Installation](#installation) below.

## Peek

A short video loop that demonstrates the basic features (list, create, apply, export)

![video loop that demonstrates basic features](openrefine-client-peek.gif)

## Usage

Command line interface:

- list all projects: `--list`
- create project from file: `--create [FILE]`
- apply [rules from json file](http://kb.refinepro.com/2012/06/google-refine-json-and-my-notepad-or.html): `--apply [FILE.json] [PROJECTID/PROJECTNAME]`
- export project to file: `--export [PROJECTID/PROJECTNAME] --output=FILE.tsv`
- templating export: `--export "My Address Book" --template='{ "friend" : {{jsonize(cells["friend"].value)}}, "address" : {{jsonize(cells["address"].value)}} }' --prefix='{ "address" : [' --rowSeparator=',' --suffix='] }' --filterQuery="^mary$"`
- show project metadata: `--info [PROJECTID/PROJECTNAME]`
- delete project: `--delete [PROJECTID/PROJECTNAME]`
- check `--help` for further options...

If you are familiar with python you may try all functions interactively (`python -i refine.py`) or use this library in your own python scripts. Some Examples:

* show version of OpenRefine server: `refine.RefineServer().get_version()`
* show total rows of project 2151545447855: `refine.RefineProject(refine.RefineServer(),'2151545447855').do_json('get-rows')['total']`
* compute clusters of project 2151545447855 and column key: `refine.RefineProject(refine.RefineServer(),'2151545447855').compute_clusters('key')`

## Configuration

By default the OpenRefine server URL is [http://127.0.0.1:3333](http://127.0.0.1:3333)

The environment variables `OPENREFINE_HOST` and `OPENREFINE_PORT` enable overriding the host & port as well as the command line options `-H` and `-P`.

## Installation

```
pip install openrefine-client
```

(requires Python 2.x, depends on urllib2_file>=0.2.1)

## Tests

Ensure you have a Refine server running somewhere and, if necessary, set the environment vars as above.

Run tests, build, and install:

```
python setup.py test # to do a subset, e.g., --test-suite tests.test_facet

python setup.py build

python setup.py install
```

There is a Makefile that will do this too, and more.

## Credits

[Paul Makepeace](http://paulm.com), author

David Huynh, [initial cut](<http://markmail.org/message/jsxzlcu3gn6drtb7)

[Artfinder](http://www.artfinder.com), inspiration

[Felix Lohmeier](https://felixlohmeier.de), extended the CLI features

Some data used in the test suite has been used from publicly available sources,

- louisiana-elected-officials.csv: from http://www.sos.louisiana.gov/tabid/136/Default.aspx

- us_economic_assistance.csv: ["The Green Book"](http://www.data.gov/raw/1554)

- eli-lilly.csv: [ProPublica's "Docs for Dollars](http://projects.propublica.org/docdollars) leading to a [Lilly Faculty PDF](http://www.lillyfacultyregistry.com/documents/EliLillyFacultyRegistryQ22010.pdf) processed by [David Huynh's ScraperWiki script](http://scraperwiki.com/scrapers/eli-lilly-dollars-for-docs-scraper/edit/)
