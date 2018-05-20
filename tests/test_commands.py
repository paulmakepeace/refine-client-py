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



if __name__ == '__main__':
    unittest.main()
