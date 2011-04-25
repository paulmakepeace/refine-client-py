#!/usr/bin/env python
"""
Client library to communicate with a Refine server.
"""

import csv
import json
import gzip
import os
import re
import StringIO
import urllib
import urllib2_file
import urllib2
import urlparse


REFINE_HOST = os.environ.get('GOOGLE_REFINE_HOST', '127.0.0.1')
REFINE_PORT = os.environ.get('GOOGLE_REFINE_PORT', '3333')


def to_camel(attr):
    """convert this_attr_name to thisAttrName."""
    # Do lower case first letter
    return (attr[0].lower() +
            re.sub(r'_(.)', lambda x: x.group(1).upper(), attr[1:]))

def from_camel(attr):
    """convert thisAttrName to this_attr_name."""
    # Don't add an underscore for capitalized first letter
    return re.sub(r'(?<=.)([A-Z])', lambda x: '_' + x.group(1), attr).lower()


class Facet(object):
    def __init__(self, column, type, expression='value',
                 **options):
        self.type = type
        self.column_name = column
        self.name = column  # XXX not sure what the difference is yet
        self.expression = expression
        for k, v in options.items():
            setattr(self, k, v)

    def as_dict(self):
        return dict([(to_camel(k), v) for k, v in self.__dict__.items()
                     if v is not None])


class TextFacet(Facet):
    def __init__(self, column, selection=None, omit_blank=False, omit_error=False, select_blank=False, select_error=False, invert=False, **options):
        super(TextFacet, self).__init__(
            column,
            type='list',
            omit_blank=omit_blank,
            omit_error=omit_error,
            select_blank=select_blank,
            select_error=select_error,
            invert=invert,
            **options)
        self.selection = []
        if selection is None:
            selection = []
        elif not isinstance(selection, list):
            selection = [selection]
        for value in selection:
            self.include(value)

    def include(self, value):
        for s in self.selection:
            if s['v']['v'] == value:
                return
        self.selection.append({'v': {'v': value, 'l': value}})

    def exclude(self, value):
        self.selection = [s for s in self.selection
                          if s['v']['v'] != value]

    def reset(self):
        self.selection = []


class StarredFacet(TextFacet):
    def __init__(self, selection=None):
        if selection is not None and not isinstance(selection, bool):
            raise ValueError('selection must be True or False.')
        super(StarredFacet, self).__init__('',
            expression='row.starred', selection=selection)


class FlaggedFacet(TextFacet):
    def __init__(self, selection=None):
        if selection is not None and not isinstance(selection, bool):
            raise ValueError('selection must be True or False.')
        super(FlaggedFacet, self).__init__('',
            expression='row.flagged', selection=selection)


# Capitalize 'From' to get around python's reserved word.
class NumericFacet(Facet):
    def __init__(self, column, From=None, to=None, select_blank=True, select_error=True, select_non_numeric=True, select_numeric=True, **options):
        super(NumericFacet, self).__init__(
            column,
            type='range',
            select_blank=select_blank,
            select_error=select_error,
            select_non_numeric=select_non_numeric,
            select_numeric=select_numeric,
            From=From,
            to=to,
            **options)


class FacetResponse(object):
    def __init__(self, facet):
        for k, v in facet.items():
            if isinstance(k, bool) or isinstance(k, basestring):
                setattr(self, from_camel(k), v)
        self.choices = {}
        class FacetChoice(object):
            def __init__(self, c):
                self.count = c['c']
                self.selected = c['s']

        if 'choices' in facet:
            for choice in facet['choices']:
                self.choices[choice['v']['v']] = FacetChoice(choice)
            if 'blankChoice' in facet:
                self.blank_choice = FacetChoice(facet['blankChoice'])
            else:
                self.blank_choice = None
        if 'bins' in facet:
            self.bins = facet['bins']
            self.base_bins = facet['baseBins']


class FacetsResponse(object):
    def __init__(self, facets):
        self.facets = [FacetResponse(f) for f in facets['facets']]
        self.mode = facets['mode']


class Engine(object):
    def __init__(self, facets=None, mode='row-based'):
        if facets is None:
            facets = []
        elif not isinstance(facets, list):
            facets = [facets]
        self.facets = facets
        self.mode = mode

    def as_dict(self):
        return {
            'facets': [f.as_dict() for f in self.facets],   # XXX how with json?
            'mode': self.mode,
        }

    def __len__(self):
        return len(self.facets)

    def as_json(self):
        return json.dumps(self.as_dict())

    def add_facet(self, facet):
        self.facets.append(facet)

    def remove_all(self):
        self.facets = []

    def reset_all(self):
        for facet in self.facets:
            facet.reset()


class Sorting(object):
    """Class representing the current sorting order for a project.

    Used in RefineProject.get_rows()"""
    def __init__(self, criteria=None):
        self.criteria = []
        if criteria is None:
            criteria = []
        if not isinstance(criteria, list):
            criteria = [criteria]
        for criterion in criteria:
            if isinstance(criterion, basestring):
                criterion = {
                    'column': criterion,
                    'valueType': 'string',
                    'caseSensitive': False,
                }
                criterion.setdefault('reverse', False)
                criterion.setdefault('errorPosition', 1)
                criterion.setdefault('blankPosition', 2)
            self.criteria.append(criterion)

    def as_json(self):
        return json.dumps({'criteria': self.criteria})

    def __len__(self):
        return len(self.criteria)


class RefineServer(object):
    """Communicate with a Refine server."""

    def __init__(self, server='http://%s:%s' % (REFINE_HOST, REFINE_PORT)):
        self.server = server[:-1] if server.endswith('/') else server

    def urlopen(self, command, data=None, project_id=None):
        """Open a Refine URL and optionally POST data."""
        url = self.server + '/command/core/' + command
        if data is None:
            data = {}
        if project_id:
            # XXX haven't figured out pattern on qs v body
            if 'delete' in command:
                data['project'] = project_id
            else:
                url += '?project=' + project_id
        req = urllib2.Request(url)
        if data:
            req.add_data(data) # data = urllib.urlencode(data)
        #req.add_header('Accept-Encoding', 'gzip')
        response = urllib2.urlopen(req)
        if response.info().get('Content-Encoding', None) == 'gzip':
            # Need a seekable filestream for gzip
            gzip_fp = gzip.GzipFile(fileobj=StringIO.StringIO(response.read()))
            # XXX Monkey patch response's filehandle. Better way?
            urllib.addbase.__init__(response, gzip_fp)
        return response

    def urlopen_json(self, *args, **kwargs):
        """Open a Refine URL, optionally POST data, and return parsed JSON."""
        response = json.loads(self.urlopen(*args, **kwargs).read())
        if 'code' in response and response['code'] != 'ok':
            raise Exception(
                response['code'] + ': ' +
                response.get('message', response.get('stack', response)))
        return response


class Refine:
    """Class representing a connection to a Refine server."""
    def __init__(self, server, **kwargs):
        if isinstance(server, RefineServer):
            self.server = server
        else:
            self.server = RefineServer(server)

    def get_version(self):
        """Return version data.

        {"revision":"r1836","full_version":"2.0 [r1836]",
         "full_name":"Google Refine 2.0 [r1836]","version":"2.0"}"""
        return self.server.urlopen_json('get-version')

    def list_projects(self):
        """Return a dict of projects indexed by id & name.

        {u'1877818633188': {
            'id': u'1877818633188', u'name': u'akg',
            u'modified': u'2011-04-07T12:30:07Z',
            u'created': u'2011-04-07T12:30:07Z'
        },
        {u'akg': { ... } } ...}"""
        projects = self.server.urlopen_json('get-all-project-metadata')['projects']
        # Provide a way for projects to be indexed by name too
        for project_id, metadata in projects.items():
            metadata['id'] = project_id
            projects[metadata['name']] = metadata
        return projects

    def get_project_id_name(self, project):
        """Returns (project_id, project_name) given either."""
        projects = self.list_projects()
        # Is the project param an integer? If so treat as an id, else a name.
        if re.match(r'^\d+$', project):
            return project, projects[project]['name']
        else:
            return projects[project]['id'], project

    def open_project(self, project):
        """Open a Refine project referred to by id or name."""
        project_id, project_name = self.get_project_id_name(project)
        return RefineProject(self.server, project_id, project_name)

    def new_project(self, project_file=None, project_url=None, project_name=None,
        split_into_columns=True,
        separator='',
        ignore_initial_non_blank_lines=0,
        header_lines=1, # use 0 if your data has no header
        skip_initial_data_rows=0,
        limit=None, # no more than this number of rows
        guess_value_type=True,  # numbers, dates, etc.
        ignore_quotes=False):

        if (project_file and project_url) or (not project_file and not project_url):
            raise ValueError('One (only) of project_file and project_url must be set')
        def s(opt):
            if isinstance(opt, bool):
                return 'on' if opt else ''
            if opt is None:
                return ''
            return str(opt)
        options = {
            'split-into-columns': s(split_into_columns),
            'separator': s(separator),
            'ignore': s(ignore_initial_non_blank_lines),
            'header-lines': s(header_lines),
            'skip': s(skip_initial_data_rows), 'limit': s(limit),
            'guess-value-type': s(guess_value_type),
            'ignore-quotes': s(ignore_quotes),
        }
        if project_url is not None:
            options['url'] = project_url
        elif project_file is not None:
            options['project-file'] = {
                'fd': open(project_file),
                'filename': project_file,
            }
        if project_name is None:
            # strip extension and directories
            project_name = (project_file or 'New project').rsplit('.', 1)[0]
            project_name = os.path.basename(project_name)
        options['project-name'] = project_name
        response = self.server.urlopen('create-project-from-upload', options)
        # expecting a redirect to the new project containing the id in the url
        url_params = urlparse.parse_qs(urlparse.urlparse(response.geturl()).query)
        if 'project' in url_params:
            project_id = url_params['project'][0]
            return RefineProject(self.server, project_id, project_name)
        else:
            raise Exception('Project not created')


class RowsResponse(object):
    class RefineRows(object):
        class RefineRow(object):
            def __init__(self, row_response):
                self.flagged = row_response['flagged']
                self.starred = row_response['starred']
                self.index = row_response['i']
                self.row = [c['v'] if c else None for c in row_response['cells']]

        def __init__(self, rows_response):
            self.rows_response = rows_response
        def __iter__(self):
            for row_response in self.rows_response:
                yield self.RefineRow(row_response)
        def __len__(self):
            return len(self.rows_response)

    def __init__(self, response):
        self.mode = response['mode']
        self.filtered = response['filtered']
        self.start = response['start']
        self.limit = response['limit']
        self.total = response['total']
        self.pool = response['pool']    # {"reconCandidates": {},"recons": {}}
        self.rows = self.RefineRows(response['rows'])


class RefineProject:
    """A Google Refine project."""

    def __init__(self, server, project_id=None, project_name=None):
        if not isinstance(server, RefineServer):
            url = urlparse.urlparse(server)
            if url.query:
                # Parse out the project ID and create a base server URL
                project_id = url.query[8:]  # skip project=
                server = urlparse.urlunparse((url.scheme, url.netloc, '', '', '', ''))
            server = RefineServer(server)
        self.server = server
        if not project_id and not project_name:
            raise Exception('Missing Refine project ID and name; need at least one of those')
        if not project_name or not project_id:
            project_id, project_name = Refine(server).get_project_id_name(
                project_name or project_id)
        self.project_id = project_id
        self.project_name = project_name
        self.columns = []   # columns & column_index filled in by get_models()
        self.column_index = {}
        self.get_models()
        self.engine = Engine()
        self.sorting = Sorting()

    def do_raw(self, command, data):
        """Issue a command to the server & return a response object."""
        return self.server.urlopen(command, self.project_id, data)

    def do_json(self, command, data=None, include_engine=True):
        """Issue a command to the server, parse & return decoded JSON."""
        if include_engine:
            if data is None:
                data = {}
            data['engine'] = self.engine.as_json()
        return self.server.urlopen_json(command, project_id=self.project_id,
                                        data=data)

    def get_models(self):
        """Fill out column metadata."""
        response = self.do_json('get-models', include_engine=False)
        column_model = response['columnModel']
        columns = column_model['columns']
        # Pre-extend the list in python
        self.columns = [None] * (1 + max(c['cellIndex'] for c in columns))
        for column in columns:
            cell_index, name = column['cellIndex'], column['name']
            self.column_index[name] = cell_index
            self.columns[cell_index] = name
        self.key_column = column_model['keyColumnName']
        # TODO: implement rest

    def wait_until_idle(self, polling_delay=0.5):
        while True:
            response_json = self.do('get-processes')
            if 'processes' in response_json and len(response_json['processes']) > 0:
                time.sleep(polling_delay)
            else:
                return

    def apply_operations(self, file_path, wait=True):
        json = open(file_path).read()
        response_json = self.do('apply-operations', {'operations': json})
        if response_json['code'] == 'pending' and wait:
            self.wait_until_idle()
            return 'ok'
        return response_json['code'] # can be 'ok' or 'pending'

    def export(self, export_format='tsv'):
        """Return a fileobject of a project's data."""
        url = ('export-rows/' + urllib.quote(self.project_name) + '.' +
               export_format)
        return self.do_raw(url, {'format': export_format})

    def export_rows(self, **kwargs):
        """Return an iterable of parsed rows of a project's data."""
        return csv.reader(self.export(**kwargs), dialect='excel-tab')

    def delete(self):
        response_json = self.do_json('delete-project', include_engine=False)
        return 'code' in response_json and response_json['code'] == 'ok'

    def compute_facets(self, facets=None):
        if facets:
            self.engine = Engine(facets)
        response = self.do_json('compute-facets')
        return FacetsResponse(response)

    def get_rows(self, facets=None, sort_by=None, start=0, limit=10):
        if facets:
            self.engine = Engine(facets)
        if sort_by is not None:
            self.sorting = Sorting(sort_by)
        response = self.do_json('get-rows', {'sorting': self.sorting.as_json(),
                                             'start': start, 'limit': limit})
        return RowsResponse(response)

    def reorder_rows(self, sort_by=None):
        if sort_by is not None:
            self.sorting = Sorting(sort_by)
        response = self.do_json('reorder-rows',
                                {'sorting': self.sorting.as_json()})
        return response

    def remove_rows(self, facets=None):
        if facets:
            self.engine = Engine(facets)
        return self.do_json('remove-rows')

    def text_transform(self, column, expression, on_error='set-to-blank',
                       repeat=False, repeat_count=10):
        response = self.do_json('text-transform', {
            'columnName': column, 'expression': expression,
            'onError': on_error, 'repeat': repeat,
            'repeatCount': repeat_count})
        return response

    def edit(self, column, edit_from, edit_to):
        edits = [{'from': [edit_from], 'to': edit_to}]
        return self.mass_edit(column, edits)

    def mass_edit(self, column, edits, expression='value'):
        """edits is [{'from': ['foo'], 'to': 'bar'}, {...}]"""
        edits = json.dumps(edits)
        response = self.do_json('mass-edit', {
            'columnName': column, 'expression': expression, 'edits': edits})
        return response

    clusterer_defaults = {
        'binning': {
            'type': 'binning',
            'function': 'fingerprint',
            'params': {},
        },
        'knn': {
            'type': 'knn',
            'function': 'levenshtein',
            'params': {
                'radius': 1,
                'blocking-ngram-size': 6,
            },
        },
    }
    def compute_clusters(self, column, clusterer_type='binning',
                         function=None, params=None):
        """Returns a list of clusters of {'value': ..., 'count': ...}."""
        clusterer = self.clusterer_defaults[clusterer_type]
        if params is not None:
            clusterer['params'] = params
        if function is not None:
            clusterer['function'] = function
        clusterer['column'] = column
        response = self.do_json('compute-clusters', {
            'clusterer': json.dumps(clusterer)})
        return [[{'value': x['v'], 'count': x['c']} for x in cluster]
                for cluster in response]

    def annotate_one_row(self, row, annotation, state=True):
        if annotation not in ('starred', 'flagged'):
            raise ValueError('annotation must be one of starred or flagged')
        state = 'true' if state == True else 'false'
        return self.do_json('annotate-one-row', {'row': row.index,
                                                 annotation: state})

    def flag_row(self, row, flagged=True):
        return self.annotate_one_row(row, 'flagged', flagged)

    def star_row(self, row, starred=True):
        return self.annotate_one_row(row, 'starred', starred)

