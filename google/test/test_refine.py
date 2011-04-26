#!/usr/bin/env python
"""
test_refine.py

These tests require a connection to a Refine server either at
http://127.0.0.1:3333/ or by specifying environment variables REFINE_HOST
and REFINE_PORT.
"""

# Copyright (c) 2011 Paul Makepeace, Real Programmers. All rights reserved.

import os
import unittest

from google.refine import refine
from google.refine import facet

PATH_TO_TEST_DATA = os.path.join('google', 'test', 'data')


class RefineTestCase(unittest.TestCase):
    project_file = None
    project_file_options = {}
    project = None
    # Section "2. Exploration using Facets": {1}, {2}
    def setUp(self):
        self.server = refine.RefineServer()
        self.refine = refine.Refine(self.server)
        if self.project_file:
            self.project = self.refine.new_project(
                os.path.join(PATH_TO_TEST_DATA, self.project_file),
                **self.project_file_options)

    def tearDown(self):
        if self.project:
            self.project.delete()
            self.project = None


class RefineServerTest(RefineTestCase):
    def test_init(self):
        self.assertEqual(self.server.server,
            'http://%s:%s' % (refine.REFINE_HOST, refine.REFINE_PORT))
        server = refine.RefineServer('http://refine.example/')
        self.assertEqual(server.server, 'http://refine.example')

    def test_list_projects(self):
        projects = self.refine.list_projects()
        self.assertTrue(isinstance(projects, dict))

    def test_get_version(self):
        version_info = self.refine.get_version()
        for item in ('revision', 'version', 'full_version', 'full_name'):
            self.assertTrue(item in version_info)


class RefineTest(RefineTestCase):
    project_file = 'duplicates.csv'

    def test_new_project(self):
        self.assertTrue(isinstance(self.project, refine.RefineProject))

    def test_get_models(self):
        self.assertEqual(self.project.key_column, 'email')
        self.assertTrue('email' in self.project.column_order)
        self.assertEqual(self.project.column_order['name'], 1)

    def test_delete_project(self):
        self.assertTrue(self.project.delete())


if __name__ == '__main__':
    unittest.main()
