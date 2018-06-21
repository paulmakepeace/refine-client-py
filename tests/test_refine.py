#!/usr/bin/env python
"""
test_refine.py

These tests require a connection to a Refine server either at
http://127.0.0.1:3333/ or by specifying environment variables
OPENREFINE_HOST and OPENREFINE_PORT.
"""

# Copyright (c) 2011 Paul Makepeace, Real Programmers. All rights reserved.

import csv
import unittest
import io

from open.refine import refine
from tests import refinetest


class RefineServerTest(refinetest.RefineTestCase):
    def test_init(self):
        server_url = 'http://' + refine.REFINE_HOST
        if refine.REFINE_PORT != '80':
            server_url += ':' + refine.REFINE_PORT
        self.assertEqual(self.server.server, server_url)
        self.assertEqual(refine.RefineServer.server_url(), server_url)
        # strip trailing /
        server = refine.RefineServer('http://refine.example/')
        self.assertEqual(server.server, 'http://refine.example')

    def test_list_projects(self):
        projects = self.refine.list_projects()
        self.assertTrue(isinstance(projects, dict))

    def test_get_version(self):
        version_info = self.server.get_version()
        for item in ('revision', 'version', 'full_version', 'full_name'):
            self.assertTrue(item in version_info)

    def test_version(self):
        self.assertTrue(self.server.version in ('2.0', '2.1', '2.5', '2.8','3.0-beta',))


class RefineTest(refinetest.RefineTestCase):
    project_file = 'duplicates.csv'
    project_file_name = 'duplicates.csv'

    def test_new_project(self):
        self.assertTrue(isinstance(self.project, refine.RefineProject))

    def test_wait_until_idle(self):
        self.project.wait_until_idle()  # should just return

    def test_get_models(self):
        self.assertEqual('email', self.project.key_column)
        self.assertTrue('email' in self.project.columns)
        self.assertTrue('email' in self.project.column_order)
        self.assertEqual(self.project.column_order['name'], 1)

    def test_delete_project(self):
        self.assertTrue(self.project.delete())

    def test_open_export(self):
        content = refine.RefineProject(self.project.project_url()).export()
        self.assertTrue('email' in content)
        for line in content.splitlines():
            if line == 'email	name	state	gender	purchase':
                continue
            self.assertTrue('M' in content or 'F' in content)

    def test_open_export_csv(self):
        fp = refine.RefineProject(self.project.project_url()).export()
        fp = fp.split('\n')
        export = []
        for row in fp:
            export.append(row.split('\t'))
        self.assertTrue(export[0][0] == 'email')
        export.pop(0)
        export.pop(len(export)-1)
        for row in export:
            self.assertTrue(row[3] == 'F' or row[3] == 'M')

    # Not sure what I am dong wrong here
    # def test_invalid_type_raises_InvalidFileFormatError(self):
    #     self.assertRaises(self.refine.default_options('Bad Type'), refine.InvalidFileFormat)

    def test_default_options(self):
        options = self.refine.default_options('text/line-based')
        expected = {
                'encoding': '',
                'lines_per_row': 1,
                'ignore_lines': -1,
                'limit': -1,
                'skip_data_lines': -1,
                'store_blank_rows': True,
                'store_blank_cells_as_nulls': True,
                'include_file_sources': False
            }
        self.assertEqual(options, expected)

    def test_options_set_properly(self):
        options = self.refine.set_options('text/line-based', lines_per_row=2, limit=5)
        expected = {
                'encoding': '',
                'lines_per_row': 2,
                'ignore_lines': -1,
                'limit': 5,
                'skip_data_lines': -1,
                'store_blank_rows': True,
                'store_blank_cells_as_nulls': True,
                'include_file_sources': False
            }
        self.assertEqual(options, expected)

if __name__ == '__main__':
    unittest.main()
