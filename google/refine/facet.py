#!/usr/bin/env python
"""
Google Refine Facets, Engine, and Facet Responses.
"""

# Copyright (c) 2011 Paul Makepeace, Real Programmers. All rights reserved.

import json
import re


def to_camel(attr):
    """convert this_attr_name to thisAttrName."""
    # Do lower case first letter
    return (attr[0].lower() +
            re.sub(r'_(.)', lambda x: x.group(1).upper(), attr[1:]))

def from_camel(attr):
    """convert thisAttrName to this_attr_name."""
    # Don't add an underscore for capitalized first letter
    return re.sub(r'(?<=.)([A-Z])', lambda x: '_' + x.group(1), attr).lower()


class Facet(object):
    def __init__(self, column, type, expression='value', **options):
        self.type = type
        self.name = column
        self.column_name = column
        self.expression = expression
        for k, v in options.items():
            setattr(self, k, v)

    def as_dict(self):
        return dict([(to_camel(k), v) for k, v in self.__dict__.items()
                     if v is not None])


class TextFilterFacet(Facet):
    def __init__(self, column, query, **options):
        super(TextFilterFacet, self).__init__(column, query=query, type='text',
                                              mode='text', **options)


class TextFacet(Facet):
    def __init__(self, column, selection=None, omit_blank=False, omit_error=False, select_blank=False, select_error=False, invert=False, **options):
        super(TextFacet, self).__init__(
            column,
            type='list',
            omit_blank=omit_blank,
            omit_error=omit_error,
            select_blank=select_blank,
            select_error=select_error,
            invert=invert,
            **options)
        self.selection = []
        if selection is None:
            selection = []
        elif not isinstance(selection, list):
            selection = [selection]
        for value in selection:
            self.include(value)

    def include(self, value):
        for s in self.selection:
            if s['v']['v'] == value:
                return
        self.selection.append({'v': {'v': value, 'l': value}})
        return self

    def exclude(self, value):
        self.selection = [s for s in self.selection
                          if s['v']['v'] != value]
        return self

    def reset(self):
        self.selection = []
        return self


class BoolFacet(TextFacet):
    def __init__(self, column, expression=None, selection=None):
        if selection is not None and not isinstance(selection, bool):
            raise ValueError('selection must be True or False.')
        if expression is None:
            raise ValueError('Missing expression')
        super(BoolFacet, self).__init__(column,
            expression=expression, selection=selection)


class StarredFacet(BoolFacet):
    def __init__(self, selection=None):
        super(StarredFacet, self).__init__('',
            expression='row.starred', selection=selection)


class FlaggedFacet(BoolFacet):
    def __init__(self, selection=None):
        super(FlaggedFacet, self).__init__('',
            expression='row.flagged', selection=selection)


class BlankFacet(BoolFacet):
    def __init__(self, column, selection=None):
        super(BlankFacet, self).__init__(column,
            expression='isBlank(value)', selection=selection)


# Capitalize 'From' to get around python's reserved word.
class NumericFacet(Facet):
    def __init__(self, column, From=None, to=None, select_blank=True, select_error=True, select_non_numeric=True, select_numeric=True, **options):
        super(NumericFacet, self).__init__(
            column,
            type='range',
            select_blank=select_blank,
            select_error=select_error,
            select_non_numeric=select_non_numeric,
            select_numeric=select_numeric,
            From=From,
            to=to,
            **options)


class FacetResponse(object):
    def __init__(self, facet):
        for k, v in facet.items():
            if isinstance(k, bool) or isinstance(k, basestring):
                setattr(self, from_camel(k), v)
        self.choices = {}
        class FacetChoice(object):
            def __init__(self, c):
                self.count = c['c']
                self.selected = c['s']

        if 'choices' in facet:
            for choice in facet['choices']:
                self.choices[choice['v']['v']] = FacetChoice(choice)
            if 'blankChoice' in facet:
                self.blank_choice = FacetChoice(facet['blankChoice'])
            else:
                self.blank_choice = None
        if 'bins' in facet:
            self.bins = facet['bins']
            self.base_bins = facet['baseBins']


class FacetsResponse(object):
    def __init__(self, facets):
        self.facets = [FacetResponse(f) for f in facets['facets']]
        self.mode = facets['mode']


class Engine(object):
    def __init__(self, facets=None, mode='row-based'):
        self.set_facets(facets)
        self.mode = mode

    def set_facets(self, facets=None):
        if facets is None:
            facets = []
        elif not isinstance(facets, list):
            facets = [facets]
        self.facets = facets

    def as_dict(self):
        return {
            'facets': [f.as_dict() for f in self.facets],  # XXX how with json?
            'mode': self.mode,
        }

    def __len__(self):
        return len(self.facets)

    def as_json(self):
        return json.dumps(self.as_dict())

    def add_facet(self, facet):
        self.facets.append(facet)

    def remove_all(self):
        self.facets = []

    def reset_all(self):
        for facet in self.facets:
            facet.reset()


class Sorting(object):
    """Class representing the current sorting order for a project.

    Used in RefineProject.get_rows()"""
    def __init__(self, criteria=None):
        self.criteria = []
        if criteria is None:
            criteria = []
        if not isinstance(criteria, list):
            criteria = [criteria]
        for criterion in criteria:
            if isinstance(criterion, basestring):
                criterion = {
                    'column': criterion,
                    'valueType': 'string',
                    'caseSensitive': False,
                }
                criterion.setdefault('reverse', False)
                criterion.setdefault('errorPosition', 1)
                criterion.setdefault('blankPosition', 2)
            self.criteria.append(criterion)

    def as_json(self):
        return json.dumps({'criteria': self.criteria})

    def __len__(self):
        return len(self.criteria)
