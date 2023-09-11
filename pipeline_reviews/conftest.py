"""File with fixtures for tests for review pipeline"""

from pytest import fixture
from pandas import DataFrame


@fixture
def fake_df_load():
    """Fake data-frame used for testing"""
    return DataFrame([{"game_id": 2, "test": 9},
        {"game_id": 3, "test": 5}, {"game_id": 8, "test": None}], index=[1,2,3])


@fixture
def fake_review() -> str:
    """Returns a fake review for testing"""
    return "Test\n,;review fail"


@fixture
def fake_df_sentiment(fake_review) -> DataFrame:
    """Returns data-frame used for testing"""
    return DataFrame([{"review": fake_review}], index=[1])
