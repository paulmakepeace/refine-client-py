===================================
OpenRefine Python Client Library
===================================

The OpenRefine Python Client Library provides an interface to
communicating with an `OpenRefine <http://openrefine.org/>`_ server.

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

