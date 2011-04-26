#!/usr/bin/env python
"""
test_refine_small.py
"""

# Copyright (c) 2011 Paul Makepeace, Real Programmers. All rights reserved.

import unittest

from google.refine import refine


class RefineRowsTest(unittest.TestCase):
    def test_rows_response(self):
        rr = refine.RowsResponseFactory({
            u'gender': 3, u'state': 2, u'purchase': 4, u'email': 0,
            u'name': 1})
        response = rr({
            u'rows': [{
                u'i': 0,
                u'cells': [
                    {u'v': u'danny.baron@example1.com'},
                    {u'v': u'Danny Baron'},
                    {u'v': u'CA'},
                    {u'v': u'M'},
                    {u'v': u'TV'}
                ],
                u'starred': False,
                u'flagged': False
            }],
            u'start': 0,
            u'limit': 1,
            u'mode': u'row-based',
            u'filtered': 10,
            u'total': 10,
            u'pool': {
                u'recons': {},
                u'reconCandidates': {}
            }
        })
        self.assertEqual(len(response.rows), 1)
        # test iteration
        rows = [row for row in response.rows]
        self.assertEqual(rows[0]['name'], 'Danny Baron')
        # test indexing
        self.assertEqual(response.rows[0]['name'], 'Danny Baron')


if __name__ == '__main__':
    unittest.main()
