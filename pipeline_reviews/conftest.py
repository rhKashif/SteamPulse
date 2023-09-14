"""File with fixtures for tests for review pipeline"""

from pytest import fixture
from pandas import DataFrame
from unittest.mock import MagicMock


@fixture
def fake_df_load():
    """Returns data-frame used for testing"""
    return DataFrame([{"game_id": 2, "test": 9},
                      {"game_id": 3, "test": 5}, {"game_id": 8, "test": None}], index=[1, 2, 3])


@fixture
def fake_review() -> str:
    """Returns a fake review for testing"""
    return "Test\n,;review fail"


@fixture
def fake_df_sentiment(fake_review: str) -> DataFrame:
    """Returns data-frame used for testing"""
    return DataFrame([{"review": fake_review}], index=[1])


@fixture
def time_string() -> str:
    """Returns a timestamp string for testing"""
    return "2019-02-23 12:13:10"


@fixture
def fake_df_transform(time_string: str) -> DataFrame:
    """Returns data-frame used for testing"""
    return DataFrame([{"playtime_last_2_weeks": 0, "review_score": 1,
                       "last_timestamp": time_string, "game_id": 1},
                      {"playtime_last_2_weeks": 2, "review_score": 1,
                       "last_timestamp": time_string, "game_id": 2}])


def mock_multiprocessing() -> MagicMock:
    "Returns a magic mock to mock multiprocessing"
    return MagicMock()


def mock_get_game_reviews(game: int) -> list:
    """Returns a mock game review"""
    test_review = {"review": "test"}
    return [[test_review]]
