"""Testing file for transform script"""
import pytest
from pandas._libs.tslibs.timestamps import Timestamp

from transform_games import identify_unique_genre, create_user_generated_column, drop_unnecessary_columns, convert_date_to_datetime, convert_price_to_float, explode_column_to_individual_rows, check_data_is_not_null


def test_separate_rows_created_for_unique_tags(fake_raw_data):
    """Tests that unique genre have a separate row"""
    assert 'genre' not in list(fake_raw_data.columns)
    assert fake_raw_data.shape[0] == 1
    result = identify_unique_genre(fake_raw_data)
    assert result.shape[0] == 4
    assert 'genre' in list(result.columns)


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


def test_date_converted_if_valid():
    """Test valid date is returned"""
    result = convert_date_to_datetime("5 Sep, 2023")
    assert str(result) == "2023-09-05 00:00:00"
    assert isinstance(result, Timestamp) is True


def test_date_converted_to_none():
    """Test None is returned"""
    result = convert_date_to_datetime("30 Feb, 2023")
    assert result is None


@pytest.mark.parametrize("fake_price, expected_result", [("£5.30", 5.3), ("Free to play", 0.0)])
def test_prices_converted_to_float(fake_price, expected_result):
    """Test float returned when price passed in"""
    result = convert_price_to_float(fake_price)
    assert isinstance(result, float) is True
    assert result == expected_result


def test_explode_columns(fake_raw_data):
    """Test atomic rows created for rows with more than one value for specified column"""
    assert fake_raw_data.shape[0] == 1
    result = explode_column_to_individual_rows(fake_raw_data, 'developers')
    assert result.shape[0] == 2


@pytest.mark.parametrize("fake_data, expected_result", [(None, "Data not provided"), ("Fake publisher", "Fake publisher")])
def test_data_is_not_null_function(fake_data, expected_result):
    """Test data returned if valid or generic string if not valid"""
    result = check_data_is_not_null(fake_data)
    assert isinstance(result, str) is True
    assert result == expected_result
