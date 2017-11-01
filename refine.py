#!/usr/bin/env python
"""
Script to provide a command line interface to a Refine server.
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


import optparse
import os
import sys
import time

from google.refine import refine

from google.urllib2_file import urllib2_file
import urllib2
import urlparse

import json

class myParser(optparse.OptionParser):

    def format_epilog(self, formatter):
        return self.epilog

PARSER = \
    myParser(description='Script to provide a command line interface to an OpenRefine server.',
             usage='usage: %prog [--help | OPTIONS]',
             epilog="""
Examples:
  ./refine.py --list # show list of Refine projects, ID: name
  ./refine.py --list -H 127.0.0.1 -P 80 # specify hostname and port
  ./refine.py --create example.csv # create new project from file example.csv
  ./refine.py --create example.tsv --format=tsv --encoding=UTF-8
  ./refine.py --create example.xml --format=xml --recordPath=collection --recordPath=record
  ./refine.py --create example.json --format=json --recordPath=_ --recordPath=_
  ./refine.py --create example.xlsx --format=xlsx --sheets=0
  ./refine.py --create example.ods --format=ods --sheets=0
  ./refine.py --export 1234... > project.tsv # export project 1234... in tsv format
  ./refine.py --export --output=project.xls 1234... # export project in xls format
  ./refine.py --apply trim.json 1234... # apply rules in trim.json to project 1234...

""")

group1 = optparse.OptionGroup(PARSER, 'Connection options')
group1.add_option('-H', '--host', dest='host', metavar='127.0.0.1',
                  help='OpenRefine hostname (default: localhost)')
group1.add_option('-P', '--port', dest='port', metavar='3333',
                  help='OpenRefine port (default: 3333)')
PARSER.add_option_group(group1)

group2 = optparse.OptionGroup(PARSER, 'Commands')
group2.add_option('-l', '--list', dest='list', action='store_true',
                  help='List projects: refine.py -l')
group2.add_option('-c', '--create', dest='create', action='store_true',
                  help='Create project from file: refine.py -c [FILE]')
group2.add_option('-E', '--export', dest='export', action='store_true',
                  help='Export project: refine.py -E [PROJECTID]')
group2.add_option('-f', '--apply', dest='apply', metavar='file.json',
                  help='Apply JSON rules: refine.py -f [FILE] [PROJECTID]')
PARSER.add_option_group(group2)

group3 = optparse.OptionGroup(PARSER, 'Export options (optional)')
group3.add_option('-o', '--output', dest='output', metavar='file.csv',
                  help='Specify output filename and filetype. The filename ending (e.g. .csv) defines the output format (csv,tsv,xls,html)')
PARSER.add_option_group(group3)

group4 = optparse.OptionGroup(PARSER, 'Create format (mandatory for xml, json, fixed-width, xlsx, ods)')
group4.add_option('--format', dest='inputformat',
                  help='Specify input format (csv, tsv, xml, json, line-based, fixed-width, xlsx, ods)')
PARSER.add_option_group(group4)

group5 = optparse.OptionGroup(PARSER, 'Create options (mandatory for xml, json, fixed-width, xslx, ods; only together with --format)')
group5.add_option('--recordPath', dest='recordPath', action='append',
                  help='(xml, json), please provide path in multiple arguments without slashes, e.g. /collection/record/ should be entered like this: --recordPath=collection --recordPath=record')
group5.add_option('--columnWidths', dest='columnWidths',
                  help='(fixed-width) please provide widths separated by comma (e.g. 7,5)')
group5.add_option('--sheets', dest='sheets',
                  help='(xlsx, ods), please provide sheets separated by comma (e.g. 0,1), default: 0 (first sheet)')
PARSER.add_option_group(group5)

group6 = optparse.OptionGroup(PARSER, 'More create options (optional, only together with --format)')
group6.add_option('--projectName', dest='projectName',
                  help='(all formats), default: (filename)')
group6.add_option('--limit', dest='limit',
                  help='(all formats), default: -1')
group6.add_option('--includeFileSources', dest='includeFileSources',
                  help='(all formats), default: false')
group6.add_option('--trimStrings', dest='trimStrings',
                  help='(xml, json), default: false')
group6.add_option('--storeEmptyStrings', dest='storeEmptyStrings',
                  help='(xml, json), default: true')
group6.add_option('--guessCellValueTypes', dest='guessCellValueTypes',
                  help='(xml, csv, tsv, fixed-width, json), default: false')
group6.add_option('--encoding', dest='encoding',
                  help='(csv, tsv, line-based, fixed-width), please provide short encoding name (e.g. UTF-8)')
group6.add_option('--ignoreLines', dest='ignoreLines',
                  help='(csv, tsv, line-based, fixed-width, xlsx, ods), default: -1')
group6.add_option('--headerLines', dest='headerLines',
                  help='(csv, tsv, fixed-width, xlsx, ods), default: 1')
group6.add_option('--skipDataLines', dest='skipDataLines',
                  help='(csv, tsv, line-based, fixed-width, xlsx, ods), default: 0')
group6.add_option('--storeBlankRows', dest='storeBlankRows',
                  help='(csv, tsv, line-based, fixed-width, xlsx, ods), default: true')
group6.add_option('--separator', dest='separator',
                  help='(csv, tsv), default: csv: , tsv: \\t')
group6.add_option('--processQuotes', dest='processQuotes',
                  help='(csv, tsv), default: true')
group6.add_option('--storeBlankCellsAsNulls',
                  dest='storeBlankCellsAsNulls',
                  help='(csv, tsv, line-based, fixed-width, xlsx, ods), default: true')
group6.add_option('--linesPerRow', dest='linesPerRow',
                  help='(line-based), default: 1')
PARSER.add_option_group(group6)

def create_project(options, file_fullpath):
    servernewproject = 'http://' + refine.REFINE_HOST
    if refine.REFINE_PORT != '80':
        servernewproject += ':' + refine.REFINE_PORT

    input_format = ''
    input_options = ''

    # xml
    if options.inputformat == 'xml':
        input_format = 'text/xml'
        recordPath = 'record'
        if options.recordPath:
            recordPath = options.recordPath
        limit = '-1'
        if options.limit:
            limit = options.limit
        trimStrings = 'false'
        if options.trimStrings:
            trimStrings = options.trimStrings
        guessCellValueTypes = 'false'
        if options.guessCellValueTypes:
            guessCellValueTypes = options.guessCellValueTypes
        storeEmptyStrings = 'true'
        if options.storeEmptyStrings:
            storeEmptyStrings = options.storeEmptyStrings
        includeFileSources = 'false'
        if options.includeFileSources:
            includeFileSources = options.includeFileSources
        input_options = '{"recordPath":["' + '","'.join(recordPath) + '"]' \
            + ',"limit":' + limit \
            + ',"trimStrings":' + trimStrings \
            + ',"guessCellValueTypes":' + guessCellValueTypes \
            + ',"storeEmptyStrings":' + storeEmptyStrings \
            + ',"includeFileSources":' + includeFileSources \
            + '}'

    # csv
    if options.inputformat == 'csv':
        input_format = 'text/line-based/*sv'
        encoding = ''
        if options.encoding:
            encoding = options.encoding
        separator = ','
        if options.separator:
            separator = options.separator
        ignoreLines = '-1'
        if options.ignoreLines:
            ignoreLines = options.ignoreLines
        headerLines = '1'
        if options.headerLines:
            headerLines = options.headerLines
        skipDataLines = '0'
        if options.skipDataLines:
            skipDataLines = options.skipDataLines
        limit = '-1'
        if options.limit:
            limit = options.limit
        storeBlankRows = 'true'
        if options.storeBlankRows:
            storeBlankRows = options.storeBlankRows
        guessCellValueTypes = 'false'
        if options.guessCellValueTypes:
            guessCellValueTypes = options.guessCellValueTypes
        processQuotes = 'true'
        if options.processQuotes:
            processQuotes = options.processQuotes
        storeBlankCellsAsNulls = 'true'
        if options.storeBlankCellsAsNulls:
            storeBlankCellsAsNulls = options.storeBlankCellsAsNulls
        includeFileSources = 'false'
        if options.includeFileSources:
            includeFileSources = options.includeFileSources
        input_options = '{"encoding":"' + encoding + '"' \
            + ',"separator":"' + separator + '"' \
            + ',"ignoreLines":' + ignoreLines \
            + ',"headerLines":' + headerLines \
            + ',"skipDataLines":' + skipDataLines \
            + ',"limit":' + limit \
            + ',"storeBlankRows":' + storeBlankRows \
            + ',"guessCellValueTypes":' + guessCellValueTypes \
            + ',"processQuotes":' + processQuotes \
            + ',"storeBlankCellsAsNulls":' + storeBlankCellsAsNulls \
            + ',"includeFileSources":' + includeFileSources \
            + '}'

    # tsv
    if options.inputformat == 'tsv':
        input_format = 'text/line-based/*sv'
        encoding = ''
        if options.encoding:
            encoding = options.encoding
        separator = '\\t'
        if options.separator:
            separator = options.separator
        ignoreLines = '-1'
        if options.ignoreLines:
            ignoreLines = options.ignoreLines
        headerLines = '1'
        if options.headerLines:
            headerLines = options.headerLines
        skipDataLines = '0'
        if options.skipDataLines:
            skipDataLines = options.skipDataLines
        limit = '-1'
        if options.limit:
            limit = options.limit
        storeBlankRows = 'true'
        if options.storeBlankRows:
            storeBlankRows = options.storeBlankRows
        guessCellValueTypes = 'false'
        if options.guessCellValueTypes:
            guessCellValueTypes = options.guessCellValueTypes
        processQuotes = 'true'
        if options.processQuotes:
            processQuotes = options.processQuotes
        storeBlankCellsAsNulls = 'true'
        if options.storeBlankCellsAsNulls:
            storeBlankCellsAsNulls = options.storeBlankCellsAsNulls
        includeFileSources = 'false'
        if options.includeFileSources:
            includeFileSources = options.includeFileSources
        input_options = '{"encoding":"' + encoding + '"' \
            + ',"separator":"' + separator + '"' \
            + ',"ignoreLines":' + ignoreLines \
            + ',"headerLines":' + headerLines \
            + ',"skipDataLines":' + skipDataLines \
            + ',"limit":' + limit \
            + ',"storeBlankRows":' + storeBlankRows \
            + ',"guessCellValueTypes":' + guessCellValueTypes \
            + ',"processQuotes":' + processQuotes \
            + ',"storeBlankCellsAsNulls":' + storeBlankCellsAsNulls \
            + ',"includeFileSources":' + includeFileSources \
            + '}'

    # line-based
    if options.inputformat == 'line-based':
        input_format = 'text/line-based'
        encoding = ''
        if options.encoding:
            encoding = options.encoding
        linesPerRow = '1'
        if options.linesPerRow:
            linesPerRow = options.linesPerRow
        ignoreLines = '-1'
        if options.ignoreLines:
            ignoreLines = options.ignoreLines
        limit = '-1'
        if options.limit:
            limit = options.limit
        skipDataLines = '-1'
        if options.skipDataLines:
            skipDataLines = options.skipDataLines
        storeBlankRows = 'true'
        if options.storeBlankRows:
            storeBlankRows = options.storeBlankRows
        storeBlankCellsAsNulls = 'true'
        if options.storeBlankCellsAsNulls:
            storeBlankCellsAsNulls = options.storeBlankCellsAsNulls
        includeFileSources = 'false'
        if options.includeFileSources:
            includeFileSources = options.includeFileSources
        input_options = '{"encoding":"' + encoding + '"' \
            + ',"linesPerRow":' + linesPerRow \
            + ',"ignoreLines":' + ignoreLines \
            + ',"limit":' + limit \
            + ',"skipDataLines":' + skipDataLines \
            + ',"storeBlankRows":' + storeBlankRows \
            + ',"storeBlankCellsAsNulls":' + storeBlankCellsAsNulls \
            + ',"includeFileSources":' + includeFileSources \
            + '}'

    # fixed-width
    if options.inputformat == 'fixed-width':
        input_format = 'text/line-based/fixed-width'
        encoding = ''
        if options.encoding:
            encoding = options.encoding
        columnWidths = ''
        if options.columnWidths:
            columnWidths = options.columnWidths
        ignoreLines = '-1'
        if options.ignoreLines:
            ignoreLines = options.ignoreLines
        headerLines = '0'
        if options.headerLines:
            headerLines = options.headerLines
        skipDataLines = '0'
        if options.skipDataLines:
            skipDataLines = options.skipDataLines
        limit = '-1'
        if options.limit:
            limit = options.limit
        guessCellValueTypes = 'false'
        if options.guessCellValueTypes:
            guessCellValueTypes = options.guessCellValueTypes
        storeBlankRows = 'true'
        if options.storeBlankRows:
            storeBlankRows = options.storeBlankRows
        storeBlankCellsAsNulls = 'true'
        if options.storeBlankCellsAsNulls:
            storeBlankCellsAsNulls = options.storeBlankCellsAsNulls
        includeFileSources = 'false'
        if options.includeFileSources:
            includeFileSources = options.includeFileSources
        input_options = '{"encoding":"' + encoding + '"' \
            + ',"columnWidths":[' + columnWidths + ']' \
            + ',"ignoreLines":' + ignoreLines \
            + ',"headerLines":' + headerLines \
            + ',"skipDataLines":' + skipDataLines \
            + ',"limit":' + limit \
            + ',"guessCellValueTypes":' + guessCellValueTypes \
            + ',"storeBlankRows":' + storeBlankRows \
            + ',"storeBlankCellsAsNulls":' + storeBlankCellsAsNulls \
            + ',"includeFileSources":' + includeFileSources \
            + '}'

    # json
    if options.inputformat == 'json':
        input_format = 'text/json'
        recordPath = ['_', '_']
        if options.recordPath:
            recordPath = options.recordPath
        limit = '-1'
        if options.limit:
            limit = options.limit
        trimStrings = 'false'
        if options.trimStrings:
            trimStrings = options.trimStrings
        guessCellValueTypes = 'false'
        if options.guessCellValueTypes:
            guessCellValueTypes = options.guessCellValueTypes
        storeEmptyStrings = 'true'
        if options.storeEmptyStrings:
            storeEmptyStrings = options.storeEmptyStrings
        includeFileSources = 'false'
        if options.includeFileSources:
            includeFileSources = options.includeFileSources
        input_options = '{"recordPath":["' + '","'.join(recordPath) + '"]' \
            + ',"limit":' + limit \
            + ',"trimStrings":' + trimStrings \
            + ',"guessCellValueTypes":' + guessCellValueTypes \
            + ',"storeEmptyStrings":' + storeEmptyStrings \
            + ',"includeFileSources":' + includeFileSources \
            + '}'

    # xlsx
    if options.inputformat == 'xlsx':
        input_format = 'binary/text/xml/xls/xlsx'
        sheets = '0'
        if options.sheets:
            sheets = options.sheets
        ignoreLines = '-1'
        if options.ignoreLines:
            ignoreLines = options.ignoreLines
        headerLines = '1'
        if options.headerLines:
            headerLines = options.headerLines
        skipDataLines = '0'
        if options.skipDataLines:
            skipDataLines = options.skipDataLines
        limit = '-1'
        if options.limit:
            limit = options.limit
        storeBlankRows = 'true'
        if options.storeBlankRows:
            storeBlankRows = options.storeBlankRows
        storeBlankCellsAsNulls = 'true'
        if options.storeBlankCellsAsNulls:
            storeBlankCellsAsNulls = options.storeBlankCellsAsNulls
        includeFileSources = 'false'
        if options.includeFileSources:
            includeFileSources = options.includeFileSources
        input_options = '{"sheets":[' + sheets + ']' \
            + ',"ignoreLines":' + ignoreLines \
            + ',"headerLines":' + headerLines \
            + ',"skipDataLines":' + skipDataLines \
            + ',"limit":' + limit \
            + ',"storeBlankRows":' + storeBlankRows \
            + ',"storeBlankCellsAsNulls":' + storeBlankCellsAsNulls \
            + ',"includeFileSources":' + includeFileSources \
            + '}'

    # ods
    if options.inputformat == 'ods':
        input_format = 'text/xml/ods'
        sheets = '0'
        if options.sheets:
            sheets = options.sheets
        ignoreLines = '-1'
        if options.ignoreLines:
            ignoreLines = options.ignoreLines
        headerLines = '1'
        if options.headerLines:
            headerLines = options.headerLines
        skipDataLines = '0'
        if options.skipDataLines:
            skipDataLines = options.skipDataLines
        limit = '-1'
        if options.limit:
            limit = options.limit
        storeBlankRows = 'true'
        if options.storeBlankRows:
            storeBlankRows = options.storeBlankRows
        storeBlankCellsAsNulls = 'true'
        if options.storeBlankCellsAsNulls:
            storeBlankCellsAsNulls = options.storeBlankCellsAsNulls
        includeFileSources = 'false'
        if options.includeFileSources:
            includeFileSources = options.includeFileSources
        input_options = '{"sheets":[' + sheets + ']' \
            + ',"ignoreLines":' + ignoreLines \
            + ',"headerLines":' + headerLines \
            + ',"skipDataLines":' + skipDataLines \
            + ',"limit":' + limit \
            + ',"storeBlankRows":' + storeBlankRows \
            + ',"storeBlankCellsAsNulls":' + storeBlankCellsAsNulls \
            + ',"includeFileSources":' + includeFileSources \
            + '}'

    file_name = os.path.split(file_fullpath)[-1]
    projectName = file_name
    if options.projectName:
        projectName = options.projectName
    data = {}
    data['project-file'] = {'fd': open(file_fullpath),
                            'filename': file_name}
    data['project-name'] = projectName

    response = urllib2.urlopen(servernewproject
                               + '/command/core/create-project-from-upload?format='
                               + input_format + '&options='
                               + input_options, data)
    response_body = response.read()
    url_params = \
        urlparse.parse_qs(urlparse.urlparse(response.geturl()).query)

    if 'project' in url_params:
        project_id = url_params['project'][0]
        print('New project: ' + project_id)
    else:
        raise Exception('Project not created')

    # wait until project is created
    def wait_until_idle(self, polling_delay=0.5):
        while True:
            response = urllib2.urlopen(servernewproject + '/command/core/get-processes?project=' + project_id)
            response_body = response.read()
            url_params = \
                urlparse.parse_qs(urlparse.urlparse(response.geturl()).query)
            if 'processes' in url_params and len(url_params['processes']) > 0:
                time.sleep(polling_delay)
            else:
                print('done')
                return
   
    # check number of rows
    response = urllib2.urlopen(servernewproject
                               + '/command/core/get-rows?project='
                               + project_id
                               + '&start=0&limit=0')
    response_body = response.read()
    response_json = json.loads(response_body)
    if 'total' in response_body and response_json['total'] > 0:
        print('Number of rows:', response_json['total'])
    else:
        raise Exception('Project contains 0 rows. Please check --help for mandatory arguments for xml, json, xls and ods')

def list_projects():
    """Query the Refine server and list projects by ID: name."""
    projects = refine.Refine(refine.RefineServer()).list_projects().items()

    def date_to_epoch(json_dt):
        """Convert a JSON date time into seconds-since-epoch."""
        return time.mktime(time.strptime(json_dt, '%Y-%m-%dT%H:%M:%SZ'))
    projects.sort(key=lambda v: date_to_epoch(v[1]['modified']), reverse=True)
    for project_id, project_info in projects:
        print('{0:>14}: {1}'.format(project_id, project_info['name']))


def export_project(project, options):
    """Dump a project to stdout or options.output file."""
    export_format = 'tsv'
    if options.output:
        ext = os.path.splitext(options.output)[1][1:]     # 'xls'
        if ext:
            export_format = ext.lower()
        output = open(options.output, 'wb')
    else:
        output = sys.stdout
    output.writelines(project.export(export_format=export_format))
    output.close()


#noinspection PyPep8Naming
def main():
    """Main."""

    # get environment variables in docker network
    docker_host = os.environ.get('OPENREFINE_SERVER_PORT_3333_TCP_ADDR')
    if docker_host:
        os.environ["OPENREFINE_HOST"] = docker_host
        refine.REFINE_HOST = docker_host
    docker_port = os.environ.get('OPENREFINE_SERVER_PORT_3333_TCP_PORT')
    if docker_port:
        os.environ["OPENREFINE_PORT"] = docker_port
        refine.REFINE_PORT = docker_port

    options, args = PARSER.parse_args()

    if options.host:
        refine.REFINE_HOST = options.host
    if options.port:
        refine.REFINE_PORT = options.port

    if not options.list and len(args) != 1:
        PARSER.print_usage()

    if options.list:
        list_projects()

    if options.create:
        file_fullpath = args[0]
        create_project(options, file_fullpath)

    if options.apply:
        project = refine.RefineProject(args[0])
        response = project.apply_operations(options.apply)
        if response != 'ok':
            print >> sys.stderr, 'Failed to apply %s: %s' \
                % (options.apply, response)

    if options.export:
        project = refine.RefineProject(args[0])
        export_project(project, options)

        return project

if __name__ == '__main__':
    # return project so that it's available interactively, python -i refine.py
    refine_project = main()
