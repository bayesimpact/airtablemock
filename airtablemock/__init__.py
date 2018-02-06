"""A mock for the airtable module to ease unittests."""

import collections
import itertools
import logging
import random
import sys
import unittest

import mock


# A dictionary of all Airtable bases accessed by MockAirtable clients.
_BASES = collections.defaultdict(lambda: collections.defaultdict(collections.OrderedDict))


def clear():
    """Drop all tables from all bases."""
    _BASES.clear()


def patch(target):
    """A function or class decorator to patch the target airtable module with this one."""
    clear()
    return mock.patch(target, new=sys.modules[__name__])


class Airtable(object):
    """Airtable mock client."""

    def __init__(self, base_id=None, api_key=None):
        self.base_id = base_id
        self.api_key = api_key

    def _table(self, table_name):
        return _BASES[self.base_id][table_name]

    def iterate(self, table_name, batch_size=0, filter_by_formula=None, view=None):
        """Iterate over all records of a table."""
        if batch_size:
            logging.info('batch_size ignored in MockAirtableClient.iterate')
        if filter_by_formula:
            raise NotImplementedError(
                'the filter_by_formula feature is not implemented in MockAirtableClient')
        if view:
            logging.warning('view ignored in MockAirtableClient.iterate')

        for key, fields in self._table(table_name).items():
            yield {'id': key, 'fields': fields}

    def get(self, table_name, record_id=None, limit=0, offset=None,
            filter_by_formula=None, view=None):
        """Get a list of records from a table."""
        table = self._table(table_name)

        if record_id:
            return {'id': record_id, 'fields': table[record_id]}

        if filter_by_formula:
            raise NotImplementedError(
                'The filter_by_formula feature is not implemented in airtablemock.')
        if view:
            logging.warning('The view field is ignored in airtablemock.')

        items = table.items()
        if offset:
            items = itertools.islice(items, offset, None)
        if not limit or limit > 100:
            # Default value, on Airtable server.
            limit = 100
        items = itertools.islice(items, limit)

        all_items = list(items)
        response = {
            'records': [{'id': key, 'fields': fields} for key, fields in all_items],
        }
        if len(all_items) + (offset or 0) == len(table):
            response['offset'] = (offset or 0) + len(all_items)
        return response

    def create(self, table_name, data):
        """Create a new record."""
        table = self._table(table_name)
        for unused_i in range(30):
            record_id = _generate_random_id()
            if record_id not in table:
                break
        else:
            raise RuntimeError('Could not generate a new random ID')

        table[record_id] = data
        return {'id': record_id, 'fields': data}

    def update(self, table_name, record_id, data):
        """Update one record partially."""
        table = self._table(table_name)
        table[record_id].update(data)
        return {'id': record_id, 'fields': table[record_id]}

    def update_all(self, table_name, record_id, data):
        """Update one record completely."""
        table = self._table(table_name)
        table[record_id] = data
        return {'id': record_id, 'fields': table[record_id]}

    def delete(self, table_name, record_id):
        """Delete a record."""
        table = self._table(table_name)
        del table[record_id]
        return {'id': record_id, 'deleted': True}


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
