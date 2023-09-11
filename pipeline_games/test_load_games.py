"""Testing script for load_games script"""
from unittest.mock import MagicMock, patch
from load_games import execute_batch_columns, execute_batch_columns_for_genres, execute_batch_columns_for_games, get_existing_platform_data, add_to_genre_link_table, add_to_publisher_link_table, add_to_developer_link_table, upload_developers, upload_publishers, upload_genres, upload_games, get_all_game_genre_ids, get_all_developer_game_ids, get_all_publisher_game_ids


@patch("load_games.execute_batch")
def test_execute_batch_columns_given_publisher_data(fake_batch, fake_publisher_data):
    """Test appropriate commands called for function"""
    fake_conn = MagicMock()
    execute_batch_columns(fake_conn, fake_publisher_data,
                          'publisher', "publisher_name", page_size=100)

    assert fake_batch.call_count == 1


@patch("load_games.execute_batch")
def test_execute_batch_columns_given_genre_data(fake_batch, fake_genre_data):
    """Test appropriate commands called for function"""
    fake_conn = MagicMock()
    execute_batch_columns_for_genres(fake_conn, fake_genre_data,
                                     'genre', page_size=100)

    assert fake_batch.call_count == 1


@patch("load_games.execute_batch")
def test_execute_batch_columns_given_game_data(fake_batch, fake_game_data):
    """Test appropriate commands called for function"""
    fake_conn = MagicMock()
    execute_batch_columns_for_games(fake_conn, fake_game_data,
                                    'game', page_size=100)

    assert fake_batch.call_count == 1


def test_platform_data_retrieved():
    """Appropriate commands called for existing data"""
    fake_conn = MagicMock()
    fake_execute = fake_conn.cursor().__enter__().execute
    fake_fetch = fake_conn.cursor().__enter__().fetchone
    fake_fetch.return_value = {'platform_id': 1}
    result = get_existing_platform_data('True', 'False', 'True', fake_conn, {})

    assert result == 1
    assert fake_execute.call_count == 1
    assert fake_fetch.call_count == 1


def test_all_game_id_commands_called(fake_game_and_genre):
    """Test appropriate commands called to get game id data"""
    fake_conn = MagicMock()
    fake_execute = fake_conn.cursor().__enter__().execute
    fake_fetch = fake_conn.cursor().__enter__().fetchall

    get_all_game_genre_ids(fake_conn, fake_game_and_genre)

    assert fake_execute.call_count == 2
    assert fake_fetch.call_count == 2


def test_all_publisher_id_commands_called(fake_game_and_publisher):
    """Test appropriate commands called to get game id data"""
    fake_conn = MagicMock()
    fake_execute = fake_conn.cursor().__enter__().execute
    fake_fetch = fake_conn.cursor().__enter__().fetchall

    get_all_game_genre_ids(fake_conn, fake_game_and_publisher)

    assert fake_execute.call_count == 2
    assert fake_fetch.call_count == 2


def test_all_developer_id_commands_called(fake_game_and_developer):
    """Test appropriate commands called to get game id data"""
    fake_conn = MagicMock()
    fake_execute = fake_conn.cursor().__enter__().execute
    fake_fetch = fake_conn.cursor().__enter__().fetchall

    get_all_game_genre_ids(fake_conn, fake_game_and_developer)

    assert fake_execute.call_count == 1
    assert fake_fetch.call_count == 1


@patch("load_games.execute_batch")
def test_genre_link_table_commands(fake_batch, fake_tuples):
    """Test appropriate commands called for genre link table"""
    fake_conn = MagicMock()

    add_to_genre_link_table(fake_conn, fake_tuples, 100)

    assert fake_batch.call_count == 1


@patch("load_games.execute_batch")
def test_publisher_link_table_commands(fake_batch, fake_tuples):
    """Test appropriate commands called for publisher link table"""
    fake_conn = MagicMock()

    add_to_publisher_link_table(fake_conn, fake_tuples, 100)

    assert fake_batch.call_count == 1


@patch("load_games.execute_batch")
def test_developer_link_table_commands(fake_batch, fake_tuples):
    """Test appropriate commands called for developer link table"""
    fake_conn = MagicMock()

    add_to_developer_link_table(fake_conn, fake_tuples, 100)

    assert fake_batch.call_count == 1


@patch("load_games.execute_batch_columns")
def test_developers_called(fake_batch, fake_complete_data):
    """Test appropriate functions called for developers"""
    fake_conn = MagicMock()
    upload_developers(fake_conn, fake_complete_data)

    assert fake_batch.call_count == 1


@patch("load_games.execute_batch_columns")
def test_publishers_called(fake_batch, fake_complete_data):
    """Test appropriate functions called for publishers"""
    fake_conn = MagicMock()
    upload_publishers(fake_conn, fake_complete_data)

    assert fake_batch.call_count == 1


@patch("load_games.execute_batch_columns_for_genres")
def test_genres_called(fake_batch, fake_complete_data):
    """Test appropriate functions called for genres"""
    fake_conn = MagicMock()
    upload_genres(fake_conn, fake_complete_data)

    assert fake_batch.call_count == 1


@patch("load_games.execute_batch_columns_for_games")
def test_games_called(fake_batch, fake_complete_data):
    """Test appropriate functions called for games"""
    fake_conn = MagicMock()
    upload_games(fake_conn, fake_complete_data)

    assert fake_batch.call_count == 1
