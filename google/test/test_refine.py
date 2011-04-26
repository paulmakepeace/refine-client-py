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
    project_file_options = {}
    project = None
    # Section "2. Exploration using Facets": {1}, {2}
    def setUp(self):
        self.server = RefineServer()
        self.refine = Refine(self.server)
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


class TutorialTestTransposeColumnsIntoRows(RefineTestCase):
    project_file = 'us_economic_assistance.csv'

    def test_transpose_columns_into_rows(self):
        # Section "5. Structural Editing, Transpose Columns into Rows"
        # {1}, {2}, {3}
        response = self.project.transpose_columns_into_rows(
            'FY1946', 64, 'pair')
        self.assertTrue('64 column(s) starting with FY1946' in
                        response['historyEntry']['description'])
        # {4}
        response = self.project.add_column('pair', 'year',
            'value[2,6].toNumber()')
        self.assertTrue('filling 26185 rows' in
                        response['historyEntry']['description'])
        # {5}
        response = self.project.text_transform(column='pair',
            expression='value.substring(7).toNumber()')
        self.assertTrue('transform on 26185 cells' in
                        response['historyEntry']['description'])
        # {6}
        response = self.project.rename_column('pair', 'amount')
        self.assertTrue('Rename column pair to amount' in
                        response['historyEntry']['description'])
        # {7}
        response = self.project.fill_down('country_name')
        self.assertTrue('Fill down 23805 cells' in
                        response['historyEntry']['description'])
        response = self.project.fill_down('program_name')
        self.assertTrue('Fill down 23805 cells' in
                        response['historyEntry']['description'])
        # spot check of last row for transforms and fill down
        response = self.project.get_rows()
        row10 = [r for r in response.rows][9]
        self.assertEqual(row10['country_name'], 'Afghanistan')
        self.assertEqual(row10['program_name'],
                        'Department of Defense Security Assistance')
        self.assertEqual(row10['amount'], 113777303)


class TutorialTestTransposeFixedNumbeOfRowsIntoColumns(RefineTestCase):
    project_file = 'fixed-rows.csv'
    project_file_options = {'split_into_columns': False,
                            'header_lines': 0}
    def test_transpose_fixed_number_of_rows_into_columns(self):
        # Section "5. Structural Editing,
        #             Transpose Fixed Number of Rows into Columns"
        # {1}
        self.assertTrue('Column' in self.project.column_order)
        # {8}
        response = self.project.transpose_rows_into_columns('Column', 4)
        self.assertTrue('Transpose every 4 cells in column Column' in
                        response['historyEntry']['description'])
        # {9} - renaming column triggers a bug in Refine
        # {10}
        response = self.project.add_column('Column 1', 'Transaction',
            'if(value.contains(" sent "), "send", "receive")')
        self.assertTrue('Column 1 by filling 4 rows' in
                        response['historyEntry']['description'])
        # {11}
        transaction_facet = TextFacet(column='Transaction', selection='send')
        self.project.engine.add_facet(transaction_facet)
        self.project.compute_facets()
        # {12}, {13}, {14}
        response = self.project.add_column('Column 1', 'Sender',
            'value.partition(" sent ")[0]')
        # XXX resetting the facet shows data in rows with Transaction=receive
        #     which shouldn't have been possible with the facet.
        response = self.project.add_column('Column 1', 'Recipient',
                'value.partition(" to ")[2].partition(" on ")[0]')
        response = self.project.add_column('Column 1', 'Amount',
                'value.partition(" sent ")[2].partition(" to ")[0]')
        # {15}
        transaction_facet.reset().include('receive')
        response = self.project.get_rows()
        # XXX there seems to be some kind of bug where the model doesn't
        #     match get_rows() output - cellIndex being returned that are
        #     out of range.
        #self.assertTrue(a_row['Sender'] is None)
        #self.assertTrue(a_row['Recipient'] is None)
        #self.assertTrue(a_row['Amount'] is None)
        # {16}
        for column, expression in (
            ('Sender',
             'cells["Column 1"].value.partition(" from ")[2]'
              '.partition(" on ")[0]'),
            ('Recipient',
             'cells["Column 1"].value.partition(" received ")[0]'),
            ('Amount',
             'cells["Column 1"].value.partition(" received ")[2]'
             '.partition(" from ")[0]')
        ):
            response = self.project.text_transform(column, expression)
            self.assertTrue('2 cells' in
                            response['historyEntry']['description'])
        # {17}
        transaction_facet.reset()
        # {18}
        response = self.project.text_transform('Column 1',
                                               'value.partition(" on ")[2]')
        self.assertTrue('4 cells' in
                        response['historyEntry']['description'])
        # {19}
        response = self.project.reorder_columns([
            'Transaction', 'Amount', 'Sender', 'Recipient'])
        self.assertEqual('Reorder columns',
                         response['historyEntry']['description'])


class TutorialTestTransposeVariableNumbeOfRowsIntoColumns(RefineTestCase):
    project_file = 'variable-rows.csv'
    project_file_options = {'split_into_columns': False,
                            'header_lines': 0}

    def test_transpose_variable_number_of_rows_into_columns(self):
        # {20}, {21}
        response = self.project.add_column('Column', 'First Line',
            'if(value.contains(" on "), value, null)')
        self.assertTrue('Column by filling 4 rows' in
                        response['historyEntry']['description'])
        response = self.project.get_rows()
        first_names = [row['First Line'][0:10] if row['First Line'] else None
                       for row in response.rows]
        self.assertEqual(first_names, ['Tom Dalton', None, None, None,
            'Morgan Law', None, None, None, None, 'Eric Batem'])
        # {22}
        response = self.project.move_column('First Line', 0)
        self.assertTrue('Move column First Line to position 0' in
                        response['historyEntry']['description'])
        self.assertEqual(self.project.column_order['First Line'], 0)
        # {23}
        self.project.engine.mode = 'record-based'
        response = self.project.get_rows()
        self.assertEqual(response.mode, 'record-based')
        self.assertEqual(response.filtered, 4)
        # {24}
        response = self.project.add_column('Column', 'Status',
            'row.record.cells["Column"].value[-1]')
        self.assertTrue('filling 18 rows' in
                        response['historyEntry']['description'])
        # {25}
        response = self.project.text_transform('Column',
            'row.record.cells["Column"].value[1, -1].join("|")')
        self.assertTrue('18 cells' in
                        response['historyEntry']['description'])
        # {26}
        self.project.engine.mode = 'row-based'
        # {27}
        blank_facet = TextFacet('First Line', expression='isBlank(value)',
                                selection=True)
        response = self.project.remove_rows(blank_facet)
        self.assertEqual('Remove 14 rows',
                         response['historyEntry']['description'])
        self.project.engine.remove_all()
        # {28}
        'Split 4 cell(s) in column Column into several columns by separator'
        response = self.project.split_column('Column', separator='|')
        self.assertTrue('Split 4 cell(s) in column Column' in
                        response['historyEntry']['description'])


if __name__ == '__main__':
    unittest.main()