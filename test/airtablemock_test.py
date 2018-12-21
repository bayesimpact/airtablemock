"""Unit tests for the airtablemock module."""

import re
import typing
import unittest

import mock

from airtable import airtable
import airtablemock
from requests import exceptions


class AirtablemockTestCase(airtablemock.TestCase):
    """Unit tests for the Airtablemock class."""

    def test_get(self) -> None:
        """Test basic usage of the get method."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 1})
        base.create('table', {'number': 2})

        records = base.get('table')['records']

        self.assertEqual([1, 2], [record['fields']['number'] for record in records])

    def test_get_by_record_id(self) -> None:
        """Test getting one record by its ID."""

        base = airtable.Airtable('base', '')
        record = base.create('table', {'number': 1})
        base.create('table', {'number': 2})

        fetched_record = base.get('table', record_id=record['id'])

        self.assertEqual(record, fetched_record)

    @mock.patch('logging.warning')
    def test_get_missing_table(self, mock_warning: mock.MagicMock) -> None:
        """Test getting a table that does not exist."""

        base = airtable.Airtable('base', '')

        match_exception = '404 .* Not Found .* {}'.format(
            re.escape('{}base/table'.format(airtable.API_URL % airtable.API_VERSION)))
        with self.assertRaisesRegex(exceptions.HTTPError, match_exception):
            base.get('table')

        mock_warning.assert_called_once()
        self.assertIn('create_empty_table', mock_warning.call_args[0][0])

    @mock.patch('logging.warning')
    def test_get_empty_table(self, mock_warning: mock.MagicMock) -> None:
        """Test getting an empty table."""

        base = airtable.Airtable('base', '')

        airtablemock.create_empty_table('base', 'table')
        base.get('table')

        mock_warning.assert_not_called()

    def test_creating_empty_table_twice(self) -> None:
        """Test creating an empty table twice."""

        airtablemock.create_empty_table('base', 'table')
        airtablemock.create_empty_table('base', 'table2')
        airtablemock.create_empty_table('base2', 'table')

        with self.assertRaises(ValueError):
            airtablemock.create_empty_table('base', 'table')

    def test_filter_by_formula_equal(self) -> None:
        """Test filtering by formula with a simple equal."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 1, 'filter': 'yes'})
        base.create('table', {'number': 2, 'filter': 'no'})
        base.create('table', {'number': 3, 'filter': 'yes'})

        records = base.get('table', filter_by_formula='filter = "yes"')['records']

        self.assertEqual([1, 3], [record['fields']['number'] for record in records])

    def test_filter_by_formula_greater(self) -> None:
        """Test filtering by formula with a numerical greater than."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 1, 'filter': 'yes'})
        base.create('table', {'number': 2, 'filter': 'no'})
        base.create('table', {'number': 3, 'filter': 'yes'})

        records = base.get('table', filter_by_formula='number >= 1.99')['records']

        self.assertEqual([2, 3], [record['fields']['number'] for record in records])

    def test_filter_by_formula_and(self) -> None:
        """Test filtering by formula using AND."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 1, 'filter': 'yes', 'other': 'a'})
        base.create('table', {'number': 2, 'filter': 'no', 'other': 'a'})
        base.create('table', {'number': 3, 'filter': 'yes', 'other': 'b'})

        records = base.get(
            'table', filter_by_formula='AND(filter = "yes", other = "b")')['records']

        self.assertEqual([3], [record['fields']['number'] for record in records])

    def test_filter_by_formula_offset(self) -> None:
        """Test filtering by formula and using an offset."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 1, 'filter': 'no'})
        base.create('table', {'number': 2, 'filter': 'yes'})
        base.create('table', {'number': 3, 'filter': 'yes'})

        # Note that the offset should be applied after the filter.
        records = base.get('table', filter_by_formula='filter = "yes"', offset=1)['records']

        self.assertEqual([3], [record['fields']['number'] for record in records])

    def test_filter_by_formula_quotes(self) -> None:
        """Test filtering by formula using a string with quotes."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 1, 'filter': '\'"(=,)}{'})
        base.create('table', {'number': 2, 'filter': 'no'})
        base.create('table', {'number': 3, 'filter': 'yes'})

        records = base.get('table', filter_by_formula='filter = "\'\\"(=,)}{"')['records']

        self.assertEqual([1], [record['fields']['number'] for record in records])

    def test_get_limit(self) -> None:
        """Test the limit feature of the get method."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 1})
        base.create('table', {'number': 2})
        base.create('table', {'number': 3})
        base.create('table', {'number': 4})
        base.create('table', {'number': 5})

        response = base.get('table', limit=2)

        self.assertEqual([1, 2], [record['fields']['number'] for record in response['records']])
        self.assertEqual(2, response.get('offset'))

        response = base.get('table', limit=2, offset=2)

        self.assertEqual([3, 4], [record['fields']['number'] for record in response['records']])
        self.assertEqual(4, response.get('offset'))

        response = base.get('table', limit=2, offset=4)

        self.assertEqual([5], [record['fields']['number'] for record in response['records']])
        self.assertNotIn('offset', response)

    def test_view(self) -> None:
        """Test calling records of a view."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 1, 'filter': 'no'})
        base.create('table', {'number': 2, 'filter': 'yes'})
        base.create('table', {'number': 3, 'filter': 'yes'})

        base.create_view('table', 'filtered view', 'filter = "yes"')

        records = base.get('table', view='filtered view')['records']
        self.assertEqual([2, 3], [record['fields']['number'] for record in records])

    @mock.patch('logging.warning')
    def test_view_never_created(self, mock_logging: mock.MagicMock) -> None:
        """Test calling records of a view without ever creating any views."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 1, 'filter': 'no'})
        base.create('table', {'number': 2, 'filter': 'yes'})
        base.create('table', {'number': 3, 'filter': 'yes'})

        records = base.get('table', view='filtered view')['records']
        self.assertEqual([1, 2, 3], [record['fields']['number'] for record in records])

        mock_logging.assert_called_once_with(
            'The view field is ignored as no views were created in airtablemock.')

    def test_view_and_filter(self) -> None:
        """Test filtering records of a view."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 1, 'filter': 'no'})
        base.create('table', {'number': 2, 'filter': 'yes'})
        base.create('table', {'number': 3, 'filter': 'yes'})

        base.create_view('table', 'filtered view', 'filter = "yes"')

        records = base.get('table', view='filtered view', filter_by_formula='number > 2')['records']
        self.assertEqual([3], [record['fields']['number'] for record in records])

    def test_unknown_view(self) -> None:
        """Try accessing an unknown view, while views are enabled."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 1, 'filter': 'no'})

        base.create_view('table', 'existing view', 'filter = "yes"')

        match_exception = '422 .* Unprocessable Entity .* {}'.format(
            re.escape('{}base/table?view=non%20existing%20view'.format(
                airtable.API_URL % airtable.API_VERSION)))
        with self.assertRaisesRegex(exceptions.HTTPError, match_exception):
            base.get('table', view='non existing view')

    def test_iterate(self) -> None:
        """Test basic usage of the iterate method."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 3})
        base.create('table', {'number': 4})

        records = base.iterate('table')

        self.assertEqual([3, 4], [record['fields']['number'] for record in records])

    def test_iterate_filter_by_formula(self) -> None:
        """Test filtering by formula on the iterate method."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 3})
        base.create('table', {'number': 4})

        records = base.iterate('table', filter_by_formula='number > 3')

        self.assertEqual([4], [record['fields']['number'] for record in records])

    def test_iterate_view(self) -> None:
        """Test iterating a view."""

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 3})
        base.create('table', {'number': 4})
        base.create_view('table', 'my-view', 'number < 4')

        records = base.iterate('table', view='my-view')

        self.assertEqual([3], [record['fields']['number'] for record in records])

    @mock.patch('random.randrange')
    def test_create_no_random(self, mock_randrange: mock.MagicMock) -> None:
        """Tries creating an entry without randomness."""

        mock_randrange.return_value = 14

        base = airtable.Airtable('base', '')
        base.create('table', {'number': 5})
        with self.assertRaises(RuntimeError):
            base.create('table', {'number': 6})

    def test_update(self) -> None:
        """Updates a record partially."""

        base = airtable.Airtable('base', '')
        record = base.create('table', {'number': 3, 'untouched_field': 'original'})
        record_id = record['id']
        base.update('table', record_id, {'number': 4, 'new_field': 'future'})

        fields = [record['fields'] for record in base.iterate('table')]
        self.assertEqual(
            [{'number': 4, 'untouched_field': 'original', 'new_field': 'future'}], fields)

    def test_update_all(self) -> None:
        """Updates a record entirely."""

        base = airtable.Airtable('base', '')
        record = base.create('table', {'number': 3, 'untouched_field': 'original'})
        record_id = record['id']
        base.update_all('table', record_id, {'number': 4, 'new_field': 'future'})

        fields = [record['fields'] for record in base.iterate('table')]
        self.assertEqual([{'number': 4, 'new_field': 'future'}], fields)

    def test_delete(self) -> None:
        """Delete a record."""

        base = airtable.Airtable('base', '')
        record = base.create('table', {'number': 3})
        record_id = record['id']
        base.create('table', {'number': 4})

        base.delete('table', record_id)

        records = base.iterate('table')

        self.assertEqual([4], [record['fields']['number'] for record in records])

    def test_multiple_bases(self) -> None:
        """Test using the same table name in 2 different bases."""

        base1 = airtable.Airtable('first-base', '')
        base1.create('table', {'number': 6})

        base2 = airtable.Airtable('second-base', '')
        base2.create('table', {'number': 7})

        records = base1.iterate('table')
        self.assertEqual([6], [record['fields']['number'] for record in records])

    def test_multiple_clients(self) -> None:
        """Test accessing a table from different clients."""

        base1 = airtable.Airtable('first-base', '')
        base1.create('table', {'number': 8})

        other_client_base1 = airtable.Airtable('first-base', '')
        other_client_base1.create('table', {'number': 9})

        records = base1.iterate('table')
        self.assertEqual([8, 9], [record['fields']['number'] for record in records])


class FunctionsTestCase(unittest.TestCase):
    """Tests for top level module functions."""

    def test_clear(self) -> None:
        """Basic usage of the clear function."""

        base1 = airtablemock.Airtable('first-base', '')
        base1.create('table', {'number': 8})

        airtablemock.clear()

        other_client_base1 = airtablemock.Airtable('first-base', '')
        other_client_base1.create('table', {'number': 9})

        records = base1.iterate('table')
        self.assertEqual(
            [9],
            [typing.cast(typing.Dict[str, int], record['fields'])['number'] for record in records])


if __name__ == '__main__':
    unittest.main()  # pragma: no cover
