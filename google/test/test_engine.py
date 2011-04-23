#!/usr/bin/env python
# encoding: utf-8
"""
test_engine.py

Created by Paul Makepeace on 2011-04-22.
Copyright (c) 2011 Real Programmers. All rights reserved.
"""

import json

import os
import sys
import unittest
import urllib
from google.refine import Facet, Engine, FacetsResponse

class FacetTest(unittest.TestCase):
    def test_init(self):
        facet = Facet('column name')
        engine = Engine(facet)
        self.assertTrue(str(engine))
        facet2 = Facet('Ethnicity')
        engine.add_facet(facet2)
        print engine.as_json()

    def test_serialize(self):
        engine = Engine()
        engine_json = engine.as_json()
        self.assertEqual(engine_json, '{"facets": [], "mode": "row-based"}')

    def test_facets_response(self):
        response = """{"facets":[{"name":"Party Code","expression":"value","columnName":"Party Code","invert":false,"choices":[{"v":{"v":"D","l":"D"},"c":3700,"s":false},{"v":{"v":"R","l":"R"},"c":1613,"s":false},{"v":{"v":"N","l":"N"},"c":15,"s":false},{"v":{"v":"O","l":"O"},"c":184,"s":false}],"blankChoice":{"s":false,"c":1446}}],"mode":"row-based"}"""
        response = json.loads(response)
        facets = FacetsResponse(response)
        self.assertEqual(facets.facets[0].choices['D'].count, 3700)
        
if __name__ == '__main__':
    unittest.main()