import mock
import typing
import unittest


def clear() -> None:
  ...


def patch(target: typing.Any) -> mock._patch:
  ...


_Record = typing.Dict[str, typing.Union[str, typing.Dict[str, typing.Any]]]


class Airtable(object):

  def __init__(
      self,
      base_id: typing.Optional[str] = None,
      api_key: typing.Optional[str] = None) -> None:
    ...

  def iterate(
      self,
      table_name: str,
      batch_size: int = 0,
      filter_by_formula: typing.Optional[str] = None,
      view: typing.Optional[str] = None) -> typing.Iterator[_Record]:
    ...

  @typing.overload
  def get(
      self,
      table_name: str,
      record_id: None = None,
      limit: int = 0,
      offset: typing.Optional[int] = None,
      filter_by_formula: typing.Optional[str] = None,
      view: typing.Optional[str] = None) \
      -> typing.Dict[str, typing.List[_Record]]:
   ...

  @typing.overload
  def get(
      self,
      table_name: str,
      record_id: str,
      limit: int = 0,
      offset: typing.Optional[int] = None,
      filter_by_formula: typing.Optional[str] = None,
      view: typing.Optional[str] = None) \
      -> _Record:
    ...

  def create(self, table_name: str, data: typing.Dict[str, typing.Any]) -> _Record:
    ...
 
  def update(self, table_name: str, record_id: str, data: typing.Dict[str, typing.Any]) -> _Record:
    ...

  def update_all(self, table_name: str, record_id: str, data: typing.Dict[str, typing.Any]) -> _Record:
    ...

  def delete(self, table_name: str, record_id: str) -> typing.Dict[str, typing.Union[str, bool]]:
    ...

  def create_view(self, table_name: str, view_name: str, formula: str) -> None:
    ...


class TestCase(unittest.TestCase):
  ...


def create_empty_table(base_id: str, table_name: str) -> None:
  ...
