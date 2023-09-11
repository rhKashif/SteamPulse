"""File with unit tests for load.py"""

from unittest.mock import MagicMock

from load import get_game_ids_foreign_key_values, get_game_ids, move_reviews_to_db


def test_get_game_ids_foreign_key_values(monkeypatch, fake_df_load):
    """Verifies that data-frame gets correctly modified with nan
    cell values taken out for the full row and correct game_ids replaced"""
    monkeypatch.setattr("extract.get_db_connection", lambda x: None)
    monkeypatch.setattr("load.get_game_ids", lambda *args: 1)
    assumed_result_df = fake_df_load.assign(game_id=1)
    assumed_result_df = assumed_result_df[assumed_result_df["test"].notna()]
    returned_df = get_game_ids_foreign_key_values(fake_df_load)
    assert returned_df.equals(assumed_result_df)


def test_get_game_ids():
    """Verifies that get_game_ids returns correctly
    formatted value from sql query"""
    fake_connection = MagicMock()
    fake_cursor = fake_connection.cursor().__enter__()
    fake_fetch = fake_cursor.fetchone
    fake_fetch.return_value = {"game_id": 1}
    returned_val = get_game_ids(fake_connection, 0, {})
    assert returned_val == 1


def test_move_reviews_to_db(monkeypatch, fake_df_load, capfd):
    """Verifies that execute_batch was called"""
    fake_connection = MagicMock()
    monkeypatch.setattr("load.execute_batch", lambda *args: print("Data committed!"))
    move_reviews_to_db(fake_connection, fake_df_load)
    captured = capfd.readouterr()
    assert "Data committed!" in captured.out
