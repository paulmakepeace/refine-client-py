#!/usr/bin/env python
"""
test_history.py
"""

# Copyright (c) 2011 Paul Makepeace, Real Programmers. All rights reserved.

import unittest

from google.refine.history import *


class HistoryTest(unittest.TestCase):
    def test_init(self):
        response = {
            u"code": "ok",
            u"historyEntry": {
                u"id": 1303851435223,
                u"description": "Split 4 cells",
                u"time": "2011-04-26T16:45:08Z"
            }
        }
        he = response['historyEntry']
        entry = HistoryEntry(he['id'], he['time'], he['description'])
        self.assertEqual(entry.id, 1303851435223)
        self.assertEqual(entry.description, 'Split 4 cells')
        self.assertEqual(entry.time, '2011-04-26T16:45:08Z')


if __name__ == '__main__':
    unittest.main()
