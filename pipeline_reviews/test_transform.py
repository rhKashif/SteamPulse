"""File with unit tests for transform.py"""

from datetime import date
from unittest.mock import MagicMock
from pandas import DataFrame
from numpy import int64

from transform import get_release_date, remove_empty_rows, validate_time_string
from transform import remove_duplicate_reviews, remove_unnamed, correct_cell_values
from transform import change_column_types, correct_playtime


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


def test_validate_time_string_basic(time_string):
    """Verifies that correct object type
    is returned (date) from a timestamp string"""
    assert isinstance(validate_time_string(time_string), date)


def test_validate_time_string_error():
    """Verifies that when error occurs, None is returned"""
    assert validate_time_string(None) is None


def test_remove_duplicate_reviews():
    """Verifies that duplicate rows are removed"""
    fake_review = {"review": "test", "game_id": 1, "playtime_last_2_weeks": 55}
    fake_df = DataFrame([fake_review, fake_review])
    assert remove_duplicate_reviews(fake_df).shape == (1, 3)


def test_remove_unnamed():
    """Verifies that unnamed column is removed if exists"""
    fake_df = DataFrame([{"Unnamed: 0": 1, "test": "test2"}])
    assert remove_unnamed(fake_df).shape == (1, 1)


def test_correct_cell_values(fake_df_transform):
    """Verifies that rows are removed with incorrect cell values"""
    assert correct_cell_values(fake_df_transform).shape == (1, 4)


def test_change_column_types(fake_df_transform):
    """Verifies that column types are correctly changed"""
    returned_df = change_column_types(fake_df_transform)
    assert all(isinstance(val, date)
               for val in returned_df["last_timestamp"].values)
    assert all(isinstance(val, int64)
               for val in returned_df["review_score"].values)
    assert all(isinstance(val, int64) for val in
               returned_df["playtime_last_2_weeks"].values)


def test_correct_playtime(monkeypatch, time_string, fake_df_transform):
    """Verifies that function correctly identifies that playtime is valid"""
    monkeypatch.setattr("transform.get_db_connection", lambda *args: None)
    monkeypatch.setattr("transform.get_release_date",
                        lambda *args: validate_time_string(time_string))
    assert correct_playtime(fake_df_transform).equals(fake_df_transform)
