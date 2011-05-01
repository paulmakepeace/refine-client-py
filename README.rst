===================================
Google Refine Python Client Library
===================================

The Google Refine Python Client Library provides an interface to
communicating with a Google Refine server.

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

Configuration
=============

By default the Google Refine server URL is http://127.0.0.1:3333
The environment variables ``GOOGLE_REFINE_HOST`` and ``GOOGLE_REFINE_PORT``
enable overriding the host & port.

In order to run all tests, a live Refine server is needed. No existing projects
are affected.

Installation
============

(Someone with more familiarity with python's byzantine collection of installation
frameworks is very welcome to improve/"best practice" all this.)

#. Install dependencies, which currently is ``urllib2_file``:

   ``sudo pip install -r requirements.txt``

#. Ensure you have a Refine server running somewhere and, if necessary, set
   the envvars as above.

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

- reconciliation
- undo/redo
- Freebase
- join columns
- columns from URL

Credits
=======

Paul Makepeace, author, <paulm@paulm.com>

David Huynh, `initial cut <http://groups.google.com/group/google-refine/msg/ee29cf8d660e66a9>`_

`Artfinder <http://www.artfinder.com/>`_, inspiration

Some data used in the test suite has been used from publicly available sources,

 - louisiana-elected-officials.csv: from
   http://www.sos.louisiana.gov/tabid/136/Default.aspx

 - us_economic_assistance.csv: `"The Green Book" <http://www.data.gov/raw/1554>`_

 - eli-lilly.csv: `ProPublica's "Docs for Dollars" <http://projects.propublica.org/docdollars/>`_ leading to a `Lilly Faculty PDF <http://www.lillyfacultyregistry.com/documents/EliLillyFacultyRegistryQ22010.pdf>`_ processed by `David Huynh's ScraperWiki script <http://scraperwiki.com/scrapers/eli-lilly-dollars-for-docs-scraper/edit/>`_

