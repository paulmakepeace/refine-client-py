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
from google.refine import NumericFacet, TextFacet, StarredFacet, Engine
from google.refine import RefineServer, Refine, RefineProject
from google.refine import to_camel, from_camel

PATH_TO_TEST_DATA = os.path.join('google', 'test', 'data')


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


class RefineTestCase(unittest.TestCase):
    project_file = None
    project = None
    # Section "2. Exploration using Facets": {1}, {2}
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
        self.assertTrue('email' in self.project.column_order)
        self.assertEqual(self.project.column_order['name'], 1)

    def test_delete_project(self):
        self.assertTrue(self.project.delete())


class TutorialTestFacets(RefineTestCase):
    project_file = 'louisiana-elected-officials.csv'

    def test_get_rows(self):
        # Section "2. Exploration using Facets": {3}
        response = self.project.get_rows(limit=10)
        self.assertEqual(len(response.rows), 10)
        self.assertEqual(response.limit, 10)
        self.assertEqual(response.total, 6958)
        for row in response.rows:
            self.assertFalse(row.flagged)
            self.assertFalse(row.starred)

    def test_facet(self):
        # Section "2. Exploration using Facets": {4}
        party_code_facet = TextFacet(column='Party Code')
        response = self.project.compute_facets(party_code_facet)
        pc = response.facets[0]
        self.assertEqual(pc.name, 'Party Code')
        self.assertEqual(pc.choices['D'].count, 3700)
        self.assertEqual(pc.choices['N'].count, 15)
        self.assertEqual(pc.blank_choice.count, 1446)
        # {5}, {6}
        engine = Engine(party_code_facet)
        ethnicity_facet = TextFacet(column='Ethnicity')
        engine.add_facet(ethnicity_facet)
        self.project.engine = engine
        response = self.project.compute_facets()
        e = response.facets[1]
        self.assertEqual(e.choices['B'].count, 1255)
        self.assertEqual(e.choices['W'].count, 4469)
        # {7}
        ethnicity_facet.include('B')
        response = self.project.get_rows()
        self.assertEqual(response.filtered, 1255)
        indexes = [r.index for r in response.rows]
        self.assertEqual(indexes, [1, 2, 3, 4, 6, 12, 18, 26, 28, 32])
        # {8}
        response = self.project.compute_facets()
        pc = response.facets[0]
        self.assertEqual(pc.name, 'Party Code')
        self.assertEqual(pc.choices['D'].count, 1179)
        self.assertEqual(pc.choices['R'].count, 11)
        self.assertEqual(pc.blank_choice.count, 46)
        # {9}
        party_code_facet.include('R')
        response = self.project.compute_facets()
        e = response.facets[1]
        self.assertEqual(e.choices['B'].count, 11)
        # {10}
        party_code_facet.reset()
        ethnicity_facet.reset()
        response = self.project.get_rows()
        self.assertEqual(response.filtered, 6958)
        # {11}
        office_title_facet = TextFacet('Office Title')
        self.project.engine.add_facet(office_title_facet)
        response = self.project.compute_facets()
        self.assertEqual(len(response.facets[2].choices), 76)
        # {12} - XXX not sure how to interpret bins & baseBins yet
        office_level_facet = NumericFacet('Office Level')
        self.project.engine.add_facet(office_level_facet)
        # {13}
        office_level_facet.From = 300   # from reserved word
        office_level_facet.to = 320
        response = self.project.get_rows()
        self.assertEqual(response.filtered, 1907)
        response = self.project.compute_facets()
        ot = response.facets[2]   # Office Title
        self.assertEqual(len(ot.choices), 21)
        self.assertEqual(ot.choices['Chief of Police'].count, 2)
        self.assertEqual(ot.choices['Chief of Police          '].count, 211)
        # {14}
        self.project.engine.remove_all()
        response = self.project.get_rows()
        self.assertEqual(response.filtered, 6958)
        # {15}
        phone_facet = TextFacet('Phone', expression='value[0, 3]')
        self.project.engine.add_facet(phone_facet)
        response = self.project.compute_facets()
        p = response.facets[0]
        self.assertEqual(p.expression, 'value[0, 3]')
        self.assertEqual(p.choices['318'].count, 2331)
        # {16}
        commissioned_date_facet = NumericFacet('Commissioned Date',
            expression='value.toDate().datePart("year")')
        self.project.engine.add_facet(commissioned_date_facet)
        response = self.project.compute_facets()
        cd = response.facets[1]
        self.assertEqual(cd.error_count, 959)
        self.assertEqual(cd.numeric_count, 5999)
        # {17}
        office_description_facet = NumericFacet('Office Description',
            expression=r'value.match(/\D*(\d+)\w\w Rep.*/)[0].toNumber()')
        self.project.engine.add_facet(office_description_facet)
        response = self.project.compute_facets()
        cd = response.facets[2]
        self.assertEqual(cd.min, 0)
        self.assertEqual(cd.max, 110)
        self.assertEqual(cd.numeric_count, 548)


class TutorialTestEditing(RefineTestCase):
    project_file = 'louisiana-elected-officials.csv'

    def test_editing(self):
        # Section "3. Cell Editing": {1}
        self.project.engine.remove_all()    # redundant due to setUp
        # {2}
        response = self.project.text_transform(column='Zip Code 2',
            expression='value.toString()[0, 5]')
        self.assertTrue('6067' in response['historyEntry']['description'])
        # {3} - XXX history
        # {4}
        office_title_facet = TextFacet('Office Title')
        self.project.engine.add_facet(office_title_facet)
        response = self.project.compute_facets()
        self.assertEqual(len(response.facets[0].choices), 76)
        response = self.project.text_transform('Office Title', 'value.trim()')
        self.assertTrue('6895' in response['historyEntry']['description'])
        response = self.project.compute_facets()
        self.assertEqual(len(response.facets[0].choices), 67)
        # {5}
        response = self.project.edit('Office Title',
            'Councilmen', 'Councilman')
        self.assertTrue('13' in response['historyEntry']['description'])
        response = self.project.compute_facets()
        self.assertEqual(len(response.facets[0].choices), 66)
        # {6}
        response = self.project.compute_clusters('Office Title')
        self.assertTrue(not response)
        # {7}
        clusters = self.project.compute_clusters('Office Title', 'knn')
        self.assertEqual(len(clusters), 7)
        self.assertEqual(len(clusters[0]), 2)
        self.assertEqual(clusters[0][0]['value'], 'RSCC Member')
        self.assertEqual(clusters[0][0]['count'], 233)
        # Not strictly necessary to repeat 'Council Member' but a test
        # of mass_edit, and it's also what the front end sends.
        response = self.project.mass_edit('Office Title', [{
            'from': ['Council Member', 'Councilmember'],
            'to': 'Council Member'
        }])
        self.assertTrue('372' in response['historyEntry']['description'])
        response = self.project.compute_facets()
        self.assertEqual(len(response.facets[0].choices), 65)

        # Section "4. Row and Column Editing, Batched Row Deletion"
        # Test doesn't strictly follow the tutorial as the "Browse this
        # cluster" performs a text facet which the server can't complete
        # as it busts its max facet count. The useful work is done with
        # get_rows(). Also, we can facet & select in one; the UI can't.
        # {1}, {2}, {3}, {4}
        clusters = self.project.compute_clusters('Candidate Name')
        for cluster in clusters[0:3]:   # just do a few
            for match in cluster:
                # {2}
                if match['value'].endswith(', '):
                    response = self.project.get_rows(
                        TextFacet('Candidate Name', match['value']))
                    self.assertEqual(len(response.rows), 1)
                    for row in response.rows:
                        response = self.project.star_row(row)
                        self.assertTrue(str(row.index + 1) in
                                        response['historyEntry']['description'])
        # {5}, {6}, {7}
        response = self.project.compute_facets(StarredFacet(True))
        self.assertEqual(len(response.facets[0].choices), 2)    # true & false
        self.assertEqual(response.facets[0].choices[True].count, 3)
        response = self.project.remove_rows()
        self.assertTrue('3 rows' in response['historyEntry']['description'])


class TutorialTestDuplicateDetection(RefineTestCase):
    project_file = 'duplicates.csv'

    def test_duplicate_detection(self):
        # Section "4. Row and Column Editing,
        #             Duplicate Row Detection and Deletion"
        # {7}, {8}
        response = self.project.get_rows(sort_by='email')
        indexes = [r.index for r in response.rows]
        self.assertEqual(indexes, [4, 9, 8, 3, 0, 2, 5, 6, 1, 7])
        # {9}
        response = self.project.reorder_rows()
        self.assertEqual('Reorder rows',
                         response['historyEntry']['description'])
        response = self.project.get_rows()
        indexes = [r.index for r in response.rows]
        self.assertEqual(indexes, range(10))
        # {10}
        response = self.project.add_column('email', 'count',
            'facetCount(value, "value", "email")')
        self.assertTrue('column email by filling 10 rows' in
                        response['historyEntry']['description'])
        response = self.project.get_rows()
        self.assertEqual(self.project.column_order['email'], 0)  # i.e. 1st
        self.assertEqual(self.project.column_order['count'], 1)  # i.e. 2nd
        counts = [r['count'] for r in response.rows]
        self.assertEqual(counts, [2, 2, 1, 1, 3, 3, 3, 1, 2, 2])
        # {11}
        self.assertFalse(self.project.has_records)
        response = self.project.blank_down('email')
        self.assertTrue('Blank down 4 cells' in
                        response['historyEntry']['description'])
        self.assertTrue(self.project.has_records)
        response = self.project.get_rows()
        emails = [1 if r['email'] else 0 for r in response.rows]
        self.assertEqual(emails, [1, 0, 1, 1, 1, 0, 0, 1, 1, 0])
        # {12}
        blank_facet = TextFacet('email', expression='isBlank(value)',
                                selection=True)
        # {13}
        response = self.project.remove_rows(blank_facet)
        self.assertTrue('Remove 4 rows' in
                        response['historyEntry']['description'])
        self.project.engine.remove_all()
        response = self.project.get_rows()
        email_counts = [(row['email'], row['count']) for row in response.rows]
        self.assertEqual(email_counts, [
            (u'arthur.duff@example4.com', 2),
            (u'ben.morisson@example6.org', 1),
            (u'ben.tyler@example3.org', 1),
            (u'danny.baron@example1.com', 3),
            (u'jean.griffith@example5.org', 1),
            (u'melanie.white@example2.edu', 2)
        ])


if __name__ == '__main__':
    unittest.main()