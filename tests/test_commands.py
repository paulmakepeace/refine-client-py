#!/usr/bin/env python

import unittest

from open.refine import facet
from tests import refinetest


class TestCommands(refinetest.RefineTestCase):
    project_file = 'louisiana-elected-officials.csv'
    project_file_name = 'louisiana-elected-officials.csv'

    def setUp(self):
        refinetest.RefineTestCase.setUp(self)
        response = self.project.get_rows(limit=10)
        self.assertEqual(10, len(response.rows))
        self.assertEqual(10, response.limit)
        self.project.mass_edit('Office Title', [{'from': ['Council Member', 'Councilmember'], 'to': 'Council Member'}])
        self.assertInResponse('9')
        clusters = self.project.compute_clusters('Candidate Name')
        for cluster in clusters[0:3]:  # just do a few
            for match in cluster:
                # {2}
                if match['value'].endswith(', '):
                    response = self.project.get_rows(
                        facet.TextFacet('Candidate Name', match['value']))
                    self.assertEqual(len(response.rows), 1)
                    for row in response.rows:
                        self.project.star_row(row)
                        self.assertInResponse(str(row.index + 1))
        # {5}, {6}, {7}
        response = self.project.compute_facets(facet.StarredFacet(True))
        self.assertEqual(len(response.facets[0].choices), 2)  # true & false
        self.assertEqual(response.facets[0].choices[True].count, 2)
        self.project.remove_rows()
        self.assertInResponse('2 rows')

    def test_get_operations(self):
        response = self.project.get_operations()
        self.assertTrue(len(response.get("entries")) == 4)

    def test_apply_operations(self):
        operations_list = [
            {'op': 'core/column-addition',
                 'description': 'Create column zip type at index 15 based on column Zip Code 2 using expression grel:value.type()',
                 'engineConfig':
                     {
                         'mode': 'row-based',
                         'facets': []
                     },
                 'newColumnName': 'zip type',
                 'columnInsertIndex': 15,
                 'baseColumnName': 'Zip Code 2',
                 'expression': 'grel:value.type()',
                 'onError': 'set-to-blank'},
            {
                'op': 'core/column-addition',
                 'description': 'Create column testing at index 15 based on column Zip Code 2 using expression grel:value.toString()[0,5]',
                 'engineConfig':
                     {
                         'mode': 'row-based',
                         'facets': []
                     },
                 'newColumnName': 'testing',
                 'columnInsertIndex': 15,
                 'baseColumnName': 'Zip Code 2',
                 'expression': 'grel:value.toString()[0,5]',
                 'onError': 'set-to-blank'},
            {
                'op': 'core/column-addition',
                'description': 'Create column the same? at index 16 based on column testing using expression grel:cells["Zip Code 2"].value == value',
                'engineConfig':
                    {
                        'mode': 'row-based',
                        'facets': []
                    },
                'newColumnName': 'the same?',
                'columnInsertIndex': 16,
                'baseColumnName': 'testing',
                'expression': 'grel:cells["Zip Code 2"].value == value',
                'onError': 'set-to-blank'},
            {
                'op': 'core/text-transform',
                'description': 'Text transform on cells in column Office Level using expression grel:value.toNumber()',
                    'engineConfig':
                        {
                            'mode': 'row-based',
                            'facets':
                                [
                                    {
                                        'omitError': False,
                                        'expression': 'value',
                                        'selectBlank': True,
                                        'selection': [],
                                        'selectError': False,
                                        'invert': False,
                                        'name': 'the same?',
                                        'omitBlank': False,
                                        'type': 'list',
                                        'columnName': 'the same?'
                                    }
                                ]
                        },
                'columnName': 'Office Level',
                'expression': 'grel:value.toNumber()',
                'onError': 'keep-original',
                'repeat': False,
                'repeatCount': 10},
            {
                'op': 'core/fill-down',
                'description': 'Fill down cells in column Salutation',
                'engineConfig':
                    {
                        'mode': 'row-based',
                        'facets': []}, 'columnName': 'Salutation'
            }
        ]
        self.project.apply_operations(operations=operations_list)
        response = self.project.get_models()
        self.assertTrue(response["columnModel"]["columns"][15]["name"] == 'testing')



if __name__ == '__main__':
    unittest.main()
