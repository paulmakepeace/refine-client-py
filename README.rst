===================================
OpenRefine Python Client Library
===================================

The OpenRefine Python Client Library provides an interface to
communicating with an `OpenRefine <http://openrefine.org/>`_ server.

Download
========

One-file-executables:

* Linux: `openrefine-client_0-3-4_linux-64bit <https://github.com/opencultureconsulting/openrefine-client/releases/download/v0.3.4/openrefine-client_0-3-4_linux-64bit>`_ (4,9 MB)
* Windows: `openrefine-client_0-3-4_windows.exe <https://github.com/opencultureconsulting/openrefine-client/releases/download/v0.3.4/openrefine-client_0-3-4_windows.exe>`_ (5,1 MB)

For native Python installation on Windows, Mac or Linux see `Installation <#installation>`_ below.

Usage
=====

Command line interface:

- list all projects: ``python refine.py --list``
- create project from file: ``python refine.py --create [FILE]``
- apply `rules from json file <http://kb.refinepro.com/2012/06/google-refine-json-and-my-notepad-or.html>`_: ``python refine.py --apply [FILE.json] [PROJECTID/PROJECTNAME]``
- export project to file: ``python refine.py --export [PROJECTID/PROJECTNAME] --output=FILE.tsv``
- templating export: ``python refine.py --export "My Address Book" --template='{ "friend" : {{jsonize(cells["friend"].value)}}, "address" : {{jsonize(cells["address"].value)}} }' --prefix='{ "address" : [' --rowSeparator ',' --suffix '] }' --filterQuery="^mary$"``
- show project metadata: ``python refine.py --info [PROJECTID/PROJECTNAME]``
- delete project: ``python refine.py --delete [PROJECTID/PROJECTNAME]``
- check ``python refine.py --help`` for further options...

If you are familiar with python you may try all functions interactively (``python -i refine.py``) or use this library in your own python scripts. Some Examples:

* show version of OpenRefine server: ``refine.RefineServer().get_version()``
* show total rows of project 2151545447855: ``refine.RefineProject(refine.RefineServer(),'2151545447855').do_json('get-rows')['total']``
* compute clusters of project 2151545447855 and column key: ``refine.RefineProject(refine.RefineServer(),'2151545447855').compute_clusters('key')``

Features
=============

Currently, the following API is supported:

- project creation/import, deletion, export
- facet computation

  - text
  - text filter
  - numeric
  - blank
  - starred & flagged
  - ... extensible class

- 'engine': managing multiple facets and their computation results
- sorting & reordering
- clustering
- transforms
- transposes
- single and mass edits
- annotation (star/flag)
- column

  - move
  - add
  - split
  - rename
  - reorder
  - remove

- reconciliation

  - reconciliation judgment facet
  - guessing column type
  - querying reconciliation services preferences
  - perform reconciliation

Configuration
=============

By default the OpenRefine server URL is http://127.0.0.1:3333
The environment variables ``OPENREFINE_HOST`` and ``OPENREFINE_PORT``
enable overriding the host & port.

In order to run all tests, a live Refine server is needed. No existing projects
are affected.

Installation
============

(Someone with more familiarity with python's byzantine collection of installation
frameworks is very welcome to improve/"best practice" all this.)

#. Install dependencies, which currently is ``urllib2_file``:

   ``sudo pip install -r requirements.txt``

   (If you don't have ``pip`` visit `pip-installer.org <http://www.pip-installer.org/en/latest/installing.html#install-or-upgrade-pip>`_)

#. Ensure you have a Refine server running somewhere and, if necessary, set
   the environment vars as above.

#. Run tests, build, and install:

   ``python setup.py test # to do a subset, e.g., --test-suite tests.test_facet``

   ``python setup.py build``

   ``python setup.py install``

There is a Makefile that will do this too, and more.

TODO
====

The API so far has been filled out from building a test suite to carry out the
actions in `David Huynh's Refine tutorial <http://davidhuynh.net/spaces/nicar2011/tutorial.pdf>`_ which while certainly showing off a
wide range of Refine features doesn't cover the entire suite. Notable exceptions
currently include:

- reconciliation support is useful but not complete
- undo/redo
- Freebase
- join columns
- columns from URL

Contribute
============

Pull requests with passing tests welcome! Source is at https://github.com/PaulMakepeace/refine-client-py

Useful Tools
------------

One aspect of development is watching HTTP transactions. To that end, I found
`Fiddler <http://www.fiddler2.com/>`_ on Windows and `HTTPScoop
<http://www.tuffcode.com/>`_ invaluable. The latter won't URL-decode nor nicely
format JSON but the `Online JavaScript Beautifier <http://jsbeautifier.org/>`_
will.

Executables may be built with `pyinstaller <http://www.pyinstaller.org>`_.

History
=======

OpenRefine used to be called Google Refine, and this library used to be called
the Google Refine Python Client Library.

Credits
=======

Paul Makepeace, author, <paulm@paulm.com>

David Huynh, `initial cut <http://markmail.org/message/jsxzlcu3gn6drtb7>`_

`Artfinder <http://www.artfinder.com/>`_, inspiration

Some data used in the test suite has been used from publicly available sources,

- louisiana-elected-officials.csv: from
  http://www.sos.louisiana.gov/tabid/136/Default.aspx

- us_economic_assistance.csv: `"The Green Book" <http://www.data.gov/raw/1554>`_

- eli-lilly.csv: `ProPublica's "Docs for Dollars" <http://projects.propublica.org/docdollars/>`_ leading to a `Lilly Faculty PDF <http://www.lillyfacultyregistry.com/documents/EliLillyFacultyRegistryQ22010.pdf>`_ processed by `David Huynh's ScraperWiki script <http://scraperwiki.com/scrapers/eli-lilly-dollars-for-docs-scraper/edit/>`_

