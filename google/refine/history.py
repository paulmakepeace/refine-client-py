#!/usr/bin/env python
"""
OpenRefine history: parsing responses.
"""

# Copyright (c) 2011 Paul Makepeace, Real Programmers. All rights reserved.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>


class HistoryEntry(object):
    # N.B. e.g. **response['historyEntry'] won't work as keys are unicode :-/
    #noinspection PyUnusedLocal
    def __init__(self, history_entry_id=None, time=None, description=None, **kwargs):
        if history_entry_id is None:
            raise ValueError('History entry id must be set')
        self.id = history_entry_id
        self.description = description
        self.time = time
