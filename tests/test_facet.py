#!/usr/bin/env python
"""
test_facet.py
"""

# Copyright (c) 2011 Paul Makepeace, Real Programmers. All rights reserved.

import json
import unittest

from google.refine.facet import *


class CamelTest(unittest.TestCase):
    def test_to_camel(self):
        pairs = (
            ('this', 'this'),
            ('this_attr', 'thisAttr'),
            ('From', 'from'),
        )
        for attr, camel_attr in pairs:
            self.assertEqual(to_camel(attr), camel_attr)

    def test_from_camel(self):
        pairs = (
            ('this', 'this'),
            ('This', 'this'),
            ('thisAttr', 'this_attr'),
            ('ThisAttr', 'this_attr'),
            ('From', 'from'),
        )
        for camel_attr, attr in pairs:
            self.assertEqual(from_camel(camel_attr), attr)


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
        facet = TextFilterFacet('column name', 'query')
        self.assertEqual(facet.query, 'query')

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
        facet.include('element').include('element 2')
        self.assertEqual(len(facet.selection), 2)


class EngineTest(unittest.TestCase):
    def test_init(self):
        engine = Engine()
        self.assertEqual(engine.mode, 'row-based')
        engine.mode = 'record-based'
        self.assertEqual(engine.mode, 'record-based')
        engine.set_facets(BlankFacet)
        self.assertEqual(engine.mode, 'record-based')
        engine.set_facets(BlankFacet, BlankFacet)
        self.assertEqual(len(engine), 2)

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

    def test_reset_remove(self):
        text_facet1 = TextFacet('column name')
        text_facet1.include('element')
        text_facet2 = TextFacet('column name 2')
        text_facet2.include('element 2')
        engine = Engine(text_facet1, text_facet2)
        self.assertEqual(len(engine), 2)
        self.assertEqual(len(text_facet1.selection), 1)
        engine.reset_all()
        self.assertEqual(len(text_facet1.selection), 0)
        self.assertEqual(len(text_facet2.selection), 0)
        engine.remove_all()
        self.assertEqual(len(engine), 0)


class SortingTest(unittest.TestCase):
    def test_sorting(self):
        sorting = Sorting()
        self.assertEqual(sorting.as_json(), '{"criteria": []}')
        sorting = Sorting('email')
        c = sorting.criteria[0]
        self.assertEqual(c['column'], 'email')
        self.assertEqual(c['valueType'], 'string')
        self.assertEqual(c['reverse'], False)
        self.assertEqual(c['caseSensitive'], False)
        self.assertEqual(c['errorPosition'], 1)
        self.assertEqual(c['blankPosition'], 2)
        sorting = Sorting(['email', 'gender'])
        self.assertEqual(len(sorting), 2)
        sorting = Sorting(['email', {'column': 'date', 'valueType': 'date'}])
        self.assertEqual(len(sorting), 2)
        c = sorting.criteria[1]
        self.assertEqual(c['column'], 'date')
        self.assertEqual(c['valueType'], 'date')


class FacetsResponseTest(unittest.TestCase):
    response = """{"facets":[{"name":"Party Code","expression":"value","columnName":"Party Code","invert":false,"choices":[{"v":{"v":"D","l":"D"},"c":3700,"s":false},{"v":{"v":"R","l":"R"},"c":1613,"s":false},{"v":{"v":"N","l":"N"},"c":15,"s":false},{"v":{"v":"O","l":"O"},"c":184,"s":false}],"blankChoice":{"s":false,"c":1446}}],"mode":"row-based"}"""

    def test_facet_response(self):
        party_code_facet = TextFacet('Party Code')
        engine = Engine(party_code_facet)
        facets = engine.facets_response(json.loads(self.response)).facets
        self.assertEqual(facets[0].choices['D'].count, 3700)
        self.assertEqual(facets[0].blank_choice.count, 1446)
        self.assertEqual(facets[party_code_facet], facets[0])
        # test iteration
        facet = [f for f in facets][0]
        self.assertEqual(facet, facets[0])


if __name__ == '__main__':
    unittest.main()
