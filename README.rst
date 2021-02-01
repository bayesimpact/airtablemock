Airtable Mock
=============

A mock library to help test Python code accessing Airtable using the
`Python library <https://github.com/nicocanali/airtable-python>`__.

It keeps tables in RAM and can do basic operations.

Installation
------------

The easiest way is using pip:

.. code:: sh

    pip install airtablemock

Usage
-----

In your test, you patch the whole airtable library:

.. code:: py

    import unittest

    import airtablemock

    import mycode


    @airtablemock.patch(mycode.__name__ + '.airtable')
    class TestMyCode(unittest.TestCase):

      def test_foo():
        # This is a client for the base "baseID", it will not access the real
        # Airtable service but only the mock one which keeps data in RAM.
        client = airtablemock.Airtable('baseID', 'apiKey')

        # Populate the table.
        client.create('table-foo', {'field1': 1, 'field2': 'two'})

        # Run your code that uses Airtable, it should transparently uses the table
        # above.
        mycode.run()

        # Access the table again to check if anything was modified.
        records = client.get('table-foo')
        …

Release
-------

To create a new release of airtablemock, tag the Git repo and run:

.. code:: sh

    python setup.py sdist bdist_wheel
    twine upload dist/airtablemock-*
