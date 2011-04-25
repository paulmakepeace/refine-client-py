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
from google.refine import TextFacet, NumericFacet, StarredFacet, FlaggedFacet
from google.refine import Engine, FacetsResponse

class FacetTest(unittest.TestCase):
    def test_init(self):
        facet = TextFacet('column name')
        engine = Engine(facet)
        self.assertEqual(facet.selection, [])
        self.assertTrue(str(engine))
        facet = NumericFacet('column name', From=1, to=5)
        self.assertEqual(facet.to, 5)
        self.assertEqual(facet.From, 1)
        facet = StarredFacet()
        self.assertEqual(facet.expression, 'row.starred')
        facet = StarredFacet(True)
        self.assertEqual(facet.selection[0]['v']['v'], True)
        facet = FlaggedFacet(False)
        self.assertEqual(facet.selection[0]['v']['v'], False)
        self.assertRaises(ValueError, FlaggedFacet, 'false')    # no strings

    def test_serialize(self):
        engine = Engine()
        engine_json = engine.as_json()
        self.assertEqual(engine_json, '{"facets": [], "mode": "row-based"}')
        facet = TextFacet(column='column')
        self.assertEqual(facet.as_dict(), {'selectError': False, 'name': 'column', 'selection': [], 'expression': 'value', 'invert': False, 'columnName': 'column', 'selectBlank': False, 'omitBlank': False, 'type': 'list', 'omitError': False})
        facet = NumericFacet(column='column', From=1, to=5)
        self.assertEqual(facet.as_dict(), {'from': 1, 'to': 5, 'selectBlank': True, 'name': 'column', 'selectError': True, 'expression': 'value',  'selectNumeric': True, 'columnName': 'column', 'selectNonNumeric': True, 'type': 'range'})

    def test_add_facet(self):
        facet = TextFacet(column='Party Code')
        engine = Engine(facet)
        engine.add_facet(TextFacet(column='Ethnicity'))
        self.assertEqual(len(engine.facets), 2)
        self.assertEqual(len(engine), 2)

    def test_selections(self):
        facet = TextFacet('column name')
        facet.include('element')
        self.assertEqual(len(facet.selection), 1)
        facet.include('element 2')
        self.assertEqual(len(facet.selection), 2)
        facet.exclude('element')
        self.assertEqual(len(facet.selection), 1)
        facet.reset()
        self.assertEqual(len(facet.selection), 0)

    def test_reset_remove(self):
        text_facet1 = TextFacet('column name')
        text_facet1.include('element')
        text_facet2 = TextFacet('column name 2')
        text_facet2.include('element 2')
        engine = Engine([text_facet1, text_facet2])
        self.assertEqual(len(engine), 2)
        self.assertEqual(len(text_facet1.selection), 1)
        engine.reset_all()
        self.assertEqual(len(text_facet1.selection), 0)
        self.assertEqual(len(text_facet2.selection), 0)
        engine.remove_all()
        self.assertEqual(len(engine), 0)


    def test_facets_response(self):
        response = """{"facets":[{"name":"Party Code","expression":"value","columnName":"Party Code","invert":false,"choices":[{"v":{"v":"D","l":"D"},"c":3700,"s":false},{"v":{"v":"R","l":"R"},"c":1613,"s":false},{"v":{"v":"N","l":"N"},"c":15,"s":false},{"v":{"v":"O","l":"O"},"c":184,"s":false}],"blankChoice":{"s":false,"c":1446}}],"mode":"row-based"}"""
        response = FacetsResponse(json.loads(response))
        facets = response.facets
        self.assertEqual(facets[0].choices['D'].count, 3700)
        self.assertEqual(facets[0].blank_choice.count, 1446)


if __name__ == '__main__':
    unittest.main()