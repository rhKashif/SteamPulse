"""File with unit tests for extract.py"""

from unittest.mock import MagicMock
from pytest import raises

from extract import get_game_ids, GamesNotFound, get_db_connection
from extract import get_number_of_reviews


def test_get_game_ids_passes():
    """"""
    fake_connection = MagicMock()
    fake_cursor = fake_connection.cursor().__enter__()
    fake_fetch = fake_cursor.fetchall
    fake_fetch.return_value = [{"app_id": 1},{"app_id": 2}]
    assert get_game_ids(fake_connection) == [1, 2]



def test_get_game_ids_fails():
    """"""
    fake_connection = MagicMock()
    fake_cursor = fake_connection.cursor().__enter__()
    fake_fetch = fake_cursor.fetchall
    fake_fetch.return_value = []
    with raises(GamesNotFound):
        get_game_ids(fake_connection)


def test_get_db_connection(monkeypatch):
    """"""
    monkeypatch.setattr("extract.connect", lambda **kwargs: None)
    assert get_db_connection() == None


def test_get_number_of_reviews(monkeypatch):
    """"""
    fake_response = MagicMock()
    fake_response.json.return_value = {"query_summary": {"total_reviews": "test"}}
    monkeypatch.setattr("requests.get", lambda *args: fake_response)
    assert get_number_of_reviews(0) == "test"