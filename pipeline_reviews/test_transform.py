"""File with unit tests for transform.py"""

from datetime import date

from pandas import DataFrame
from unittest.mock import MagicMock

from transform import get_release_date, remove_empty_rows, validate_time_string
from transform import remove_duplicate_reviews, remove_unnamed


def test_get_release_date():
    """Verifies that release date returnes correct value"""
    fake_connection = MagicMock()
    fake_cursor = fake_connection.cursor().__enter__()
    fake_fetch = fake_cursor.fetchone.return_value = {"release_date": 1}
    assert get_release_date(0, fake_connection, {}) == 1


def test_remove_empty_rows():
    """Verifies that empty rows are removed"""
    fake_df = DataFrame({"test": None}, index=[1])
    assert remove_empty_rows(fake_df).empty


def test_validate_time_string_basic():
    """Verifies that correct object type
    is returned (date) from a timestamp string"""
    timestamp_string = "2019-02-23 12:13:10"
    assert isinstance(validate_time_string(timestamp_string), date)


def test_validate_time_string_error():
    """Verifies that when error occurs, None is returned"""
    assert validate_time_string(None) is None


def test_remove_duplicate_reviews():
    """Verifies that duplicate rows are removed"""
    fake_review = {"review": "test","game_id": 1,"playtime_last_2_weeks": 55}
    fake_df = DataFrame([fake_review, fake_review])
    assert remove_duplicate_reviews(fake_df).shape == (1,3)


def test_remove_unnamed():
    """Verifies that unnamed column is removed if exists"""
    fake_df = DataFrame([{"Unnamed: 0": 1, "test": "test2"}])
    assert remove_unnamed(fake_df).shape == (1,1)