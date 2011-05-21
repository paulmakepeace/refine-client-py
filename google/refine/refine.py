#!/usr/bin/env python
"""
Client library to communicate with a Refine server.
"""

# Copyright (c) 2011 Paul Makepeace, Real Programmers. All rights reserved.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
    
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

from google.refine import facet
from google.refine import history

REFINE_HOST = os.environ.get('GOOGLE_REFINE_HOST', '127.0.0.1')
REFINE_PORT = os.environ.get('GOOGLE_REFINE_PORT', '3333')


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
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError as (url_error,):
            raise urllib2.URLError(
                '%s for %s. No Refine server reachable/running; ENV set?' %
                (url_error, self.server))
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
        """Return a dict of projects indexed by id.

        {u'1877818633188': {
            'id': u'1877818633188', u'name': u'akg',
            u'modified': u'2011-04-07T12:30:07Z',
            u'created': u'2011-04-07T12:30:07Z'
        },
        """
        # It's tempting to add in an index by name but there can be
        # projects with the same name.
        return self.server.urlopen_json('get-all-project-metadata')['projects']

    def get_project_name(self, project_id):
        """Returns project name given project_id."""
        projects = self.list_projects()
        return projects[project_id]['name']

    def open_project(self, project_id):
        """Open a Refine project."""
        return RefineProject(self.server, project_id)

    def new_project(self, project_file=None, project_url=None,
        project_name=None,
        split_into_columns=True,
        separator='',
        ignore_initial_non_blank_lines=0,
        header_lines=1, # use 0 if your data has no header
        skip_initial_data_rows=0,
        limit=None, # no more than this number of rows
        guess_value_type=True,  # numbers, dates, etc.
        ignore_quotes=False):

        if ((project_file and project_url) or
            (not project_file and not project_url)):
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
            # make a name for itself by stripping extension and directories
            project_name = (project_file or 'New project').rsplit('.', 1)[0]
            project_name = os.path.basename(project_name)
        options['project-name'] = project_name
        response = self.server.urlopen('create-project-from-upload', options)
        # expecting a redirect to the new project containing the id in the url
        url_params = urlparse.parse_qs(
            urlparse.urlparse(response.geturl()).query)
        if 'project' in url_params:
            project_id = url_params['project'][0]
            return RefineProject(self.server, project_id)
        else:
            raise Exception('Project not created')


def RowsResponseFactory(column_index):
    """Factory for the parsing the output from get_rows().

    Uses the project's model's row cell index so that a row can be used
    as a dict by column name."""

    class RowsResponse(object):
        class RefineRows(object):
            class RefineRow(object):
                def __init__(self, row_response):
                    self.flagged = row_response['flagged']
                    self.starred = row_response['starred']
                    self.index = row_response['i']
                    self.row = [c['v'] if c else None
                                for c in row_response['cells']]
                def __getitem__(self, column):
                    # Trailing nulls seem to be stripped from row data
                    try:
                        return self.row[column_index[column]]
                    except IndexError:
                        return None

            def __init__(self, rows_response):
                self.rows_response = rows_response
            def __iter__(self):
                for row_response in self.rows_response:
                    yield self.RefineRow(row_response)
            def __getitem__(self, index):
                return self.RefineRow(self.rows_response[index])
            def __len__(self):
                return len(self.rows_response)

        def __init__(self, response):
            self.mode = response['mode']
            self.filtered = response['filtered']
            self.start = response['start']
            self.limit = response['limit']
            self.total = response['total']
            # 'pool': {"reconCandidates": {},"recons": {}}
            self.pool = response['pool']
            self.rows = self.RefineRows(response['rows'])

    return RowsResponse


class RefineProject:
    """A Google Refine project."""

    def __init__(self, server, project_id=None):
        if not isinstance(server, RefineServer):
            if '/project?project=' in server:
                server, project_id = server.split('/project?project=')
            server = RefineServer(server)
        self.server = server
        if not project_id:
            raise Exception('Missing Refine project ID')
        self.project_id = project_id
        self.engine = facet.Engine()
        self.sorting = facet.Sorting()
        self.history_entry = None
        # following filled in by get_models()
        self.has_records = False
        self.columns = None
        self.column_order = {}  # map of column names to order in UI
        self.rows_response_factory = None   # for parsing get_rows()
        self.get_models()

    def project_name(self):
        return Refine(self.server).get_project_name(self.project_id)

    def project_url(self):
        """Return a URL to the project."""
        return '%s/project?project=%s' % (self.server.server, self.project_id)

    def do_raw(self, command, data):
        """Issue a command to the server & return a response object."""
        return self.server.urlopen(command, data, self.project_id)

    def do_json(self, command, data=None, include_engine=True):
        """Issue a command to the server, parse & return decoded JSON."""
        if include_engine:
            if data is None:
                data = {}
            data['engine'] = self.engine.as_json()
        response = self.server.urlopen_json(command,
                                            project_id=self.project_id,
                                            data=data)
        if 'historyEntry' in response:
            # **response['historyEntry'] won't work as keys are unicode :-/
            he = response['historyEntry']
            self.history_entry = history.HistoryEntry(he['id'], he['time'],
                                                      he['description'])
        return response

    def get_models(self):
        """Fill out column metadata.

        column structure is sent in a list of columns in their order.
        The cellIndex is used to find that column's data when returned from
        get_rows()."""
        response = self.do_json('get-models', include_engine=False)
        column_model = response['columnModel']
        column_index = {}
        self.columns = [column['name'] for column in column_model['columns']]
        for i, column in enumerate(column_model['columns']):
            name = column['name']
            self.column_order[name] = i
            column_index[name] = column['cellIndex']
        self.key_column = column_model['keyColumnName']
        self.has_records = response['recordModel'].get('hasRecords', False)
        self.rows_response_factory = RowsResponseFactory(column_index)
        # TODO: implement rest
        return response

    def wait_until_idle(self, polling_delay=0.5):
        while True:
            response = self.do_json('get-processes')
            if 'processes' in response and len(response['processes']) > 0:
                time.sleep(polling_delay)
            else:
                return

    def apply_operations(self, file_path, wait=True):
        json = open(file_path).read()
        response_json = self.do_json('apply-operations', {'operations': json})
        if response_json['code'] == 'pending' and wait:
            self.wait_until_idle()
            return 'ok'
        return response_json['code'] # can be 'ok' or 'pending'

    def export(self, export_format='tsv'):
        """Return a fileobject of a project's data."""
        url = ('export-rows/' + urllib.quote(self.project_name()) + '.' +
               export_format)
        return self.do_raw(url, {'format': export_format})

    def export_rows(self, **kwargs):
        """Return an iterable of parsed rows of a project's data."""
        return csv.reader(self.export(**kwargs), dialect='excel-tab')

    def delete(self):
        response_json = self.do_json('delete-project', include_engine=False)
        return 'code' in response_json and response_json['code'] == 'ok'

    def compute_facets(self, facets=None):
        """Compute facets as per the project's engine.

        The response object has two attributes, mode & facets. mode is one of
        'row-based' or 'record-based'. facets is a magic list of facets in the
        same order as they were specified in the Engine. Magic allows the
        original Engine's facet as index into the response, e.g.,

        name_facet = TextFacet('name')
        response = project.compute_facets(name_facet)
        response.facets[name_facet]     # same as response.facets[0]
        """
        if facets:
            self.engine.set_facets(facets)
        response = self.do_json('compute-facets')
        return self.engine.facets_response(response)

    def get_rows(self, facets=None, sort_by=None, start=0, limit=10):
        if facets:
            self.engine.set_facets(facets)
        if sort_by is not None:
            self.sorting = facet.Sorting(sort_by)
        response = self.do_json('get-rows', {'sorting': self.sorting.as_json(),
                                             'start': start, 'limit': limit})
        return self.rows_response_factory(response)

    def reorder_rows(self, sort_by=None):
        if sort_by is not None:
            self.sorting = facet.Sorting(sort_by)
        response = self.do_json('reorder-rows',
                                {'sorting': self.sorting.as_json()})
        # clear sorting
        self.sorting = facet.Sorting()
        return response

    def remove_rows(self, facets=None):
        if facets:
            self.engine.set_facets(facets)
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

    def add_column(self, column, new_column, expression='value',
                   column_insert_index=None, on_error='set-to-blank'):
        if column_insert_index is None:
            column_insert_index = self.column_order[column] + 1
        response = self.do_json('add-column', {'baseColumnName': column,
            'newColumnName': new_column, 'expression': expression,
            'columnInsertIndex': column_insert_index, 'onError': on_error})
        self.get_models()
        return response

    def split_column(self, column, separator=',', mode='separator',
                     regex=False, guess_cell_type=True,
                     remove_original_column=True):
        response = self.do_json('split-column', {'columnName': column,
            'separator': separator, 'mode': mode, 'regex': regex,
            'guessCellType': guess_cell_type,
            'removeOriginalColumn': remove_original_column})
        self.get_models()
        return response

    def rename_column(self, column, new_column):
        response = self.do_json('rename-column', {'oldColumnName': column,
                                                  'newColumnName': new_column})
        self.get_models()
        return response

    def reorder_columns(self, new_column_order):
        """Takes an array of column names in the new order."""
        response = self.do_json('reorder-columns', {
            'columnNames': new_column_order})
        self.get_models()
        return response

    def move_column(self, column, index):
        """Move column to a new position."""
        if index == 'end':
            index = len(self.columns) - 1
        response = self.do_json('move-column', {'columnName': column,
                                                'index': index})
        self.get_models()
        return response

    def blank_down(self, column):
        response = self.do_json('blank-down', {'columnName': column})
        self.get_models()
        return response

    def fill_down(self, column):
        response = self.do_json('fill-down', {'columnName': column})
        self.get_models()
        return response

    def transpose_columns_into_rows(self, start_column, column_count,
        combined_column_name, separator=':', prepend_column_name=True,
        ignore_blank_cells=True):
        response = self.do_json('transpose-columns-into-rows', {
            'startColumnName': start_column, 'columnCount': column_count,
            'combinedColumnName': combined_column_name,
            'prependColumnName': prepend_column_name,
            'separator': separator, 'ignoreBlankCells': ignore_blank_cells})
        self.get_models()
        return response

    def transpose_rows_into_columns(self, column, row_count):
        response = self.do_json('transpose-rows-into-columns', {
            'columnName': column, 'rowCount': row_count})
        self.get_models()
        return response

