"""Unit tests for the airtablemock module."""
import unittest

import mock

import airtablemock


class AirtablemockTestCase(unittest.TestCase):
    """Unit tests for the Airtablemock class."""

    def test_get(self):
        """Test basic usage of the get method."""

        base = airtablemock.Airtable()
        base.create('get-table', {'number': 1})
        base.create('get-table', {'number': 2})

        records = base.get('get-table')['records']

        self.assertEqual([1, 2], [record['fields']['number'] for record in records])

    def test_get_by_record_id(self):
        """Test getting one record by its ID."""

        base = airtablemock.Airtable()
        record = base.create('get-table-record-id', {'number': 1})
        base.create('get-table-record-id', {'number': 2})

        fetched_record = base.get('get-table-record-id', record_id=record['id'])

        self.assertEqual(record, fetched_record)

    def test_iterate(self):
        """Test basic usage of the iterate method."""

        base = airtablemock.Airtable()
        base.create('iterate-table', {'number': 3})
        base.create('iterate-table', {'number': 4})

        records = base.iterate('iterate-table')

        self.assertEqual([3, 4], [record['fields']['number'] for record in records])

    @mock.patch(airtablemock.random.__name__ + '.randrange')
    def test_create_no_random(self, mock_randrange):
        """Tries creating an entry without randomness."""

        mock_randrange.return_value = 14

        base = airtablemock.Airtable()
        base.create('random-table', {'number': 5})
        with self.assertRaises(RuntimeError):
            base.create('random-table', {'number': 6})

    def test_update(self):
        """Updates a record partially."""

        base = airtablemock.Airtable()
        record = base.create('update-table', {'number': 3, 'untouched_field': 'original'})
        record_id = record['id']
        base.update('update-table', record_id, {'number': 4, 'new_field': 'future'})

        fields = [record['fields'] for record in base.iterate('update-table')]
        self.assertEqual(
            [{'number': 4, 'untouched_field': 'original', 'new_field': 'future'}], fields)

    def test_update_all(self):
        """Updates a record entirely."""

        base = airtablemock.Airtable()
        record = base.create('update-all-table', {'number': 3, 'untouched_field': 'original'})
        record_id = record['id']
        base.update_all('update-all-table', record_id, {'number': 4, 'new_field': 'future'})

        fields = [record['fields'] for record in base.iterate('update-all-table')]
        self.assertEqual([{'number': 4, 'new_field': 'future'}], fields)

    def test_delete(self):
        """Delete a record."""

        base = airtablemock.Airtable()
        record = base.create('delete-table', {'number': 3})
        record_id = record['id']
        base.create('delete-table', {'number': 4})

        base.delete('delete-table', record_id)

        records = base.iterate('delete-table')

        self.assertEqual([4], [record['fields']['number'] for record in records])


if __name__ == '__main__':
    unittest.main()  # pragma: no cover