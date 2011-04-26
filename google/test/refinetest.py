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
