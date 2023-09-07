"""Script for loading to database"""
from os import environ
from dotenv import load_dotenv
import pandas as pd
from psycopg2 import connect, DatabaseError, sql
from psycopg2.extras import RealDictCursor, execute_batch


def get_db_connection(config) -> connect:
    """Connect to the database with game data"""
    try:
        return connect(
            user=config['DATABASE_USERNAME'],
            password=config['DATABASE_PASSWORD'],
            host=config['DATABASE_IP'],
            port=config['DATABASE_PORT'],
            database=config['DATABASE_NAME'])
    except ValueError:
        return "Error connecting to database."


def execute_batch_columns(conn, data: pd.DataFrame, table: str, column: str, page_size=100) -> None:
    """Using psycopg2.extras.execute_batch() to insert the dataframe"""
    tuples = list(zip(data.unique()))
    cols = column
    query = """INSERT INTO %s(%s) VALUES(%%s)""" % (table, cols)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        try:
            execute_batch(cur, query, tuples, page_size)
            conn.commit()
            cur.close()
            print("execute_batch() done")
        except (Exception, DatabaseError) as error:
            print(f"Error: {error}")
            conn.rollback()
            cur.close()


def execute_batch_columns_for_genres(conn, data: pd.DataFrame, table: str, page_size=100) -> None:
    """Using psycopg2.extras.execute_batch() to insert the genres into database"""
    tuples = [tuple(x) for x in data.to_numpy()]
    cols = ','.join(list(data.columns))

    query = "INSERT INTO %s(%s) VALUES(%%s,%%s)" % (table, cols)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        try:
            execute_batch(cur, query, tuples, page_size)
            conn.commit()
            cur.close()
            print("execute_batch() done")
        except (Exception, DatabaseError) as error:
            print(f"Error: {error}")
            conn.rollback()
            cur.close()


def execute_batch_columns_for_games(conn, data: pd.DataFrame, table: str, page_size=100) -> None:
    """Using psycopg2.extras.execute_batch() to insert the genres into database"""
    tuples = [tuple(x) for x in data.to_numpy()]
    cols = ','.join(list(data.columns))

    query = "INSERT INTO %s(%s) VALUES(%%s,%%s,%%s,%%s,%%s,%%s)" % (
        table, cols)
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        try:
            execute_batch(cur, query, tuples, page_size)
            conn.commit()
            cur.close()
            print("execute_batch() done")
        except (Exception, DatabaseError) as error:
            print(f"Error: {error}")
            conn.rollback()
            cur.close()


def get_existing_data(variable: str, table: str, value_name: str, value: str, conn: connect, cache: dict) -> None:
    """Retrieves the existing data and adds to a cache dict given a provided value and table"""
    if value in cache.keys():
        return cache[value]
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                sql.SQL("""SELECT {variable} FROM {table} WHERE {value_name} = %s;""").format(
                    variable=sql.Identifier(variable), table=sql.Identifier(table),
                    value_name=sql.Identifier(value_name)), [value])
            id_value = cur.fetchone()[variable]
            cache[value] = id_value
            cur.close()
            return cache[value]
    except TypeError:
        return "None"


def get_existing_data_for_genre(genre_column: str, user_column: bool, conn: connect, cache: dict) -> int | None:
    """Retrieves the existing data and adds to a cache dict given a provided value and table"""
    value = f'{genre_column} {user_column}'
    if value in cache.keys():
        return cache[value]
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""SELECT genre_id FROM genre WHERE genre = %s AND user_generated = %s;""", [
                        genre_column, user_column])
            id_value = cur.fetchone()['genre_id']
            cache[value] = id_value
            cur.close()
            return cache[value]
    except TypeError:
        return "None"


def get_existing_platform_data(mac_column, windows_column, linux_column, conn: connect, cache: dict) -> int | None:
    """Retrieves the existing data and adds to a cache dict given a provided value and table"""
    value = f'{mac_column} {windows_column} {linux_column}'
    if value in cache.keys():
        return cache[value]
    else:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""SELECT platform_id FROM platform WHERE mac = %s AND windows = %s AND linux = %s;""", [
                        mac_column, windows_column, linux_column])
            id_value = cur.fetchone()['platform_id']
            cache[value] = id_value
            cur.close()
            return cache[value]


def add_to_genre_link_table(conn: connect, data: list) -> None:
    """Update genre link table"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT genre_id FROM genre WHERE genre = %s AND user_generated = %s;""",
            [data[12], data[13]])
        genre_id = cur.fetchone()['genre_id']
        cur.execute(
            """SELECT game_id FROM game WHERE app_id = %s;""",
            [data[2]])
        game_id = cur.fetchone()['game_id']
        cur.execute(
            """SELECT exists (SELECT 1 FROM game_genre_link 
            WHERE game_id = %s AND genre_id = %s LIMIT 1);""",
            [game_id, genre_id])
        result = cur.fetchone()
        if result['exists'] is True:
            cur.close()
        elif result['exists'] is False:
            cur.execute("""INSERT INTO game_genre_link(game_id, genre_id)
                        VALUES (%s, %s);""", [game_id, genre_id])
        conn.commit()
        cur.close()


def add_to_publisher_link_table(conn: connect, data: list) -> None:
    """Update publisher link table"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT publisher_id FROM publisher WHERE publisher_name = %s;""",
            [data[11]])
        publisher_id = cur.fetchone()['publisher_id']
        cur.execute(
            """SELECT game_id FROM game WHERE app_id = %s;""",
            [data[2]])
        game_id = cur.fetchone()['game_id']
        cur.execute(
            """SELECT exists (SELECT 1 FROM game_publisher_link 
            WHERE game_id = %s AND publisher_id = %s LIMIT 1);""",
            [game_id, publisher_id])
        result = cur.fetchone()
        if result['exists'] is True:
            cur.close()
        elif result['exists'] is False:
            cur.execute(
                """INSERT INTO game_publisher_link(game_id, publisher_id)
                VALUES (%s, %s);""", [game_id, publisher_id])
        conn.commit()
        cur.close()


def add_to_developer_link_table(conn: connect, data: list) -> None:
    """Update link table"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT developer_id FROM developer WHERE developer_name = %s;""",
            [data[10]])
        developer_id = cur.fetchone()['developer_id']
        cur.execute(
            """SELECT game_id FROM game WHERE app_id = %s;""",
            [data[2]])
        game_id = cur.fetchone()['game_id']
        cur.execute(
            """SELECT exists (SELECT 1 FROM game_developer_link 
            WHERE game_id = %s AND developer_id = %s LIMIT 1);""",
            [game_id, developer_id])
        result = cur.fetchone()
        if result['exists'] is True:
            cur.close()
        elif result['exists'] is False:
            cur.execute(
                """INSERT INTO game_developer_link(game_id, developer_id)
                VALUES (%s, %s);""", [game_id, developer_id])
        conn.commit()
        cur.close()


if __name__ == "__main__":
    load_dotenv()
    configuration = environ
    connection = get_db_connection(configuration)

    data_frame = pd.read_csv("genres.csv")
    game_data = pd.read_csv("final_games.csv")

    try:

        developers_cache = {}
        data_frame['developer_id'] = data_frame["developers"].apply(
            lambda row: get_existing_data(
                "developer_id", "developer", "developer_name",
                row, connection, developers_cache))

        developers_data = data_frame[data_frame.developer_id == "None"]
        new_developers = developers_data['developers']

        execute_batch_columns(connection, new_developers,
                              'developer', 'developer_name', page_size=100)

        publishers_cache = {}
        data_frame["publisher_id"] = data_frame["publishers"].apply(
            lambda row: get_existing_data(
                "publisher_id", "publisher", "publisher_name",
                row, connection, publishers_cache))

        publishers_data = data_frame[data_frame.publisher_id == "None"]
        new_publishers = publishers_data['publishers']

        execute_batch_columns(connection, new_publishers,
                              'publisher', 'publisher_name', page_size=100)

        genres_cache = {}
        data_frame['genre_id'] = data_frame.apply(
            lambda row: get_existing_data_for_genre(
                row['genre'], row['user_generated'], connection, genres_cache), axis=1)

        genres_data = data_frame[data_frame.genre_id == "None"]
        genres = genres_data[["genre", "user_generated"]]

        execute_batch_columns_for_genres(connection, genres,
                                         'genre', page_size=100)

        platform_cache = {}
        game_data['platform_id'] = game_data.apply(
            lambda row: get_existing_platform_data(
                row['mac'], row['windows'], row['linux'], connection, platform_cache), axis=1)

        game_cache = {}
        game_data["game_id"] = data_frame["app_id"].apply(
            lambda row: get_existing_data(
                "game_id", "game", "app_id",
                row, connection, game_cache))

        new_game_data = game_data[game_data.game_id == "None"]
        new_game_data = new_game_data.rename(columns={'full_price': 'price'})

        games_to_load = new_game_data[[
            'app_id', 'title', 'release_date', 'price', 'sale_price', 'platform_id']]

        execute_batch_columns_for_games(connection, games_to_load,
                                        'game', page_size=100)

        for row in data_frame.itertuples():
            add_to_genre_link_table(connection, row)
            add_to_developer_link_table(connection, row)
            add_to_publisher_link_table(connection, row)

    finally:
        connection.close()
