"""File with unit tests for extract.py"""

from pandas import DataFrame
from pytest import raises
from requests.exceptions import Timeout
from unittest.mock import MagicMock

from extract import get_game_ids, GamesNotFound, get_db_connection
from extract import get_number_of_reviews, get_all_reviews, get_reviews_for_game


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
    monkeypatch.setattr("extract.connect", lambda **kwargs: None)
    assert get_db_connection() == None


def test_get_number_of_reviews(monkeypatch):
    """Verifies that get request is correctly finding the number of reviews"""
    fake_response = MagicMock()
    fake_response.json.return_value = {"query_summary": {"total_reviews": "test"}}
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: fake_response)
    assert get_number_of_reviews(0) == "test"


def test_get_all_reviews_errors(monkeypatch):
    """Verifies that if error is found, an empty data-frame is returned"""
    monkeypatch.setattr("extract.get_number_of_reviews", lambda *args: 0)
    monkeypatch.setattr("extract.get_reviews_for_game", lambda *args: {"error": "test"})
    assert get_all_reviews([0]).empty


def test_get_all_reviews_no_reviews(monkeypatch):
    """Verifies that an empty data-frame is created from no reviews"""
    monkeypatch.setattr("extract.get_number_of_reviews", lambda *args: 1)
    monkeypatch.setattr("extract.get_reviews_for_game", lambda *args: {
        "next_cursor": "test", "reviews": []})
    assert get_all_reviews([0]).empty


def test_get_all_reviews_one_review(monkeypatch):
    """Verifies that data-frame is correctly formed from the data"""
    monkeypatch.setattr("extract.get_number_of_reviews", lambda *args: 1)
    fake_reviews = {"next_cursor": "test","reviews": [
        {"test": "0", "text": "fake review"}]}
    monkeypatch.setattr("extract.get_reviews_for_game", lambda *args: fake_reviews)
    expected_result = DataFrame(fake_reviews["reviews"])
    assert get_all_reviews([0]).equals(expected_result)


def test_get_reviews_for_game_raises_error(monkeypatch):
    """Verifies that the test correctly identifies timeout error"""
    fake_response = MagicMock()
    fake_response.json.side_effect = Timeout()
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: fake_response)
    assert "error" in get_reviews_for_game(10, "").keys()


def test_get_reviews_for_game_basic(monkeypatch):
    """Verifies that reviews from mocked API request are collected correctly"""
    fake_response = MagicMock()
    fake_response.json.return_value = {"cursor" : "" ,"reviews": [{"review": 1, "votes_up": 1,
        "timestamp_created": 1672531200, "author": {"playtime_forever": 10}}]}
    monkeypatch.setattr("requests.get", lambda *args, **kwargs: fake_response)
    assert get_reviews_for_game(10, "") == {"next_cursor": "", "reviews": [
        {"game_id": 10, "last_timestamp": "2023-01-01 00:00:00",
         "playtime_last_2_weeks": 10, "review": 1, "review_score": 1}]}
