#! /usr/bin/env python
"""
Functions used by the command line interface (CLI)
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


import json
import os
import ssl
import sys
import time
import urllib

from google.refine import refine


def apply(project_id, history_file):
    """Apply OpenRefine history from json file to project."""
    project = refine.RefineProject(project_id)
    response = project.apply_operations(history_file)
    if response != 'ok':
        raise Exception('Failed to apply %s to %s: %s' %
                        (history_file, project_id, response))
    else:
        print('File %s has been successfully applied to project %s' %
              (history_file, project_id))


def create(project_file,
           project_format=None,
           project_name=None,
           columnWidths=None,
           encoding=None,
           guessCellValueTypes=False,
           headerLines=None,
           ignoreLines=None,
           includeFileSources=False,
           limit=None,
           linesPerRow=None,
           processQuotes=True,
           projectName=None,
           recordPath=None,
           separator=None,
           sheets=None,
           skipDataLines=None,
           storeBlankCellsAsNulls=True,
           storeBlankRows=True,
           storeEmptyStrings=True,
           trimStrings=False
           ):
    """Create a new project from file."""
    # guess format from file extension
    if not project_format:
        project_format = os.path.splitext(project_file)[1][1:].lower()
        if project_format == 'txt':
            try:
                columnWidths
                project_format = 'fixed-width'
            except NameError:
                project_format = 'line-based'
    # defaults for each file type
    if project_format == 'xml':
        project_format = 'text/xml'
        if not recordPath:
            recordPath = 'record'
    elif project_format == 'csv':
        project_format = 'text/line-based/*sv'
    elif project_format == 'tsv':
        project_format = 'text/line-based/*sv'
        if not separator:
            separator = '\t'
    elif project_format == 'line-based':
        project_format = 'text/line-based'
        if not skipDataLines:
            skipDataLines = -1
    elif project_format == 'fixed-width':
        project_format = 'text/line-based/fixed-width'
        if not headerLines:
            headerLines = 0
    elif project_format == 'json':
        project_format = 'text/json'
        if not recordPath:
            recordPath = ('_', '_')
    elif project_format == 'xls':
        project_format = 'binary/text/xml/xls/xlsx'
        if not sheets:
            sheets = 0
    elif project_format == 'xlsx':
        project_format = 'binary/text/xml/xls/xlsx'
        if not sheets:
            sheets = 0
    elif project_format == 'ods':
        project_format = 'text/xml/ods'
        if not sheets:
            sheets = 0
    # execute
    kwargs = {k: v for k, v in vars().items() if v is not None}
    project = refine.Refine(refine.RefineServer()).new_project(**kwargs)
    rows = project.do_json('get-rows')['total']
    if rows > 0:
        print('{0}: {1}'.format('id', project.project_id))
        print('{0}: {1}'.format('rows', rows))
        return project
    else:
        raise Exception(
            'Project contains 0 rows. Please check --help for mandatory '
            'arguments for xml, json, xlsx and ods')


def delete(project_id):
    """Delete project."""
    project = refine.RefineProject(project_id)
    response = project.delete()
    if response != True:
        raise Exception('Failed to delete %s: %s' %
                        (project_id, response))
    else:
        print('Project %s has been successfully deleted' % project_id)


def download(url, output_file=None):
    """Integrated download function for your convenience."""
    if not output_file:
        output_file = os.path.basename(url)
    if os.path.exists(output_file):
        print('Error: File %s already exists.\n'
              'Delete existing file or try command --output '
              'to specify a different filename.' % output_file)
        return
    # Workaround for SSL verification problems in one-file-executables
    context = ssl._create_unverified_context()
    urllib.urlretrieve(url, output_file, context=context)
    print('Download to file %s complete' % output_file)


def export(project_id, output_file=None, export_format=None):
    """Dump a project to stdout or file."""
    project = refine.RefineProject(project_id)
    if not export_format:
        export_format = 'tsv'
    if not output_file:
        sys.stdout.write(project.export(export_format=export_format).read())
    else:
        ext = os.path.splitext(output_file)[1][1:]
        if ext:
            export_format = ext.lower()
        with open(output_file, 'wb') as f:
            f.write(project.export(export_format).read())
        print('Export to file %s complete' % output_file)


def info(project_id):
    """Show project metadata"""
    projects = refine.Refine(refine.RefineServer()).list_projects().items()
    if project_id in [item[0] for item in projects]:
        project = refine.RefineProject(project_id)
        projects = refine.Refine(refine.RefineServer()).list_projects().items()
        for projects_id, projects_info in projects:
            if project_id == projects_id:
                print('{0:>20}: {1}'.format('id', project_id))
                print('{0:>20}: {1}'.format('url', 'http://' +
                                            refine.REFINE_HOST + ':' +
                                            refine.REFINE_PORT +
                                            '/project?project=' + project_id))
                for k, v in projects_info.items():
                    if v:
                        print('{0:>20}: {1}'.format(k, v))
        project_model = project.get_models()
        column_model = project_model['columnModel']
        columns = [column['name'] for column in column_model['columns']]
        for (i, v) in enumerate(columns, start=1):
            print('{0:>20}: {1}'.format('column ' + str(i).zfill(3), v))
    else:
        print('Error: No project found with id %s.\n'
              'Check existing projects with command --list' % (project_id))


def ls():
    """Query the server and list projects sorted by mtime."""
    projects = refine.Refine(refine.RefineServer()).list_projects().items()

    def date_to_epoch(json_dt):
        """Convert a JSON date time into seconds-since-epoch."""
        return time.mktime(time.strptime(json_dt, '%Y-%m-%dT%H:%M:%SZ'))
    projects.sort(key=lambda v: date_to_epoch(v[1]['modified']), reverse=True)
    if projects:
        for project_id, project_info in projects:
            print('{0:>14}: {1}'.format(project_id, project_info['name']))
    else:
        print('Error: No projects found')


def templating(project_id,
               template,
               output_file=None,
               mode=None,
               prefix='',
               rowSeparator='\n',
               suffix='',
               filterQuery=None,
               filterColumn=None,
               facets=None,
               splitToFiles=False,
               suffixById=None
               ):
    """Dump a project to stdout or file with templating."""
    project = refine.RefineProject(project_id)

    # basic config
    templateconfig = {'prefix': prefix,
                      'suffix': suffix,
                      'template': template,
                      'rowSeparator': rowSeparator}

    # construct the engine config
    if mode == 'record-based':
        engine = {'facets': [], 'mode': 'record-based'}
    else:
        engine = {'facets': [], 'mode': 'row-based'}
    if facets:
        engine['facets'].append(json.loads(facets))
    if filterQuery:
        if not filterColumn:
            filterColumn = project.get_models()['columnModel']['keyColumnName']
        textFilter = {'type': 'text',
                      'name': filterColumn,
                      'columnName': filterColumn,
                      'mode': 'regex',
                      'caseSensitive': False,
                      'query': filterQuery}
        engine['facets'].append(textFilter)
    templateconfig.update({'engine': json.dumps(engine)})

    # normal output or some refinable magic for splitToFiles functionality
    if not splitToFiles:
        if not output_file:
            sys.stdout.write(project.export_templating(
                             **templateconfig).read())
        else:
            with open(output_file, 'wb') as f:
                f.write(project.export_templating(**templateconfig).read())
            print('Export to file %s complete' % output_file)
    else:
        # common config for row-based and record-based
        prefix = templateconfig['prefix']
        suffix = templateconfig['suffix']
        split = '===|||THISISTHEBEGINNINGOFANEWRECORD|||==='
        keyColumn = project.get_models()['columnModel']['keyColumnName']
        if not output_file:
            output_file = time.strftime('%Y%m%d')
        else:
            base = os.path.splitext(output_file)[0]
            ext = os.path.splitext(output_file)[1][1:]
        if not ext:
            ext = 'txt'
        if suffixById:
            ids_template = ('{{forNonBlank(cells["' +
                            keyColumn +
                            '"].value, v, v, "")}}')
            ids_templateconfig = {'engine': json.dumps(engine),
                                  'template': ids_template,
                                  'rowSeparator': '\n'}
            ids = [line.rstrip('\n') for line in project.export_templating(
                   **ids_templateconfig) if line.rstrip('\n')]
        if mode == 'record-based':
            # record-based: split-character into template
            #               if key column is not blank (=record)
            template = ('{{forNonBlank(cells["' +
                        keyColumn +
                        '"].value, v, "' +
                        split +
                        '", "")}}' +
                        templateconfig['template'])
            templateconfig.update({'prefix': '',
                                   'suffix': '',
                                   'template': template,
                                   'rowSeparator': ''})
        else:
            # row-based: split-character into template
            template = split + templateconfig['template']
            templateconfig.update({'prefix': '',
                                   'suffix': '',
                                   'template': template,
                                   'rowSeparator': ''})
        records = project.export_templating(
            **templateconfig).read().split(split)
        del records[0]  # skip first blank entry
        if suffixById:
            for index, record in enumerate(records):
                output_file = base + '_' + ids[index] + '.' + ext
                with open(output_file, 'wb') as f:
                    f.writelines([prefix, record, suffix])
            print('Export to files complete. Last file: %s' % output_file)
        else:
            zeros = len(str(len(records)))
            for index, record in enumerate(records):
                output_file = base + '_' + \
                    str(index + 1).zfill(zeros) + '.' + ext
                with open(output_file, 'wb') as f:
                    f.writelines([prefix, record, suffix])
            print('Export to files complete. Last file: %s' % output_file)
