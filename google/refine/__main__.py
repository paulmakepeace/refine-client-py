#! /usr/bin/env python
"""
Script to provide a command line interface to a OpenRefine server.
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

from google.refine import refine
from google.refine import cli

reload(sys)
sys.setdefaultencoding('utf-8')

class myParser(optparse.OptionParser):

    def format_epilog(self, formatter):
        return self.epilog

PARSER = \
    myParser(description='Script to provide a command line interface to an OpenRefine server.',
             usage='usage: %prog [--help | OPTIONS]',
             epilog="""
Examples:
  --list # show list of projects (id: name)
  --list -H 127.0.0.1 -P 80 # specify hostname and port
  --info 2161595260364 # show metadata of project 
  --info "christmas gifts"
  --create example.csv # create new project from file example.csv
  --create example.tsv --encoding=UTF-8
  --create example.xml --recordPath=collection --recordPath=record
  --create example.json --recordPath=_ --recordPath=_
  --create example.xlsx --sheets=0
  --create example.ods --sheets=0
  --apply trim.json 2161595260364 # apply rules in trim.json to project 1234...
  --apply trim.json "christmas gifts"
  --export 2161595260364 > project.tsv # export project 2161595260364 in tsv format
  --export "christmas gifts" > project.tsv
  --export --output=project.xlsx 2161595260364 # export project in xlsx format
  --export --output=project.xlsx "christmas gifts"
  --export "My Address Book" --template='{ "friend" : {{jsonize(cells["friend"].value)}}, "address" : {{jsonize(cells["address"].value)}} }' --prefix='{ "rows" : [' --rowSeparator ',' --suffix '] }' --filterQuery="^mary$"
  --delete 2161595260364 # delete project 
  --delete "christmas gifts"
""")

group1 = optparse.OptionGroup(PARSER, 'Connection options')
group1.add_option('-H', '--host', dest='host', metavar='127.0.0.1',
                  help='OpenRefine hostname (default: 127.0.0.1)')
group1.add_option('-P', '--port', dest='port', metavar='3333',
                  help='OpenRefine port (default: 3333)')
PARSER.add_option_group(group1)

group2 = optparse.OptionGroup(PARSER, 'Commands')
group2.add_option('-c', '--create', dest='create', metavar='[FILE]',
                  help='Create project from file. The filename ending (e.g. .csv) defines the input format (csv,tsv,xml,json,txt,xls,xlsx,ods)')
group2.add_option('-l', '--list', dest='list', action='store_true',
                  help='List projects')
PARSER.add_option_group(group2)

group3 = optparse.OptionGroup(PARSER, 'Commands with argument [PROJECTID/PROJECTNAME]')
group3.add_option('-d', '--delete', dest='delete', action='store_true',
                  help='Delete project')
group3.add_option('-f', '--apply', dest='apply', metavar='[FILE]',
                  help='Apply JSON rules to OpenRefine project')
group3.add_option('-E', '--export', dest='export', action='store_true',
                  help='Export project in tsv format to stdout.')
group3.add_option('-o', '--output', dest='output', metavar='[FILE]',
                  help='Export project to file. The filename ending (e.g. .tsv) defines the output format (csv,tsv,xls,xlsx,html)')
group3.add_option('--info', dest='info', action='store_true',
                  help='show project metadata')
PARSER.add_option_group(group3)

group4 = optparse.OptionGroup(PARSER, 'Create options')
group4.add_option('--columnWidths', dest='columnWidths',
                  help='(txt/fixed-width) please provide widths separated by comma (e.g. 7,5)')
group4.add_option('--encoding', dest='encoding',
                  help='(csv,tsv,txt), please provide short encoding name (e.g. UTF-8)')
group4.add_option('--guessCellValueTypes', dest='guessCellValueTypes', metavar='true/false', choices=('true', 'false'),
                  help='(xml,csv,tsv,txt,json, default: false)')
group4.add_option('--headerLines', dest='headerLines', type="int",
                  help='(csv,tsv,txt/fixed-width,xls,xlsx,ods), default: 1, default txt/fixed-width: 0')
group4.add_option('--ignoreLines', dest='ignoreLines', type="int",
                  help='(csv,tsv,txt,xls,xlsx,ods), default: -1')
group4.add_option('--includeFileSources', dest='includeFileSources', metavar='true/false', choices=('true', 'false'),
                  help='(all formats), default: false')
group4.add_option('--limit', dest='limit', type="int",
                  help='(all formats), default: -1')
group4.add_option('--linesPerRow', dest='linesPerRow', type="int",
                  help='(txt/line-based), default: 1')
group4.add_option('--processQuotes', dest='processQuotes', metavar='true/false', choices=('true', 'false'),
                  help='(csv,tsv), default: true')
group4.add_option('--projectName', dest='project_name',
                  help='(all formats), default: filename')
group4.add_option('--recordPath', dest='recordPath', action='append',
                  help='(xml,json), please provide path in multiple arguments without slashes, e.g. /collection/record/ should be entered like this: --recordPath=collection --recordPath=record, default xml: record, default json: _ _')
group4.add_option('--separator', dest='separator',
                  help='(csv,tsv), default csv: , default tsv: \\t')
group4.add_option('--sheets', dest='sheets', action='append', type="int",
                  help='(xls,xlsx,ods), please provide sheets in multiple arguments, e.g. --sheets=0 --sheets=1, default: 0 (first sheet)')
group4.add_option('--skipDataLines', dest='skipDataLines', type="int",
                  help='(csv,tsv,txt,xls,xlsx,ods), default: 0, default line-based: -1')
group4.add_option('--storeBlankRows', dest='storeBlankRows', metavar='true/false', choices=('true', 'false'),
                  help='(csv,tsv,txt,xls,xlsx,ods), default: true')
group4.add_option('--storeBlankCellsAsNulls', dest='storeBlankCellsAsNulls', metavar='true/false', choices=('true', 'false'),
                  help='(csv,tsv,txt,xls,xlsx,ods), default: true')
group4.add_option('--storeEmptyStrings', dest='storeEmptyStrings', metavar='true/false', choices=('true', 'false'),
                  help='(xml,json), default: true')
group4.add_option('--trimStrings', dest='trimStrings', metavar='true/false', choices=('true', 'false'),
                  help='(xml,json), default: false')
PARSER.add_option_group(group4)

group5 = optparse.OptionGroup(PARSER, 'Legacy options')
group5.add_option('--format', dest='input_format',
help='Specify input format (csv,tsv,xml,json,line-based,fixed-width,xls,xlsx,ods)')
PARSER.add_option_group(group5)

group6= optparse.OptionGroup(PARSER, 'Templating export options')
group6.add_option('--template', dest='template',
help='mandatory; (big) text string that you enter in the *row template* textfield in the export/templating menu in the browser app)')
group6.add_option('--mode', dest='mode', metavar='row-based/record-based', choices=('row-based', 'record-based'),
help='engine mode (default: row-based)')
group6.add_option('--prefix', dest='prefix',
help='text string that you enter in the *prefix* textfield in the browser app')
group6.add_option('--rowSeparator', dest='rowSeparator',
help='text string that you enter in the *row separator* textfield in the browser app')
group6.add_option('--suffix', dest='suffix',
help='text string that you enter in the *suffix* textfield in the browser app')
group6.add_option('--filterQuery', dest='filterQuery', metavar='REGEX',
help='Simple RegEx text filter on filterColumn, e.g. ^12015$'),
group6.add_option('--filterColumn', dest='filterColumn', metavar='COLUMNNAME',
help='column name for filterQuery (default: name of first column)')
group6.add_option('--facets', dest='facets',
help='facets config in json format (may be extracted with browser dev tools in browser app)')
group6.add_option('--splitToFiles', dest='splitToFiles', metavar='true/false', choices=('true', 'false'),
help='will split each row/record into a single file; it specifies a presumably unique character series for splitting; --prefix and --suffix will be applied to all files; filename-prefix can be specified with --output (default: %Y%m%d)')
group6.add_option('--suffixById', dest='suffixById', metavar='true/false', choices=('true', 'false'),
help='enhancement option for --splitToFiles; will generate filename-suffix from values in key column')
PARSER.add_option_group(group6)

#noinspection PyPep8Naming
def main():
    """Command line interface."""

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
    commands_dict = { group2_arg.dest : getattr(options, group2_arg.dest) for group2_arg in group2.option_list }
    commands_dict.update({ group3_arg.dest : getattr(options, group3_arg.dest) for group3_arg in group3.option_list })
    commands_dict = { k: v for k, v in commands_dict.items() if v != None }
    if not commands_dict:
        PARSER.print_usage()
        return
    if options.host:
        refine.REFINE_HOST = options.host
    if options.port:
        refine.REFINE_PORT = options.port
    if args and not str.isdigit(args[0]):
        projects = refine.Refine(refine.RefineServer()).list_projects().items()
        idlist = []
        for project_id, project_info in projects:
            if args[0] == project_info['name']:
                idlist.append(str(project_id))
        if len(idlist) > 1:
            raise Exception('Found at least two projects. Please specify project by id.')
        else:
            args[0] = idlist[0]

    if options.list:
        cli.list_projects()
    if options.create:
        cli.create_project(options)
    if options.delete:
        project = refine.RefineProject(args[0])
        project.delete()
    if options.apply:
        project = refine.RefineProject(args[0])
        response = project.apply_operations(options.apply)
        if response != 'ok':
            print >> sys.stderr, 'Failed to apply %s: %s' \
                % (options.apply, response)
        return project
    if options.export or options.output:
        project = refine.RefineProject(args[0])
        cli.export_project(project, options)
        return project
    if options.info:
        cli.info(args[0])
        project = refine.RefineProject(args[0])
        return project

if __name__ == "__main__":
    # execute only if run as a script
    main()
