# Change Log

## v0.0.6 [2018-06-26]

* Fix the `filter_by_formula` when a quoted value contains a quote.

## v0.0.5 [2018-06-22]

* Implement the `view` feature of the get and iterate method.
* Implement the `filter_by_formula` feature of the iterate method.
* Raises an error when trying to access a table that was not created before.
* Fixes the `offset` response in the get method.

## v0.0.4 [2018-06-19]

* Implement the `filter_by_formula` feature of the get method.

## v0.0.3 [2018-02-07]

* Added unit tests.
* Fixed the get method that had many syntax errors.
* Added a `clear()` method to clear all data in the mock bases.
* Added a `TestCase` class to ease independant unit testing.
