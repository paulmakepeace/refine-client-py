#! /usr/bin/env python
"""
Commands provided for the CLI and interactive usage
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


import os
import sys
import time
import json

from google.refine import refine

def list_projects():
    """Query the OpenRefine server and list projects by ID: name."""
    projects = refine.Refine(refine.RefineServer()).list_projects().items()

    def date_to_epoch(json_dt):
        """Convert a JSON date time into seconds-since-epoch."""
        return time.mktime(time.strptime(json_dt, '%Y-%m-%dT%H:%M:%SZ'))
    projects.sort(key=lambda v: date_to_epoch(v[1]['modified']), reverse=True)
    for project_id, project_info in projects:
        print('{0:>14}: {1}'.format(project_id, project_info['name']))

def info(project_id):
    """Show project metadata"""
    projects = refine.Refine(refine.RefineServer()).list_projects().items()
    for projects_id, projects_info in projects:
        if project_id == projects_id:
            print('{0}: {1}'.format('id', projects_id))
            print('{0}: {1}'.format('name', projects_info['name']))
            print('{0}: {1}'.format('created', projects_info['created']))
            print('{0}: {1}'.format('modified', projects_info['modified']))

def create_project(options):
    """Create a new project from options.create file."""
    # general defaults are defined in google/refine/refine.py new_project
    # additional defaults for each file type
    defaults = {}
    defaults['xml'] = { 'project_format' : 'text/xml', 'recordPath' : 'record' }
    defaults['csv'] = { 'project_format' : 'text/line-based/*sv', 'separator' : ',' }
    defaults['tsv'] = { 'project_format' : 'text/line-based/*sv', 'separator' : '\t' }
    defaults['line-based'] = { 'project_format' : 'text/line-based', 'skipDataLines' : -1 }
    defaults['fixed-width'] = { 'project_format' : 'text/line-based/fixed-width', 'headerLines' : 0 }
    defaults['json'] = { 'project_format' : 'text/json', 'recordPath' : ('_', '_') }
    defaults['xls'] = { 'project_format' : 'binary/text/xml/xls/xlsx', 'sheets' : 0 }
    defaults['xlsx'] = { 'project_format' : 'binary/text/xml/xls/xlsx', 'sheets' : 0 }
    defaults['ods'] = { 'project_format' : 'text/xml/ods', 'sheets' : 0 }
    # guess format from file extension (or legacy option --format)
    input_format = os.path.splitext(options.create)[1][1:].lower()
    if input_format == 'txt' and options.columnWidths:
        input_format = 'fixed-width'
    if input_format == 'txt' and not options.columnWidths:
        input_format = 'line-based'
    if options.input_format:
        input_format = options.input_format
    # defaults for selected format
    input_dict = defaults[input_format]
    # user input
    input_user = { group4_arg.dest : getattr(options, group4_arg.dest) for group4_arg in group4.option_list }
    input_user['strings'] = { k: v for k, v in input_user.items() if v != None and v not in ['true', 'false'] }
    input_user['trues'] = { k: True for k, v in input_user.items() if v == 'true' }
    input_user['falses'] = { k: False for k, v in input_user.items() if v == 'false' }
    input_user_eval = input_user['strings']
    input_user_eval.update(input_user['trues'])
    input_user_eval.update(input_user['falses'])
    # merge defaults with user input
    input_dict.update(input_user_eval)
    input_dict['project_file'] = options.create
    refine.Refine(refine.RefineServer()).new_project(**input_dict)

def export_project(project, options):
    """Dump a project to stdout or options.output file."""
    export_format = 'tsv'
    if options.output and not options.splitToFiles == 'true':
        ext = os.path.splitext(options.output)[1][1:]
        if ext:
            export_format = ext.lower()
        output = open(options.output, 'wb')
    else:
        output = sys.stdout
    if options.template:
        templateconfig = { group6_arg.dest : getattr(options, group6_arg.dest) for group6_arg in group6.option_list if group6_arg.dest in ['prefix', 'template', 'rowSeparator', 'suffix'] }
        if options.mode == 'record-based':
            engine = { 'facets':[], 'mode':'record-based' }
        else:
            engine = { 'facets':[], 'mode':'row-based' }
        if options.facets:
            engine['facets'].append(json.loads(options.facets))
        if options.filterQuery:
            if not options.filterColumn:
                filterColumn = project.get_models()['columnModel']['keyColumnName']
            else:
                filterColumn = options.filterColumn
            textFilter = { 'type':'text', 'name':filterColumn, 'columnName':filterColumn, 'mode':'regex', 'caseSensitive':False, 'query':options.filterQuery }
            engine['facets'].append(textFilter)
        templateconfig.update({ 'engine': json.dumps(engine) })
        if options.splitToFiles == 'true':
            # common config for row-based and record-based
            prefix = templateconfig['prefix']
            suffix = templateconfig['suffix']
            split = '===|||THISISTHEBEGINNINGOFANEWRECORD|||==='
            keyColumn = project.get_models()['columnModel']['keyColumnName']
            if not options.output:
                filename = time.strftime('%Y%m%d')
            else:
                filename = os.path.splitext(options.output)[0]
                ext = os.path.splitext(options.output)[1][1:]
            if not ext:
                ext = 'txt'
            if options.suffixById:
                ids_template = '{{forNonBlank(cells["' + keyColumn + '"].value, v, v, "")}}'
                ids_templateconfig = { 'engine': json.dumps(engine), 'template': ids_template, 'rowSeparator':'\n' }
                ids = [line.rstrip('\n') for line in project.export_templating(**ids_templateconfig) if line.rstrip('\n')]
            if options.mode == 'record-based':
                # record-based: split-character into template if key column is not blank (=record)
                template = '{{forNonBlank(cells["' + keyColumn + '"].value, v, "' + split + '", "")}}' + templateconfig['template']
                templateconfig.update({ 'prefix': '', 'suffix': '', 'template': template, 'rowSeparator':'' })
            else:
                # row-based: split-character into template
                template = split + templateconfig['template']
                templateconfig.update({ 'prefix': '', 'suffix': '', 'template': template, 'rowSeparator':'' })
            records = project.export_templating(**templateconfig).read().split(split)
            del records[0] # skip first blank entry
            if options.suffixById:
                for index, record in enumerate(records):
                    output = open(filename + '_' + ids[index] + '.' + ext, 'wb')
                    output.writelines([prefix, record, suffix])
            else:
                zeros = len(str(len(records)))
                for index, record in enumerate(records):
                    output = open(filename + '_' + str(index+1).zfill(zeros) + '.' + ext, 'wb')
                    output.writelines([prefix, record, suffix])
        else:
            output.writelines(project.export_templating(**templateconfig))
            output.close()
    else:
        output.writelines(project.export(export_format=export_format))
        output.close()
