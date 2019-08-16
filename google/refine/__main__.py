#! /usr/bin/env python
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

from google.refine import refine
from google.refine import cli


class myParser(optparse.OptionParser):

    def format_epilog(self, formatter):
        return self.epilog


PARSER = \
    myParser(description=('Script to provide a command line interface to an '
                          'OpenRefine server.'),
             usage='usage: %prog [--help | OPTIONS]',
             epilog="""
Example data:
  --download "https://git.io/fj5hF" --output=duplicates.csv
  --download "https://git.io/fj5ju" --output=duplicates-deletion.json

Basic commands:
  --list # list all projects
  --list -H 127.0.0.1 -P 80 # specify hostname and port
  --create duplicates.csv # create new project from file
  --info "duplicates" # show project metadata
  --apply duplicates-deletion.json "duplicates" # apply rules in file to project
  --export "duplicates" # export project to terminal in tsv format
  --export --output=deduped.xls "duplicates" # export project to file in xls format
  --delete "duplicates" # delete project

Some more examples:
  --info 1234567890123 # specify project by id
  --create example.tsv --encoding=UTF-8
  --create example.xml --recordPath=collection --recordPath=record
  --create example.json --recordPath=_ --recordPath=_
  --create example.xlsx --sheets=0
  --create example.ods --sheets=0

Example for Templating Export:
  Cf. https://github.com/opencultureconsulting/openrefine-client#advanced-templating
""")

group1 = optparse.OptionGroup(PARSER, 'Connection options')
group1.add_option('-H', '--host', dest='host',
                  metavar='127.0.0.1',
                  help='OpenRefine hostname (default: 127.0.0.1)')
group1.add_option('-P', '--port', dest='port',
                  metavar='3333',
                  help='OpenRefine port (default: 3333)')
PARSER.add_option_group(group1)

group2 = optparse.OptionGroup(PARSER, 'Commands')
group2.add_option('-c', '--create', dest='create',
                  metavar='[FILE]',
                  help='Create project from file. The filename ending (e.g. .csv) defines the input format (csv,tsv,xml,json,txt,xls,xlsx,ods)')
group2.add_option('-l', '--list', dest='list',
                  action='store_true',
                  help='List projects')
group2.add_option('--download', dest='download',
                  metavar='[URL]',
                  help='Download file from URL (e.g. example data). Combine with --output to specify a filename.')
PARSER.add_option_group(group2)

group3 = optparse.OptionGroup(
    PARSER, 'Commands with argument [PROJECTID/PROJECTNAME]')
group3.add_option('-d', '--delete', dest='delete',
                  action='store_true',
                  help='Delete project')
group3.add_option('-f', '--apply', dest='apply',
                  metavar='[FILE]',
                  help='Apply JSON rules to OpenRefine project')
group3.add_option('-E', '--export', dest='export',
                  action='store_true',
                  help='Export project in tsv format to stdout.')
group3.add_option('-o', '--output', dest='output',
                  metavar='[FILE]',
                  help='Export project to file. The filename ending (e.g. .tsv) defines the output format (csv,tsv,xls,xlsx,html)')
group3.add_option('--template', dest='template',
                  metavar='[STRING]',
                  help='Export project with templating. Provide (big) text string that you enter in the *row template* textfield in the export/templating menu in the browser app)')
group3.add_option('--info', dest='info',
                  action='store_true',
                  help='show project metadata')
PARSER.add_option_group(group3)

group4 = optparse.OptionGroup(PARSER, 'General options')
group4.add_option('--format', dest='file_format',
                  help='Override file detection (import: csv,tsv,xml,json,line-based,fixed-width,xls,xlsx,ods; export: csv,tsv,html,xls,xlsx,ods)')
PARSER.add_option_group(group4)

group5 = optparse.OptionGroup(PARSER, 'Create options')
group5.add_option('--columnWidths', dest='columnWidths',
                  action='append',
                  type='int',
                  help='(txt/fixed-width), please provide widths in multiple arguments, e.g. --columnWidths=7 --columnWidths=5')
group5.add_option('--encoding', dest='encoding',
                  help='(csv,tsv,txt), please provide short encoding name (e.g. UTF-8)')
group5.add_option('--guessCellValueTypes', dest='guessCellValueTypes',
                  metavar='true/false', choices=('true', 'false'),
                  help='(xml,csv,tsv,txt,json, default: false)')
group5.add_option('--headerLines', dest='headerLines',
                  type="int",
                  help='(csv,tsv,txt/fixed-width,xls,xlsx,ods), default: 1, default txt/fixed-width: 0')
group5.add_option('--ignoreLines', dest='ignoreLines',
                  type="int",
                  help='(csv,tsv,txt,xls,xlsx,ods), default: -1')
group5.add_option('--includeFileSources', dest='includeFileSources',
                  metavar='true/false', choices=('true', 'false'),
                  help='(all formats), default: false')
group5.add_option('--limit', dest='limit',
                  type="int",
                  help='(all formats), default: -1')
group5.add_option('--linesPerRow', dest='linesPerRow',
                  type="int",
                  help='(txt/line-based), default: 1')
group5.add_option('--processQuotes', dest='processQuotes',
                  metavar='true/false', choices=('true', 'false'),
                  help='(csv,tsv), default: true')
group5.add_option('--projectName', dest='project_name',
                  help='(all formats), default: filename')
group5.add_option('--projectTags', dest='projectTags',
                  action='append',
                  help='(all formats), please provide tags in multiple arguments, e.g. --projectTags=beta --projectTags=client1')
group5.add_option('--recordPath', dest='recordPath',
                  action='append',
                  help='(xml,json), please provide path in multiple arguments without slashes, e.g. /collection/record/ should be entered like this: --recordPath=collection --recordPath=record, default xml: record, default json: _ _')
group5.add_option('--separator', dest='separator',
                  help='(csv,tsv), default csv: , default tsv: \\t')
group5.add_option('--sheets', dest='sheets',
                  action='append',
                  type="int",
                  help='(xls,xlsx,ods), please provide sheets in multiple arguments, e.g. --sheets=0 --sheets=1, default: 0 (first sheet)')
group5.add_option('--skipDataLines', dest='skipDataLines',
                  type="int",
                  help='(csv,tsv,txt,xls,xlsx,ods), default: 0, default line-based: -1')
group5.add_option('--storeBlankCellsAsNulls', dest='storeBlankCellsAsNulls',
                  metavar='true/false', choices=('true', 'false'),
                  help='(csv,tsv,txt,xls,xlsx,ods), default: true')
group5.add_option('--storeBlankRows', dest='storeBlankRows',
                  metavar='true/false', choices=('true', 'false'),
                  help='(csv,tsv,txt,xls,xlsx,ods), default: true')
group5.add_option('--storeEmptyStrings', dest='storeEmptyStrings',
                  metavar='true/false', choices=('true', 'false'),
                  help='(xml,json), default: true')
group5.add_option('--trimStrings', dest='trimStrings',
                  metavar='true/false', choices=('true', 'false'),
                  help='(xml,json), default: false')
PARSER.add_option_group(group5)

group6 = optparse.OptionGroup(PARSER, 'Templating options')
group6.add_option('--mode', dest='mode',
                  metavar='row-based/record-based',
                  choices=('row-based', 'record-based'),
                  help='engine mode (default: row-based)')
group6.add_option('--prefix', dest='prefix',
                  help='text string that you enter in the *prefix* textfield in the browser app')
group6.add_option('--rowSeparator', dest='rowSeparator',
                  help='text string that you enter in the *row separator* textfield in the browser app')
group6.add_option('--suffix', dest='suffix',
                  help='text string that you enter in the *suffix* textfield in the browser app')
group6.add_option('--filterQuery', dest='filterQuery',
                  metavar='REGEX',
                  help='Simple RegEx text filter on filterColumn, e.g. ^12015$'),
group6.add_option('--filterColumn', dest='filterColumn',
                  metavar='COLUMNNAME',
                  help='column name for filterQuery (default: name of first column)')
group6.add_option('--facets', dest='facets',
                  help='facets config in json format (may be extracted with browser dev tools in browser app)')
group6.add_option('--splitToFiles', dest='splitToFiles',
                  metavar='true/false', choices=('true', 'false'),
                  help='will split each row/record into a single file; it specifies a presumably unique character series for splitting; --prefix and --suffix will be applied to all files; filename-prefix can be specified with --output (default: %Y%m%d)')
group6.add_option('--suffixById', dest='suffixById',
                  metavar='true/false', choices=('true', 'false'),
                  help='enhancement option for --splitToFiles; will generate filename-suffix from values in key column')
PARSER.add_option_group(group6)


def main():
    """Command line interface."""

    options, args = PARSER.parse_args()

    # set environment
    if options.host:
        refine.REFINE_HOST = options.host
    if options.port:
        refine.REFINE_PORT = options.port

    # get project_id
    if args and not str.isdigit(args[0]):
        projects = refine.Refine(refine.RefineServer()).list_projects().items()
        idlist = []
        for project_id, project_info in projects:
            if args[0] == project_info['name']:
                idlist.append(str(project_id))
        if len(idlist) > 1:
            print('Error: Found %s projects with name %s.\n'
                  'Please specify project by id.' % (len(idlist), args[0]))
            for i in idlist:
                print('')
                cli.info(i)
            return
        else:
            try:
                project_id = idlist[0]
            except IndexError:
                print('Error: No project found with name %s.\n'
                      'Try command --list' % args[0])
                return
    elif args:
        project_id = args[0]

    # commands without args
    if options.list:
        cli.ls()
    elif options.download:
        cli.download(options.download, output_file=options.output)
    elif options.create:
        group5_dict = {group5_arg.dest: getattr(options, group5_arg.dest)
                       for group5_arg in group5.option_list}
        kwargs = {k: v for k, v in group5_dict.items()
                  if v is not None and v not in ['true', 'false']}
        kwargs.update({k: True for k, v in group5_dict.items()
                       if v == 'true'})
        kwargs.update({k: False for k, v in group5_dict.items()
                       if v == 'false'})
        if options.file_format:
            kwargs.update({'project_format': options.file_format})
        cli.create(options.create, **kwargs)
    # commands with args
    elif args and options.info:
        cli.info(project_id)
    elif args and options.delete:
        cli.delete(project_id)
    elif args and options.apply:
        cli.apply(project_id, options.apply)
    elif args and options.template:
        group6_dict = {group6_arg.dest: getattr(options, group6_arg.dest)
                       for group6_arg in group6.option_list}
        kwargs = {k: v for k, v in group6_dict.items()
                  if v is not None and v not in ['true', 'false']}
        kwargs.update({k: True for k, v in group6_dict.items()
                       if v == 'true'})
        kwargs.update({k: False for k, v in group6_dict.items()
                       if v == 'false'})
        cli.templating(project_id, options.template,
                       output_file=options.output, **kwargs)
    elif args and (options.export or options.output):
        cli.export(project_id, output_file=options.output,
                   export_format=options.file_format)
    else:
        PARSER.print_usage()


if __name__ == "__main__":
    # execute only if run as a script
    main()
