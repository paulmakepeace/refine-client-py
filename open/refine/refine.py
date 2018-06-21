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
import os
import re
import time
import urllib.request
import urllib.parse
import urllib.error
import urllib.response
import requests

from open.refine import facet
from open.refine import history

REFINE_HOST = os.environ.get('OPENREFINE_HOST', os.environ.get('GOOGLE_REFINE_HOST', '127.0.0.1'))
REFINE_PORT = os.environ.get('OPENREFINE_PORT', os.environ.get('GOOGLE_REFINE_PORT', '3333'))


class RefineServer(object):
    """Communicate with a Refine server."""

    @staticmethod
    def server_url():
        """Return the URL to the Refine server."""
        server = 'http://' + REFINE_HOST
        if REFINE_PORT != '80':
            server += ':' + REFINE_PORT
        return server

    def __init__(self, server=None):
        if server is None:
            server = self.server_url()
        self.server = server[:-1] if server.endswith('/') else server
        self.__version = None     # see version @property below

    def urlopen(self, command, data=None, params=None, project_id=None, files=None):
        """Open a Refine URL and with optional query params and POST data.

        data: POST data dict
        param: query params dict
        project_id: project ID as string

        Returns requests.Response object."""
        # TODO: command to direct post or get request
        url = self.server + f'/command/core/{command}'
        if project_id:
            if 'delete' in command or data:
                data['project'] = project_id
            else:
                params['project'] = project_id
        response = requests.post(url, data=data, params=params, files=files)
        if response.status_code is not 200:
            response = requests.get(url, data=data, params=params, files=files)
        return response

    def urlopen_json(self, command, *args, **kwargs):
        """Open a Refine URL, optionally POST data, and return parsed JSON."""
        response = self.urlopen(command, *args, **kwargs)
        response = response.json()
        self.check_response_ok(response)
        return response

    @staticmethod
    def check_response_ok(response):
        if 'code' in response and response['code'] not in ('ok', 'pending'):
            error_message = ('server ' + response['code'] + ': ' +
                             response.get('message', response.get('stack', response)))
            raise Exception(error_message)

    def get_version(self):
        """Return version data.
        {"revision":"r1836","full_version":"2.0 [r1836]",
         "full_name":"Google Refine 2.0 [r1836]","version":"2.0"}"""
        return self.urlopen_json('get-version')

    @property
    def version(self):
        if self.__version is None:
            self.__version = self.get_version()['version']
        return self.__version


class Refine:
    """Class representing a connection to a Refine server."""
    def __init__(self, server):
        if isinstance(server, RefineServer):
            self.server = server
        else:
            self.server = RefineServer(server)

    def new_project(self, project_file=None, project_url=None, project_name=None, project_format='text/line-based/*sv',
                    project_file_name=None, **opts):
        if (project_file and project_url) or (not project_file and not project_url):
            raise ValueError('Either a project_file or project_url must be set. Both cannot be used.')
        params = {
            'project_name': self.set_project_name(project_name, project_file)
        }
        data = {
            'format': project_format,
            'options': self.set_options(project_format, **opts)
        }
        files = {
            'project-file': (project_file_name, open(project_file, 'rb'))
        }
        response = self.server.urlopen('create-project-from-upload', params=params, data=data, files=files)
        response.raise_for_status()
        project_id = self.get_project_id(response.url)
        files['project-file'][1].close()
        return RefineProject(self.server, project_id)

    @staticmethod
    def set_project_name(project_name, project_file):
        # expecting a redirect to the new project containing the id in the server_url
        if project_name is None:
            # make a name for itself by stripping extension and directories
            project_name = (project_file or 'New project').rsplit('.', 1)[0]
            project_name = os.path.basename(project_name)
        return project_name

    def set_options(self, file_format, **kwargs):
        options = self.default_options(file_format)
        for key, value in kwargs.items():
            options[key] = value
        return options

    def get_project_name(self, project_id):
        """Returns project name given project_id."""
        projects = self.list_projects()
        return projects[project_id]['name']

    def open_project(self, project_id):
        """Open a Refine project."""
        return RefineProject(self.server, project_id)

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

    @staticmethod
    def get_project_id(url):
        url_params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        if 'project' in url_params:
            project_id = url_params['project'][0]
            return project_id
        else:
            raise Exception('Project not created')

    @staticmethod
    def default_options(file_format):
        new_project_defaults = {
            'text/line-based/*sv': {
                'encoding': '',
                'separator': ',',
                'ignore_lines': -1,
                'header_lines': 1,
                'skip_data_lines': 0,
                'limit': -1,
                'store_blank_rows': True,
                'guess_cell_value_types': True,
                'process_quotes': True,
                'store_blank_cells_as_nulls': True,
                'include_file_sources': False},
            'text/line-based': {
                'encoding': '',
                'lines_per_row': 1,
                'ignore_lines': -1,
                'limit': -1,
                'skip_data_lines': -1,
                'store_blank_rows': True,
                'store_blank_cells_as_nulls': True,
                'include_file_sources': False},
            'text/line-based/fixed-width': {
                'encoding': '',
                'column_widths': [20],
                'ignore_lines': -1,
                'header_lines': 0,
                'skip_data_lines': 0,
                'limit': -1,
                'guess_cell_value_types': False,
                'store_blank_rows': True,
                'store_blank_cells_as_nulls': True,
                'include_file_sources': False},
            'text/line-based/pc-axis': {
                'encoding': '',
                'limit': -1,
                'skip_data_lines': -1,
                'include_file_sources': False},
            'text/rdf+n3': {'encoding': ''},
            'text/xml/ods': {
                'sheets': [],
                'ignore_lines': -1,
                'header_lines': 1,
                'skip_data_lines': 0,
                'limit': -1,
                'store_blank_rows': True,
                'store_blank_cells_as_nulls': True,
                'include_file_sources': False},
            'binary/xls': {
                'xml_based': False,
                'sheets': [],
                'ignore_lines': -1,
                'header_lines': 1,
                'skip_data_lines': 0,
                'limit': -1,
                'store_blank_rows': True,
                'store_blank_cells_as_nulls': True,
                'include_file_sources': False}
        }
        if file_format in new_project_defaults.keys():
            return new_project_defaults[file_format]
        else:
            raise InvalidFileFormat


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
            self.rows = self.RefineRows(response['rows'])

    return RowsResponse


class RefineProject:
    """An OpenRefine project."""
    def __init__(self, server, project_id=None):
        if not isinstance(server, RefineServer):
            if '/project?project=' in server:
                server, project_id = server.split('/project?project=')
                server = RefineServer(server)
            elif re.match(r'\d+$', server):     # just digits => project ID
                server, project_id = RefineServer(), server
            else:
                server = RefineServer(server)
        self.server = server
        if not project_id:
            raise Exception('Missing Refine project ID')
        self.project_id = project_id
        self.engine = facet.Engine()
        self.sorting = facet.Sorting()
        self.history_entry = None
        # following filled in by get_models()
        self.key_column = None
        self.has_records = False
        self.columns = None
        self.column_order = {}  # map of column names to order in UI
        self.rows_response_factory = None   # for parsing get_rows()
        self.get_models()
        # following filled in by get_reconciliation_services
        self.recon_services = None

    def do_json(self, command, data=None, params=None, include_engine=True):
        """Issue a command to the server, parse & return decoded JSON."""
        if params is None:
            params = {}
        params['project'] = self.project_id
        if include_engine:
            if data is None:
                data = {}
            data['engine'] = self.engine.as_json()
        if command == 'delete-project':
            response = self.server.urlopen(command, params=params)
            response = response.json()
        else:
            response = self.server.urlopen_json(command, params=params, data=data)
        if 'historyEntry' in response:
            # **response['historyEntry'] won't work as keys are unicode :-/
            he = response['historyEntry']
            self.history_entry = history.HistoryEntry(he['id'], he['time'],
                                                      he['description'])
        return response

    def project_name(self):
        return Refine(self.server).get_project_name(self.project_id)

    def project_url(self):
        """Return a URL to the project."""
        return '%s/project?project=%s' % (self.server.server, self.project_id)

    def do_raw(self, command, data):
        """Issue a command to the server & return a response object."""
        return self.server.urlopen(command, project_id=self.project_id, data=data)

    def get_models(self):
        """
        Fill out column metadata.

        Column structure is a list of columns in their order.
        The cellIndex is an index for that column's data into the list returned
        from get_rows().

        {"columnModel":{"columns":[],"columnGroups":[]},"recordModel":{"hasRecords":false},"overlayModels":{},
        "scripting":{"grel":{"name":"General Refine Expression Language (GREL)","defaultExpression":"value"},
        "jython":{"name":"Python / Jython","defaultExpression":"return value"},"clojure":{"name":"Clojure",
        "defaultExpression":"value"}}}
        """
        response = self.do_json('get-models', include_engine=False)
        column_model = response['columnModel']
        column_index = {}   # map of column name to index into get_rows() data
        self.columns = [column['name'] for column in column_model['columns']]
        for i, column in enumerate(column_model['columns']):
            name = column['name']
            self.column_order[name] = i
            column_index[name] = column['cellIndex']
        self.key_column = column_model.get('keyColumnName')
        self.has_records = response['recordModel'].get('hasRecords', False)
        self.rows_response_factory = RowsResponseFactory(column_index)
        return response

    def get_preference(self, name):
        """Returns the (JSON) value of a given preference setting."""
        response = self.server.urlopen_json('get-preference', params={'name': name})
        return json.loads(response['value'])

    def wait_until_idle(self, polling_delay=0.5):
        while True:
            response = self.do_json('get-processes', include_engine=False)
            if 'processes' in response and len(response['processes']) > 0:
                time.sleep(polling_delay)
            else:
                return

    def apply_operations(self, operations=None, file_path=None, wait=True):
        json_data = self.json_data(operations, file_path)
        response_json = self.do_json('apply-operations', data={'operations': json_data})

        if response_json['code'] == 'pending' and wait:
            self.wait_until_idle()
            return 'ok'
        return response_json['code']  # can be 'ok' or 'pending'

    @staticmethod
    def json_data(operations, file_path):
        if operations:
            if type(operations) is not list:
                operations = [operations]
            return json.dumps(operations)
        elif file_path:
            return open(file_path).read()
        else:
            raise ValueError("Operation(s) not specified.")

    def export(self, export_format='tsv'):
        """Return a fileobject of a project's data."""
        url = ('export-rows/' + urllib.parse.quote(self.project_name()) + '.' + export_format)
        response = self.do_raw(url, data={'format': export_format})
        return response.text

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
        if sort_by is None:
            self.sorting = facet.Sorting([])
        elif sort_by is not None:
            self.sorting = facet.Sorting(sort_by)
        response = self.do_json('get-rows',
                                params={'start': start, 'limit': limit}, data={'sorting': self.sorting.as_json()})
        return self.rows_response_factory(response)

    def reorder_rows(self, sort_by=None):
        if sort_by is not None:
            self.sorting = facet.Sorting(sort_by)
        response = self.do_json('reorder-rows', params={'sorting': self.sorting.as_json()})
        # clear sorting
        # self.sorting = facet.Sorting()
        return response

    def remove_rows(self, facets=None):
        if facets:
            self.engine.set_facets(facets)
        return self.do_json('remove-rows')

    def text_transform(self, column, expression, on_error='set-to-blank', repeat=False, repeat_count=10):
        response = self.do_json('text-transform', params={
            'columnName': column,
            'expression': expression,
            'onError': on_error,
            'repeat': repeat,
            'repeatCount': repeat_count
        })
        return response

    def edit(self, column, edit_from, edit_to):
        edits = [{'from': [edit_from], 'to': edit_to}]
        return self.mass_edit(column, edits)

    def mass_edit(self, column, edits, expression='value'):
        """edits is [{'from': ['foo'], 'to': 'bar'}, {...}]"""
        edits = json.dumps(edits)
        response = self.do_json('mass-edit', params={'columnName': column, 'expression': expression, 'edits': edits})
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

    def compute_clusters(self, column, clusterer_type='binning', refine_function=None, params=None):
        """Returns a list of clusters of {'value': ..., 'count': ...}."""
        clusterer = self.clusterer_defaults[clusterer_type]
        if params is not None:
            clusterer['params'] = params
        if refine_function is not None:
            clusterer['function'] = refine_function

        clusterer['column'] = column
        response = self.do_json('compute-clusters', data={'clusterer': str(clusterer)})
        return [[{'value': x['v'], 'count': x['c']} for x in cluster]
                for cluster in response]

    def annotate_one_row(self, row, annotation, state=True):
        if annotation not in ('starred', 'flagged'):
            raise ValueError('annotation must be one of starred or flagged')
        state = 'true' if state is True else 'false'
        return self.do_json('annotate-one-row', params={'row': row.index, annotation: state})

    def flag_row(self, row, flagged=True):
        return self.annotate_one_row(row, 'flagged', flagged)

    def star_row(self, row, starred=True):
        return self.annotate_one_row(row, 'starred', starred)

    def add_column(self, column, new_column, expression='value', column_insert_index=None, on_error='set-to-blank'):
        if column_insert_index is None:
            column_insert_index = self.column_order[column] + 1
        response = self.do_json(
            'add-column',
            params={
                'baseColumnName': column,
                'newColumnName': new_column,
                'expression': expression,
                'columnInsertIndex': column_insert_index,
                'onError': on_error
            }
        )
        self.get_models()
        return response

    def split_column(
            self, column, separator=',', mode='separator', regex=False, guess_cell_type=True,
            remove_original_column=True):
        response = self.do_json(
            'split-column',
            params={
                'columnName': column,
                'separator': separator,
                'mode': mode,
                'regex': regex,
                'guessCellType': guess_cell_type,
                'removeOriginalColumn': remove_original_column
            })
        self.get_models()
        return response

    def rename_column(self, column, new_column):
        response = self.do_json('rename-column', params={'oldColumnName': column, 'newColumnName': new_column})
        self.get_models()
        return response

    def reorder_columns(self, new_column_order):
        """Takes an array of column names in the new order."""
        if new_column_order is not str:
            new_column_order = str(new_column_order)
        response = self.do_json('reorder-columns', data={'columnNames': new_column_order})
        self.get_models()
        return response

    def move_column(self, column, index):
        """Move column to a new position."""
        if index == 'end':
            index = len(self.columns) - 1
        response = self.do_json('move-column', params={'columnName': column, 'index': index})
        self.get_models()
        return response

    def blank_down(self, column):
        response = self.do_json('blank-down', params={'columnName': column})
        self.get_models()
        return response

    def fill_down(self, column):
        response = self.do_json('fill-down', params={'columnName': column})
        self.get_models()
        return response

    def transpose_columns_into_rows(
            self, start_column, column_count,
            combined_column_name, separator=':', prepend_column_name=True,
            ignore_blank_cells=True):

        response = self.do_json(
            'transpose-columns-into-rows',
            params={
                'startColumnName': start_column,
                'columnCount': column_count,
                'combinedColumnName': combined_column_name,
                'prependColumnName': prepend_column_name,
                'separator': separator,
                'ignoreBlankCells': ignore_blank_cells
            }
        )
        self.get_models()
        return response

    def transpose_rows_into_columns(self, column, row_count):
        response = self.do_json('transpose-rows-into-columns', params={'columnName': column, 'rowCount': row_count})
        self.get_models()
        return response

    def get_operations(self):
        response = self.do_json('get-operations')
        self.get_models()
        return response

    # Reconciliation
    # http://code.google.com/p/google-refine/wiki/ReconciliationServiceApi
    def guess_types_of_column(self, column, service):
        """Query the reconciliation service for what it thinks this column is.

        service: reconciliation endpoint URL

        Returns [
           {"id":"/domain/type","name":"Type Name","score":10.2,"count":18},
           ...
        ]
        """
        response = self.do_json(
            'guess-types-of-column',
            params={
                'columnName': column,
                'service': service
            },
            include_engine=False)
        return response['types']

    def get_reconciliation_services(self):
        response = self.get_preference('reconciliation.standardServices')
        self.recon_services = response
        return response

    def get_reconciliation_service_by_name_or_url(self, name):
        recon_services = self.get_reconciliation_services()
        for recon_service in recon_services:
            if recon_service['name'] == name or recon_service['server_url'] == name:
                return recon_service
        return None

    def reconcile(self, column, service, reconciliation_type=None, reconciliation_config=None):
        """Perform a reconciliation asynchronously.

        config: {
            "mode": "standard-service",
            "service": "http://.../reconcile/",
            "identifierSpace": "http://.../ns/authority",
            "schemaSpace": "http://.../ns/type",
            "type": {
                "id": "/domain/type",
                "name": "Type Name"
            },
            "autoMatch": true,
            "columnDetails": []
        }

        Returns typically {'code': 'pending'}; call wait_until_idle() to wait
        for reconciliation to complete.
        """
        # Create a reconciliation config by looking up recon service info
        if reconciliation_config is None:
            service = self.get_reconciliation_service_by_name_or_url(service)
            if reconciliation_type is None:
                raise ValueError('Must have at least one of config or type')
            reconciliation_config = {
                'mode': 'standard-service',
                'service': service['server_url'],
                'identifierSpace': service['identifierSpace'],
                'schemaSpace': service['schemaSpace'],
                'type': {
                    'id': reconciliation_type['id'],
                    'name': reconciliation_type['name'],
                },
                'autoMatch': True,
                'columnDetails': [],
            }
        return self.do_json('reconcile', params={'columnName': column, 'config': str(reconciliation_config)})


class InvalidFileFormat(ValueError):
    pass
