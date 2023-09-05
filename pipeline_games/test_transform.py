"""Testing file for transform script"""
import pytest

from transform_games import identify_unique_tags


def test_separate_columns_created_for_unique_tags(fake_raw_data):
    """Tests that unique tags have a separate row"""
    result = identify_unique_tags(fake_raw_data)
