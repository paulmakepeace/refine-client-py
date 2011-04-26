#!/usr/bin/env python
"""
Google Refine history: parsing responses.
"""

# Copyright (c) 2011 Paul Makepeace, Real Programmers. All rights reserved.

import json
import re

class HistoryEntry(object):
    # N.B. e.g. **response['historyEntry'] won't work as keys are unicode :-/
    def __init__(self, id=None, time=None, description=None, **kwargs):
        if id is None:
            raise ValueError('History entry id must be set')
        self.id = id
        self.description = description
        self.time = time
