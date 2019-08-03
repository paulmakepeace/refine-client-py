#!/usr/bin/env python
"""
test_tutorial.py

The tests here are based on David Huynh's Refine tutorial at
http://davidhuynh.net/spaces/nicar2011/tutorial.pdf The tests perform all the
Refine actions given in the tutorial (except the web scraping) and verify the
changes expected to be observed explained in the tutorial.

These tests require a connection to a Refine server either at
http://127.0.0.1:3333/ or by specifying environment variables
OPENREFINE_HOST and OPENREFINE_PORT.
"""

# Copyright (c) 2011 Paul Makepeace, Real Programmers. All rights reserved.

import unittest

from google.refine import facet
from tests import refinetest


class TutorialTestFacets(refinetest.RefineTestCase):
    project_file = 'louisiana-elected-officials.csv'
    project_options = {'guessCellValueTypes': True}

    def test_get_rows(self):
        # Section "2. Exploration using Facets": {3}
        response = self.project.get_rows(limit=10)
        self.assertEqual(len(response.rows), 10)
        self.assertEqual(response.limit, 10)
        self.assertEqual(response.total, 6958)
        self.assertEqual(response.filtered, 6958)
        for row in response.rows:
            self.assertFalse(row.flagged)
            self.assertFalse(row.starred)

    def test_facet(self):
        # Section "2. Exploration using Facets": {4}
        party_code_facet = facet.TextFacet(column='Party Code')
        response = self.project.compute_facets(party_code_facet)
        pc = response.facets[0]
        # test look by index same as look up by facet object
        self.assertEqual(pc, response.facets[party_code_facet])
        self.assertEqual(pc.name, 'Party Code')
        self.assertEqual(pc.choices['D'].count, 3700)
        self.assertEqual(pc.choices['N'].count, 15)
        self.assertEqual(pc.blank_choice.count, 1446)
        # {5}, {6}
        engine = facet.Engine(party_code_facet)
        ethnicity_facet = facet.TextFacet(column='Ethnicity')
        engine.add_facet(ethnicity_facet)
        self.project.engine = engine
        response = self.project.compute_facets()
        e = response.facets[ethnicity_facet]
        self.assertEqual(e.choices['B'].count, 1255)
        self.assertEqual(e.choices['W'].count, 4469)
        # {7}
        ethnicity_facet.include('B')
        response = self.project.get_rows()
        self.assertEqual(response.filtered, 1255)
        indexes = [row.index for row in response.rows]
        self.assertEqual(indexes, [1, 2, 3, 4, 6, 12, 18, 26, 28, 32])
        # {8}
        response = self.project.compute_facets()
        pc = response.facets[party_code_facet]
        self.assertEqual(pc.name, 'Party Code')
        self.assertEqual(pc.choices['D'].count, 1179)
        self.assertEqual(pc.choices['R'].count, 11)
        self.assertEqual(pc.blank_choice.count, 46)
        # {9}
        party_code_facet.include('R')
        response = self.project.compute_facets()
        e = response.facets[ethnicity_facet]
        self.assertEqual(e.choices['B'].count, 11)
        # {10}
        party_code_facet.reset()
        ethnicity_facet.reset()
        response = self.project.get_rows()
        self.assertEqual(response.filtered, 6958)
        # {11}
        office_title_facet = facet.TextFacet('Office Title')
        self.project.engine.add_facet(office_title_facet)
        response = self.project.compute_facets()
        self.assertEqual(len(response.facets[2].choices), 76)
        # {12} - XXX not sure how to interpret bins & baseBins yet
        office_level_facet = facet.NumericFacet('Office Level')
        self.project.engine.add_facet(office_level_facet)
        # {13}
        office_level_facet.From = 300   # from reserved word
        office_level_facet.to = 320
        response = self.project.get_rows()
        self.assertEqual(response.filtered, 1907)
        response = self.project.compute_facets()
        ot = response.facets[office_title_facet]
        self.assertEqual(len(ot.choices), 21)
        self.assertEqual(ot.choices['Chief of Police'].count, 2)
        self.assertEqual(ot.choices['Chief of Police          '].count, 211)
        # {14}
        self.project.engine.remove_all()
        response = self.project.get_rows()
        self.assertEqual(response.filtered, 6958)
        # {15}
        phone_facet = facet.TextFacet('Phone', expression='value[0, 3]')
        self.project.engine.add_facet(phone_facet)
        response = self.project.compute_facets()
        p = response.facets[phone_facet]
        self.assertEqual(p.expression, 'value[0, 3]')
        self.assertEqual(p.choices['318'].count, 2331)
        # {16}
        commissioned_date_facet = facet.NumericFacet(
            'Commissioned Date',
            expression='value.toDate().datePart("year")')
        self.project.engine.add_facet(commissioned_date_facet)
        response = self.project.compute_facets()
        cd = response.facets[commissioned_date_facet]
        self.assertEqual(cd.error_count, 959)
        self.assertEqual(cd.numeric_count, 5999)
        # {17}
        office_description_facet = facet.NumericFacet(
            'Office Description',
            expression=r'value.match(/\D*(\d+)\w\w Rep.*/)[0].toNumber()')
        self.project.engine.add_facet(office_description_facet)
        response = self.project.compute_facets()
        od = response.facets[office_description_facet]
        self.assertEqual(od.min, 0)
        self.assertEqual(od.max, 110)
        self.assertEqual(od.numeric_count, 548)


class TutorialTestEditing(refinetest.RefineTestCase):
    project_file = 'louisiana-elected-officials.csv'
    project_options = {'guessCellValueTypes': True}

    def test_editing(self):
        # Section "3. Cell Editing": {1}
        self.project.engine.remove_all()    # redundant due to setUp
        # {2}
        self.project.text_transform(column='Zip Code 2',
                                    expression='value.toString()[0, 5]')
        self.assertInResponse('transform on 6958 cells in column Zip Code 2')
        # {3} - XXX history
        # {4}
        office_title_facet = facet.TextFacet('Office Title')
        self.project.engine.add_facet(office_title_facet)
        response = self.project.compute_facets()
        self.assertEqual(len(response.facets[office_title_facet].choices), 76)
        self.project.text_transform('Office Title', 'value.trim()')
        self.assertInResponse('6895')
        response = self.project.compute_facets()
        self.assertEqual(len(response.facets[office_title_facet].choices), 67)
        # {5}
        self.project.edit('Office Title', 'Councilmen', 'Councilman')
        self.assertInResponse('13')
        response = self.project.compute_facets()
        self.assertEqual(len(response.facets[office_title_facet].choices), 66)
        # {6}
        response = self.project.compute_clusters('Office Title')
        self.assertTrue(not response)
        # {7}
        clusters = self.project.compute_clusters('Office Title', 'knn')
        self.assertEqual(len(clusters), 7)
        first_cluster = clusters[0]
        self.assertEqual(len(first_cluster), 2)
        self.assertEqual(first_cluster[0]['value'], 'DPEC Member at Large')
        self.assertEqual(first_cluster[0]['count'], 6)
        # Not strictly necessary to repeat 'Council Member' but a test
        # of mass_edit, and it's also what the front end sends.
        self.project.mass_edit('Office Title', [{
            'from': ['Council Member', 'Councilmember'],
            'to': 'Council Member'
        }])
        self.assertInResponse('372')
        response = self.project.compute_facets()
        self.assertEqual(len(response.facets[office_title_facet].choices), 65)

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
                        facet.TextFacet('Candidate Name', match['value']))
                    self.assertEqual(len(response.rows), 1)
                    for row in response.rows:
                        self.project.star_row(row)
                        self.assertInResponse(str(row.index + 1))
        # {5}, {6}, {7}
        response = self.project.compute_facets(facet.StarredFacet(True))
        self.assertEqual(len(response.facets[0].choices), 2)    # true & false
        self.assertEqual(response.facets[0].choices[True].count, 2)
        self.project.remove_rows()
        self.assertInResponse('2 rows')


class TutorialTestDuplicateDetection(refinetest.RefineTestCase):
    project_file = 'duplicates.csv'

    def test_duplicate_detection(self):
        # Section "4. Row and Column Editing,
        #             Duplicate Row Detection and Deletion"
        # {7}, {8}
        response = self.project.get_rows(sort_by='email')
        indexes = [row.index for row in response.rows]
        self.assertEqual(indexes, [4, 9, 8, 3, 0, 2, 5, 6, 1, 7])
        # {9}
        self.project.reorder_rows()
        self.assertInResponse('Reorder rows')
        response = self.project.get_rows()
        indexes = [row.index for row in response.rows]
        self.assertEqual(indexes, range(10))
        # {10}
        self.project.add_column(
            'email', 'count', 'facetCount(value, "value", "email")')
        self.assertInResponse('column email by filling 10 rows')
        response = self.project.get_rows()
        self.assertEqual(self.project.column_order['email'], 0)  # i.e. 1st
        self.assertEqual(self.project.column_order['count'], 1)  # i.e. 2nd
        counts = [row['count'] for row in response.rows]
        self.assertEqual(counts, [2, 2, 1, 1, 3, 3, 3, 1, 2, 2])
        # {11}
        self.assertFalse(self.project.has_records)
        self.project.blank_down('email')
        self.assertInResponse('Blank down 4 cells')
        self.assertTrue(self.project.has_records)
        response = self.project.get_rows()
        emails = [1 if row['email'] else 0 for row in response.rows]
        self.assertEqual(emails, [1, 0, 1, 1, 1, 0, 0, 1, 1, 0])
        # {12}
        blank_facet = facet.BlankFacet('email', selection=True)
        # {13}
        self.project.remove_rows(blank_facet)
        self.assertInResponse('Remove 4 rows')
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


class TutorialTestTransposeColumnsIntoRows(refinetest.RefineTestCase):
    project_file = 'us_economic_assistance.csv'

    def test_transpose_columns_into_rows(self):
        # Section "5. Structural Editing, Transpose Columns into Rows"
        # {1}, {2}, {3}
        self.project.transpose_columns_into_rows('FY1946', 64, 'pair')
        self.assertInResponse('64 column(s) starting with FY1946')
        # {4}
        self.project.add_column('pair', 'year', 'value[2,6].toNumber()')
        self.assertInResponse('filling 26185 rows')
        # {5}
        self.project.text_transform(
            column='pair', expression='value.substring(7).toNumber()')
        self.assertInResponse('transform on 26185 cells')
        # {6}
        self.project.rename_column('pair', 'amount')
        self.assertInResponse('Rename column pair to amount')
        # {7}
        self.project.fill_down('country_name')
        self.assertInResponse('Fill down 23805 cells')
        self.project.fill_down('program_name')
        self.assertInResponse('Fill down 23805 cells')
        # spot check of last row for transforms and fill down
        response = self.project.get_rows()
        row10 = response.rows[9]
        self.assertEqual(row10['country_name'], 'Afghanistan')
        self.assertEqual(row10['program_name'],
                         'Department of Defense Security Assistance')
        self.assertEqual(row10['amount'], 113777303)


class TutorialTestTransposeFixedNumberOfRowsIntoColumns(
        refinetest.RefineTestCase):
    project_file = 'fixed-rows.csv'
    project_format = 'text/line-based'
    project_options = {'headerLines': 0}

    def test_transpose_fixed_number_of_rows_into_columns(self):
        if self.server.version not in ('2.0', '2.1'):
            self.project.rename_column('Column 1', 'Column')
        # Section "5. Structural Editing,
        #             Transpose Fixed Number of Rows into Columns"
        # {1}
        self.assertTrue('Column' in self.project.column_order)
        # {8}
        self.project.transpose_rows_into_columns('Column', 4)
        self.assertInResponse('Transpose every 4 cells in column Column')
        # {9} - renaming column triggers a bug in Refine <= 2.1
        if self.server.version not in ('2.0', '2.1'):
            self.project.rename_column('Column 2', 'Address')
            self.project.rename_column('Column 3', 'Address 2')
            self.project.rename_column('Column 4', 'Status')
        # {10}
        self.project.add_column(
            'Column 1', 'Transaction',
            'if(value.contains(" sent "), "send", "receive")')
        self.assertInResponse('Column 1 by filling 4 rows')
        # {11}
        transaction_facet = facet.TextFacet(column='Transaction',
                                            selection='send')
        self.project.engine.add_facet(transaction_facet)
        self.project.compute_facets()
        # {12}, {13}, {14}
        self.project.add_column(
            'Column 1', 'Sender',
            'value.partition(" sent ")[0]')
        # XXX resetting the facet shows data in rows with Transaction=receive
        #     which shouldn't have been possible with the facet.
        self.project.add_column(
            'Column 1', 'Recipient',
            'value.partition(" to ")[2].partition(" on ")[0]')
        self.project.add_column(
            'Column 1', 'Amount',
            'value.partition(" sent ")[2].partition(" to ")[0]')
        # {15}
        transaction_facet.reset().include('receive')
        self.project.get_rows()
        # XXX there seems to be some kind of bug where the model doesn't
        #     match get_rows() output - cellIndex being returned that are
        #     out of range.
        #self.assertTrue(a_row['Sender'] is None)
        #self.assertTrue(a_row['Recipient'] is None)
        #self.assertTrue(a_row['Amount'] is None)
        # {16}
        for column, expression in (
            ('Sender',
             'cells["Column 1"].value.partition(" from ")[2].partition(" on ")[0]'),
            ('Recipient',
             'cells["Column 1"].value.partition(" received ")[0]'),
            ('Amount',
             'cells["Column 1"].value.partition(" received ")[2].partition(" from ")[0]')
        ):
            self.project.text_transform(column, expression)
            self.assertInResponse('2 cells')
        # {17}
        transaction_facet.reset()
        # {18}
        self.project.text_transform('Column 1', 'value.partition(" on ")[2]')
        self.assertInResponse('4 cells')
        # {19}
        self.project.reorder_columns(['Transaction', 'Amount', 'Sender',
                                      'Recipient'])
        self.assertInResponse('Reorder columns')


class TutorialTestTransposeVariableNumberOfRowsIntoColumns(
        refinetest.RefineTestCase):
    project_file = 'variable-rows.csv'
    project_format = 'text/line-based'
    project_options = {'headerLines': 0}

    def test_transpose_variable_number_of_rows_into_columns(self):
        # {20}, {21}
        if self.server.version not in ('2.0', '2.1') :
            self.project.rename_column('Column 1', 'Column')
        self.project.add_column(
            'Column', 'First Line', 'if(value.contains(" on "), value, null)')
        self.assertInResponse('Column by filling 4 rows')
        response = self.project.get_rows()
        first_names = [row['First Line'][0:10] if row['First Line'] else None
                       for row in response.rows]
        self.assertEqual(first_names, [
            'Tom Dalton', None, None, None,
            'Morgan Law', None, None, None, None, 'Eric Batem'])
        # {22}
        self.project.move_column('First Line', 0)
        self.assertInResponse('Move column First Line to position 0')
        self.assertEqual(self.project.column_order['First Line'], 0)
        # {23}
        self.project.engine.mode = 'record-based'
        response = self.project.get_rows()
        self.assertEqual(response.mode, 'record-based')
        self.assertEqual(response.filtered, 4)
        # {24}
        self.project.add_column(
            'Column', 'Status', 'row.record.cells["Column"].value[-1]')
        self.assertInResponse('filling 18 rows')
        # {25}
        self.project.text_transform(
            'Column', 'row.record.cells["Column"].value[1, -1].join("|")')
        self.assertInResponse('18 cells')
        # {26}
        self.project.engine.mode = 'row-based'
        # {27}
        blank_facet = facet.BlankFacet('First Line', selection=True)
        self.project.remove_rows(blank_facet)
        self.assertInResponse('Remove 14 rows')
        self.project.engine.remove_all()
        # {28}
        self.project.split_column('Column', separator='|')
        self.assertInResponse('Split 4 cell(s) in column Column')


class TutorialTestWebScraping(refinetest.RefineTestCase):
    project_file = 'eli-lilly.csv'

    filter_expr_1 = """
        forEach(
            value[2,-2].replace("&#160;", " ").split("), ("),
            v,
            v[0,-1].partition(", '", true).join(":")
        ).join("|")
    """
    filter_expr_2 = """
        filter(
            value.split("|"), p, p.partition(":")[0].toNumber() == %d
        )[0].partition(":")[2]
    """

    def test_web_scraping(self):
        # Section "6. Web Scraping"
        # {1}, {2}
        self.project.split_column('key', separator=':')
        self.assertInResponse('Split 5409 cell(s) in column key')
        self.project.rename_column('key 1', 'page')
        self.assertInResponse('Rename column key 1 to page')
        self.project.rename_column('key 2', 'top')
        self.assertInResponse('Rename column key 2 to top')
        self.project.move_column('line', 'end')
        self.assertInResponse('Move column line to position 2')
        # {3}
        self.project.sorting = facet.Sorting([
            {'column': 'page', 'valueType': 'number'},
            {'column': 'top',  'valueType': 'number'},
        ])
        self.project.reorder_rows()
        self.assertInResponse('Reorder rows')
        first_row = self.project.get_rows(limit=1).rows[0]
        self.assertEqual(first_row['page'], 1)
        self.assertEqual(first_row['top'], 24)
        # {4}
        filter_facet = facet.TextFilterFacet('line', 'ahman')
        rows = self.project.get_rows(filter_facet).rows
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['top'], 106)
        filter_facet.query = 'alvarez'
        rows = self.project.get_rows().rows
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[-1]['top'], 567)
        self.project.engine.remove_all()
        # {5} - tutorial says 'line'; it means 'top'
        line_facet = facet.NumericFacet('top')
        line_facet.to = 100
        self.project.remove_rows(line_facet)
        self.assertInResponse('Remove 775 rows')
        line_facet.From = 570
        line_facet.to = 600
        self.project.remove_rows(line_facet)
        self.assertInResponse('Remove 71 rows')
        line_facet.reset()
        response = self.project.get_rows()
        self.assertEqual(response.filtered, 4563)
        # {6}
        page_facet = facet.TextFacet('page', 1)   # 1 not '1'
        self.project.engine.add_facet(page_facet)
        # {7}
        rows = self.project.get_rows().rows
        # Look for a row with a name in it by skipping HTML
        name_row = [row for row in rows if '<b>' not in row['line']][0]
        self.assertTrue('WELLNESS' in name_row['line'])
        self.assertEqual(name_row['top'], 161)
        line_facet.From = 20
        line_facet.to = 160
        self.project.remove_rows()
        self.assertInResponse('Remove 9 rows')
        self.project.engine.remove_all()
        # {8}
        self.project.text_transform('line', expression=self.filter_expr_1)
        self.assertInResponse('Text transform on 4554 cells in column line')
        # {9} - XXX following is generating Java exceptions
        #filter_expr = self.filter_expr_2 % 16
        #self.project.add_column('line', 'Name', expression=filter_expr)
        # {10} to the final {19} - nothing new in terms of exercising the API.


if __name__ == '__main__':
    unittest.main()
