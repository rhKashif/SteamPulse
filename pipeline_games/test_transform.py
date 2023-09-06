"""Testing file for transform script"""
import pytest
from pandas._libs.tslibs.timestamps import Timestamp

from transform_games import identify_unique_tags, create_user_generated_column, drop_unnecessary_columns, convert_date_to_datetime, convert_price_to_float


def test_separate_columns_created_for_unique_tags(fake_raw_data):
    """Tests that unique tags have a separate row"""
    assert fake_raw_data.shape[0] == 1
    result = identify_unique_tags(fake_raw_data)
    assert result.shape[0] == 4


def test_user_generated_column_created(fake_data_with_tags):
    """Check new column added to dataframe"""
    assert len(fake_data_with_tags.columns) == 13
    result = create_user_generated_column(fake_data_with_tags)

    assert len(result.columns) == 14


def test_columns_dropped(fake_data_with_tags):
    """Check specified column is dropped"""
    assert len(fake_data_with_tags.columns) == 13
    assert 'user_tags' in list(fake_data_with_tags.columns)
    result = drop_unnecessary_columns(fake_data_with_tags, 'user_tags')
    assert len(result.columns) == 12
    assert 'user_tags' not in list(result.columns)


def test_date_converted_if_valid(fake_date):
    """Test valid date is returned"""
    result = convert_date_to_datetime(fake_date)

    assert str(result) == "2023-09-05 00:00:00"
    assert isinstance(result, Timestamp) is True


def test_date_converted_to_none(fake_invalid_date):
    """Test None is returned"""
    result = convert_date_to_datetime(fake_invalid_date)

    assert str(result) == "None"


def test_prices_converted_to_float(fake_price):
    """Test float returned when price passed in"""
    result = convert_price_to_float(fake_price)

    assert isinstance(result, float) is True
    assert result == 5.30


def test_prices_converted_to_float_free_fames(price_is_free):
    """Test float returned when price passed in"""
    result = convert_price_to_float(price_is_free)

    assert isinstance(result, float) is True
    assert result == 0.0
