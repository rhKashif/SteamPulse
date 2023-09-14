"""File with unit tests for extract.py"""

from unittest.mock import MagicMock

from pytest import raises
from requests.exceptions import Timeout

from conftest import mock_multiprocessing, mock_get_game_reviews
from extract import get_game_ids, GamesNotFound, get_db_connection
from extract import get_all_reviews, get_reviews_for_game
from extract import get_number_of_reviews, get_game_reviews


def test_get_game_ids_passes():
    """Verifies that app_ids were correctly formatted from
    mocked psql query response"""
    fake_connection = MagicMock()
    fake_cursor = fake_connection.cursor().__enter__()
    fake_fetch = fake_cursor.fetchall
    fake_fetch.return_value = [{"app_id": 1}, {"app_id": 2}]
    assert get_game_ids(fake_connection) == [1, 2]


def test_get_game_ids_fails():
    """Verifies that extract script raises GamesNotFound
    error if no games were returned"""
    fake_connection = MagicMock()
    fake_cursor = fake_connection.cursor().__enter__()
    fake_fetch = fake_cursor.fetchall
    fake_fetch.return_value = []
    with raises(GamesNotFound):
        get_game_ids(fake_connection)


def test_get_db_connection(monkeypatch):
    """Mocks PSQL connection and checks that it was returned"""
    monkeypatch.setattr("extract.environ", MagicMock())
    monkeypatch.setattr("extract.connect", lambda **kwargs: None)
    assert get_db_connection() is None


def test_get_number_of_reviews(monkeypatch):
    """Verifies that get request is correctly finding the number of reviews"""
    fake_response = MagicMock()
    fake_response.json.return_value = {
        "query_summary": {"total_reviews": "test"}}
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: fake_response)
    assert get_number_of_reviews(0) == "test"


def test_get_game_reviews_errors(monkeypatch):
    """Verifies that if error is found, an empty list is returned"""
    monkeypatch.setattr("extract.get_number_of_reviews", lambda *args: 1)
    monkeypatch.setattr("extract.get_reviews_for_game", lambda *args: {"error": "test"})
    assert not get_game_reviews(0)


def test_get_game_reviews_no_reviews(monkeypatch):
    """Verifies that no data is returned from no reviews"""
    monkeypatch.setattr("extract.get_number_of_reviews", lambda *args: 1)
    monkeypatch.setattr("extract.get_reviews_for_game", lambda *args: {
        "next_cursor": "test", "reviews": []})
    assert not get_game_reviews(0)


def test_get_game_reviews_one_review(monkeypatch):
    """Verifies that reviews are correctly formed from the extraction"""
    monkeypatch.setattr("extract.get_number_of_reviews", lambda *args: 1)
    monkeypatch.setattr("extract.get_reviews_for_game", lambda *args: {
        "next_cursor": "test", "reviews": [{},{}]})
    assert get_game_reviews(0) == [[{},{}]]


def test_get_reviews_for_game_raises_error(monkeypatch):
    """Verifies that the test correctly identifies timeout error"""
    fake_response = MagicMock()
    fake_response.json.side_effect = Timeout()
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: fake_response)
    assert "error" in get_reviews_for_game(10, "").keys()


def test_get_reviews_for_game_basic(monkeypatch):
    """Verifies that reviews from mocked API request are collected correctly"""
    fake_response = MagicMock()
    fake_response.json.return_value = {"cursor": "", "reviews":
                                       [{"review": 1, "votes_up": 1, "timestamp_created": 1672531200,
                                         "author": {"playtime_forever": 10}}]}
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: fake_response)
    assert get_reviews_for_game(10, "") == {"next_cursor": "", "reviews": [
        {"game_id": 10, "last_timestamp": "2023-01-01 00:00:00",
         "playtime_last_2_weeks": 10, "review": 1, "review_score": 1}]}


def test_get_all_reviews(monkeypatch):
    """Verifies that values from multiprocessing are correctly unpacked"""
    monkeypatch.setattr("multiprocessing.Pool", mock_multiprocessing)
    monkeypatch.setattr("extract.get_game_reviews", mock_get_game_reviews)
    returned_df = get_all_reviews([1])
    assert returned_df.values == "test"
