"""Unit tests for the airtablemock module."""
import unittest

import mock

from airtable import airtable
import airtablemock


class AirtablemockTestCase(airtablemock.TestCase):
    """Unit tests for the Airtablemock class."""

    def test_get(self):
        """Test basic usage of the get method."""

        base = airtable.Airtable()
        base.create('table', {'number': 1})
        base.create('table', {'number': 2})

        records = base.get('table')['records']

        self.assertEqual([1, 2], [record['fields']['number'] for record in records])

    def test_get_by_record_id(self):
        """Test getting one record by its ID."""

        base = airtable.Airtable()
        record = base.create('table', {'number': 1})
        base.create('table', {'number': 2})

        fetched_record = base.get('table', record_id=record['id'])

        self.assertEqual(record, fetched_record)

    def test_iterate(self):
        """Test basic usage of the iterate method."""

        base = airtable.Airtable()
        base.create('table', {'number': 3})
        base.create('table', {'number': 4})

        records = base.iterate('table')

        self.assertEqual([3, 4], [record['fields']['number'] for record in records])

    @mock.patch(airtablemock.random.__name__ + '.randrange')
    def test_create_no_random(self, mock_randrange):
        """Tries creating an entry without randomness."""

        mock_randrange.return_value = 14

        base = airtable.Airtable()
        base.create('table', {'number': 5})
        with self.assertRaises(RuntimeError):
            base.create('table', {'number': 6})

    def test_update(self):
        """Updates a record partially."""

        base = airtable.Airtable()
        record = base.create('table', {'number': 3, 'untouched_field': 'original'})
        record_id = record['id']
        base.update('table', record_id, {'number': 4, 'new_field': 'future'})

        fields = [record['fields'] for record in base.iterate('table')]
        self.assertEqual(
            [{'number': 4, 'untouched_field': 'original', 'new_field': 'future'}], fields)

    def test_update_all(self):
        """Updates a record entirely."""

        base = airtable.Airtable()
        record = base.create('table', {'number': 3, 'untouched_field': 'original'})
        record_id = record['id']
        base.update_all('table', record_id, {'number': 4, 'new_field': 'future'})

        fields = [record['fields'] for record in base.iterate('table')]
        self.assertEqual([{'number': 4, 'new_field': 'future'}], fields)

    def test_delete(self):
        """Delete a record."""

        base = airtable.Airtable()
        record = base.create('table', {'number': 3})
        record_id = record['id']
        base.create('table', {'number': 4})

        base.delete('table', record_id)

        records = base.iterate('table')

        self.assertEqual([4], [record['fields']['number'] for record in records])

    def test_multiple_bases(self):
        """Test using the same table name in 2 different bases."""

        base1 = airtable.Airtable('first-base')
        base1.create('table', {'number': 6})

        base2 = airtable.Airtable('second-base')
        base2.create('table', {'number': 7})

        records = base1.iterate('table')
        self.assertEqual([6], [record['fields']['number'] for record in records])

    def test_multiple_clients(self):
        """Test accessing a table from different clients."""

        base1 = airtable.Airtable('first-base')
        base1.create('table', {'number': 8})

        other_client_base1 = airtable.Airtable('first-base')
        other_client_base1.create('table', {'number': 9})

        records = base1.iterate('table')
        self.assertEqual([8, 9], [record['fields']['number'] for record in records])


class FunctionsTestCase(unittest.TestCase):
    """Tests for top level module functions."""

    def test_clear(self):
        """Basic usage of the clear function."""

        base1 = airtablemock.Airtable('first-base')
        base1.create('table', {'number': 8})

        airtablemock.clear()

        other_client_base1 = airtablemock.Airtable('first-base')
        other_client_base1.create('table', {'number': 9})

        records = base1.iterate('table')
        self.assertEqual([9], [record['fields']['number'] for record in records])


if __name__ == '__main__':
    unittest.main()  # pragma: no cover
