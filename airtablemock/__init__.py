"""A mock for the airtable module to ease unittests."""

import collections
import itertools
import json
import logging
import random
import re
import sys
import unittest
from urllib import parse
import warnings

import mock
from parsimonious import exceptions
from parsimonious import grammar
import requests


_API_URL = 'https://api.airtable.com/v0/'

# A dictionary of all Airtable bases accessed by MockAirtable clients.
_BASES = collections.defaultdict(lambda: collections.defaultdict(collections.OrderedDict))

# A dictionary of all views predicates grouped by base ID and table name.
_VIEWS = collections.defaultdict(lambda: collections.defaultdict(collections.OrderedDict))


def clear():
    """Drop all tables from all bases."""
    _BASES.clear()
    _VIEWS.clear()


def patch(target):
    """A function or class decorator to patch the target airtable module with this one."""
    clear()
    return mock.patch(target, new=sys.modules[__name__])


class Airtable(object):
    """Airtable mock client."""

    def __init__(self, base_id=None, api_key=None, dict_class=collections.OrderedDict):
        self.base_id = base_id
        self.api_key = api_key
        self._dict_class = dict_class

    def _table(self, table_name, must_exist=True):
        if must_exist and table_name not in _BASES[self.base_id]:
            logging.warning(
                'Testers, before accessing a table it should be created, probably in your '
                'test code. Either:\n'
                ' - insert a record using\n'
                '   airtable.Airtable({base}).create({table}, record)\n'
                ' - create an empty table using\n'
                '   airtablemock.create_empty_table({base}, {table})'.format(
                    base=repr(self.base_id), table=repr(table_name)))
            response = requests.Response()
            response.status_code = 404
            response.reason = 'Not Found'
            response.url = '{}{}/{}'.format(
                _API_URL, parse.quote(self.base_id or ''), parse.quote(table_name or ''))
            response.raise_for_status()
        return _BASES[self.base_id][table_name]

    def _create_record(self, id, fields):
        return self._dict_class([('id', id), ('fields', fields)])

    def _filter_dict(self, values, fields):
        if fields:
            return self._dict_class([
                (key, value)
                for key, value in values.items()
                if key in fields
            ])
        return values

    def iterate(
            self, table_name, batch_size=0, filter_by_formula=None, view=None, max_records=0,
            fields=()):
        """Iterate over all records of a table."""
        if batch_size:
            logging.info('batch_size ignored in MockAirtableClient.iterate')

        items = self._table(table_name).items()

        if view:
            if _VIEWS:
                view_predicate = _VIEWS[self.base_id][table_name].get(view)
                if not view_predicate:
                    response = requests.Response()
                    response.status_code = 422
                    response.reason = 'Unprocessable Entity'
                    response.url = '{}{}/{}?view={}'.format(
                        _API_URL, parse.quote(self.base_id or ''), parse.quote(table_name or ''),
                        parse.quote(view))
                    response.raise_for_status()
                items = filter(view_predicate, items)
            else:
                logging.warning(
                    'The view field is ignored as no views were created in airtablemock.')

        if filter_by_formula:
            items = filter(_create_predicate(filter_by_formula), items)

        if max_records:
            items = itertools.islice(items, 0, max_records)

        for record_id, values in items:
            yield self._create_record(record_id, self._filter_dict(values, fields))

    def get(self, table_name, record_id=None, limit=0, offset=None,
            filter_by_formula=None, view=None, max_records=0, fields=()):
        """Get a list of records from a table.

        The view parameter is handled specifically compared to the real API: by
        default it's just ignored (the full table is used), however as soon as
        the create_view method is used, the view must exists or this function
        will return an error (the same error that Airtable would respond in
        case of a incorrect view).
        """
        if record_id:
            return self._create_record(
                record_id, self._filter_dict(self._table(table_name)[record_id], fields))

        items = self.iterate(
            table_name, filter_by_formula=filter_by_formula, view=view, max_records=max_records,
            fields=fields)

        if offset:
            items = itertools.islice(items, offset, None)

        if not limit or limit > 100:
            # Default value, on Airtable server.
            limit = 100
        items_limited = itertools.islice(items, limit)

        all_items = list(items_limited)
        response = {'records': all_items}
        try:
            next(items)
            # TODO(pascal): Use a record ID offset, not a number...
            response['offset'] = (offset or 0) + len(all_items)
        except StopIteration:
            ...
        return response

    def create(self, table_name, data):
        """Create a new record."""
        table = self._table(table_name, must_exist=False)
        for unused_i in range(30):
            record_id = _generate_random_id()
            if record_id not in table:
                break
        else:
            raise RuntimeError('Could not generate a new random ID')

        table[record_id] = data
        return self._create_record(record_id, self._dict_class(data))

    def update(self, table_name, record_id, data):
        """Update one record partially."""
        table = self._table(table_name)
        table[record_id].update(data)
        return self._create_record(record_id, table[record_id])

    def update_all(self, table_name, record_id, data):
        """Update one record completely."""
        table = self._table(table_name)
        table[record_id] = self._dict_class(data)
        return self._create_record(record_id, table[record_id])

    def delete(self, table_name, record_id):
        """Delete a record."""
        table = self._table(table_name)
        del table[record_id]
        return self._dict_class([('id', record_id), ('deleted', True)])

    def create_view(self, table_name, view_name, formula):
        """Creates a view on a given table.

        This is not part of the official API, so you should only use this in tests.
        """
        warnings.warn('Airtable.create_view is deprecated. Use airtablemock.create_view instead.')
        create_view(self.base_id, table_name, view_name, formula)


# See grammar at
# https://support.airtable.com/hc/en-us/articles/203255215-Formula-field-reference
_FORMULA_GRAMMAR = grammar.Grammar(
    r'''
    expression  = simple_expression / function_call
    simple_expression = field_or_value blank operator blank field_or_value
    function_call = binary_function "(" expression "," blank expression ")"
    field_or_value = field / numeric / text
    blank       = ~"\s*"
    field       = ~"[a-z_]\w*"i
    operator    = "=" / "!=" / "<=" / ">=" / "<" / ">"
    numeric     = "-"? positive_number ("." positive_number)?
    positive_number = ~"[0-9]+"
    text        = "\"" quoted_text "\""
    quoted_text = ~"([^\"\\\\]|\\\\.)*"
    binary_function = "AND" / "OR"
    '''
)


def _create_predicate(formula):
    try:
        formula_parsed = _FORMULA_GRAMMAR.parse(formula)
    except exceptions.ParseError:
        raise NotImplementedError(
            'The filter_by_formula feature is not implemented in airtablemock for this formula {}.'
            .format(formula))
    return _create_predicate_from_node(formula_parsed)


def _create_predicate_from_node(formula):
    if formula.expr_name == 'expression' and len(formula.children) == 1:
        formula = formula.children[0]

    if formula.expr_name == 'simple_expression' and len(formula.children) == 5:
        operator = formula.children[2].text
        get_a = _create_value_getter_from_node(formula.children[0])
        get_b = _create_value_getter_from_node(formula.children[-1])
        if operator == '=':
            return lambda *args: get_a(*args) == get_b(*args)
        if operator == '!=':
            return lambda *args: get_a(*args) != get_b(*args)
        if operator == '<':
            return lambda *args: get_a(*args) < get_b(*args)
        if operator == '<=':
            return lambda *args: get_a(*args) <= get_b(*args)
        if operator == '>':
            return lambda *args: get_a(*args) > get_b(*args)
        if operator == '>=':
            return lambda *args: get_a(*args) >= get_b(*args)
        raise NotImplementedError(
            'Operator {} not supported yet in filter_by_formula'.format(operator))

    if formula.expr_name == 'function_call':
        funcname = formula.children[0].text
        pred1 = _create_predicate_from_node(formula.children[2])
        pred2 = _create_predicate_from_node(formula.children[5])
        if funcname == 'AND':
            return lambda *args: pred1(*args) and pred2(*args)
        if funcname == 'OR':
            return lambda *args: pred1(*args) or pred2(*args)
        raise NotImplementedError(
            'Function "{}" not supported yet in filter_by_formula'.format(funcname))

    raise NotImplementedError(
        'Grammar not supported yet in filter_by_formula: {}'.format(formula.text))


def _create_value_getter_from_node(node):
    if node.expr_name == 'field_or_value' and len(node.children) == 1:
        node = node.children[0]

    if node.expr_name == 'field':
        fieldname = node.text
        return lambda key_fields: key_fields[1].get(fieldname)

    value = json.loads(node.text)
    return lambda *args: value


class TestCase(unittest.TestCase):
    """A base class to run independant unit tests using airtablemock.

    Use this class as a base class for your test, and then access airtable as
    you would normally.
    """

    def setUp(self):
        super(TestCase, self).setUp()
        patcher = mock.patch('airtable.airtable.Airtable', Airtable)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(clear)


def _generate_random_id():
    return 'rec%x' % random.randrange(0x10000000000)


def create_empty_table(base_id, table_name):
    """Create an empty table in the given base."""

    if table_name in _BASES[base_id]:
        raise ValueError('Table "{}" already exists in "{}"'.format(table_name, base_id))
    _BASES[base_id].__missing__(table_name)


def create_view(base_id, table_name, view_name, formula):
    """Creates a view on a given table."""

    if table_name not in _BASES[base_id]:
        raise ValueError('Table "{}" does not exist in "{}" yet'.format(table_name, base_id))
    if view_name in _VIEWS[base_id][table_name]:
        raise ValueError(
            'View "{}" already exists in "{}:{}"'.format(view_name, base_id, table_name))
    # TODO(pascal): Implement the different sorting.
    _VIEWS[base_id][table_name][view_name] = _create_predicate(formula)
