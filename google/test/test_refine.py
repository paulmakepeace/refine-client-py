#!/usr/bin/env python
"""
test_refine.py

These tests require a connection to a Refine server either at
http://127.0.0.1:3333/ or by specifying environment variables
GOOGLE_REFINE_HOST and GOOGLE_REFINE_PORT.
"""

# Copyright (c) 2011 Paul Makepeace, Real Programmers. All rights reserved.

import unittest

from google.refine import refine
from google.refine import facet
from google.test import refinetest


class RefineServerTest(refinetest.RefineTestCase):
    def test_init(self):
        self.assertEqual(self.server.server,
            'http://%s:%s' % (refine.REFINE_HOST, refine.REFINE_PORT))
        # strip trailing /
        server = refine.RefineServer('http://refine.example/')
        self.assertEqual(server.server, 'http://refine.example')

    def test_list_projects(self):
        projects = self.refine.list_projects()
        self.assertTrue(isinstance(projects, dict))

    def test_get_version(self):
        version_info = self.refine.get_version()
        for item in ('revision', 'version', 'full_version', 'full_name'):
            self.assertTrue(item in version_info)


class RefineTest(refinetest.RefineTestCase):
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
