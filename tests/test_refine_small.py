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
        })
        self.assertEqual(len(response.rows), 1)
        # test iteration
        rows = [row for row in response.rows]
        self.assertEqual(rows[0]['name'], 'Danny Baron')
        # test indexing
        self.assertEqual(response.rows[0]['name'], 'Danny Baron')


class RefineProjectTest(unittest.TestCase):
    def setUp(self):
        # Mock out get_models so it doesn't attempt to connect to a server
        self._get_models = refine.RefineProject.get_models
        refine.RefineProject.get_models = lambda me: me
        # Save REFINE_{HOST,PORT} as tests overwrite it
        self._refine_host_port = refine.REFINE_HOST, refine.REFINE_PORT
        refine.REFINE_HOST, refine.REFINE_PORT = '127.0.0.1', '3333'

    def test_server_init(self):
        RP = refine.RefineProject
        p = RP('http://127.0.0.1:3333/project?project=1658955153749')
        self.assertEqual(p.server.server, 'http://127.0.0.1:3333')
        self.assertEqual(p.project_id, '1658955153749')
        p = RP('http://127.0.0.1:3333', '1658955153749')
        self.assertEqual(p.server.server, 'http://127.0.0.1:3333')
        self.assertEqual(p.project_id, '1658955153749')
        p = RP('http://server/varnish/project?project=1658955153749')
        self.assertEqual(p.server.server, 'http://server/varnish')
        self.assertEqual(p.project_id, '1658955153749')
        p = RP('1658955153749')
        self.assertEqual(p.server.server, 'http://127.0.0.1:3333')
        self.assertEqual(p.project_id, '1658955153749')
        refine.REFINE_HOST = '10.0.0.1'
        refine.REFINE_PORT = '80'
        p = RP('1658955153749')
        self.assertEqual(p.server.server, 'http://10.0.0.1')

    def tearDown(self):
        # Restore mocked get_models
        refine.RefineProject.get_models = self._get_models
        # Restore values for REFINE_{HOST,PORT}
        refine.REFINE_HOST, refine.REFINE_PORT = self._refine_host_port


if __name__ == '__main__':
    unittest.main()
