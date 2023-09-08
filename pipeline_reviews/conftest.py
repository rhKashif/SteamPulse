"""File with fixtures for tests for review pipeline"""

from pytest import fixture
from pandas import DataFrame

@fixture
def fake_df():
    """Fake data-frame used for testing"""
    return DataFrame([{"game_id": 2, "test": 9},
        {"game_id": 3, "test": 5}, {"game_id": 8, "test": None}], index=[1,2,3])