#!/usr/bin/env python
# encoding: utf-8
"""
test_refine.py

Created by Paul Makepeace on 2011-04-22.
Copyright (c) 2011 Real Programmers. All rights reserved.
"""

import sys
import os
import unittest
from google.refine import REFINE_HOST, REFINE_PORT
from google.refine import Facet, Engine
from google.refine import RefineServer, Refine, RefineProject

PATH_TO_TEST_DATA = os.path.join('google', 'test', 'data')
        
class RefineTestCase(unittest.TestCase):
    project_file = None
    project = None
    def setUp(self):
        self.server = RefineServer()
        self.refine = Refine(self.server)
        if self.project_file:
            self.project = self.refine.new_project(
                os.path.join(PATH_TO_TEST_DATA, self.project_file))

    def tearDown(self):
        if self.project:
            self.project.delete()
            self.project = None
              
               
class RefineServerTest(RefineTestCase):
    def test_init(self):
        self.assertEqual(self.server.server, 'http://%s:%s' % (REFINE_HOST, REFINE_PORT))
        server = RefineServer('http://refine.example/')
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
        self.assertTrue(isinstance(self.project, RefineProject))

    def test_get_models(self):
        self.assertEqual(self.project.key_column, 'email')
        self.assertTrue('email' in self.project.columns)
        self.assertEqual(self.project.column_index['name'], 1)
    
    def test_delete_project(self):
        self.assertTrue(self.project.delete())


class TutorialTestFacets(RefineTestCase):
    project_file = 'louisiana-elected-officials.csv'

    def test_basic_facet(self):
        facet = Facet(column='Party Code')
        facets = self.project.text_facet(facet)
        pc = facets.facets[0]
        self.assertEqual(pc.name, 'Party Code')
        self.assertEqual(pc.choices['D'].count, 3700)
        self.assertEqual(pc.choices['N'].count, 15)
        self.assertEqual(pc.blank_choice.count, 1446)
        
        engine = Engine(facet)
        engine.add_facet(Facet(column='Ethnicity'))
        facets = self.project.text_facet(engine=engine)
        e = facets.facets[1]
        self.assertEqual(e.choices['B'].count, 1255)
        self.assertEqual(e.choices['W'].count, 4469)


if __name__ == '__main__':
    unittest.main()