"""Script for loading to database"""
from os import environ
from dotenv import load_dotenv
import pandas as pd
from psycopg2 import connect, DatabaseError
from psycopg2.extension import Connection
from psycopg2.extras import RealDictCursor, execute_batch


def get_db_connection(config) -> Connection:
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


def execute_batch_columns(conn: Connection, data: pd.DataFrame, table: str, column: str, page_size=100) -> None:
    """batch execution of adding specified data to the database"""
    tuples = list(zip(data.unique()))
    cols = column
    query = """INSERT INTO %s(%s) VALUES(%%s) ON CONFLICT (%s) DO NOTHING;""" % (
        table, cols, cols)
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


def execute_batch_columns_for_genres(conn: Connection, data: pd.DataFrame, table: str, page_size=100) -> None:
    """batch execution of adding genres into the database"""
    tuples = [tuple(x) for x in data.to_numpy()]
    cols = 'genre,user_generated'

    query = """INSERT INTO %s(%s) SELECT %%s,%%s WHERE NOT EXISTS
            (SELECT genre_id FROM genre
              WHERE genre = %%s AND user_generated = %%s);""" % (table, cols)
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


def execute_batch_columns_for_games(conn: Connection, data: pd.DataFrame, table: str, page_size=100) -> None:
    """batch execution of adding games into the database"""
    tuples = [tuple(x) for x in data.to_numpy()]
    cols = ','.join(list(data.columns))

    query = """INSERT INTO %s(%s) VALUES (%%s,%%s,%%s,%%s,%%s,%%s)
            ON CONFLICT (app_id) DO NOTHING""" % (table, cols)
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


def get_existing_platform_data(mac_c, windows_c, linux_c, conn: Connection, cache: dict) -> int | None:
    """Retrieves the existing data for platform using cache and return platform_id"""
    value = f'{mac_c} {windows_c} {linux_c}'
    if value in cache.keys():
        return cache[value]

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SELECT platform_id FROM platform
                    WHERE mac = %s AND windows = %s AND linux = %s;""",
                    [mac_c, windows_c, linux_c])
        id_value = cur.fetchone()['platform_id']
        cache[value] = id_value
        cur.close()
        return cache[value]


def add_to_genre_link_table(conn: Connection, data: list) -> None:
    """Updates genre link table"""
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


def add_to_publisher_link_table(conn: Connection, data: list) -> None:
    """Updates publisher link table"""
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
        if result['exists'] is False:
            cur.execute(
                """INSERT INTO game_publisher_link(game_id, publisher_id)
                VALUES (%s, %s);""", [game_id, publisher_id])
        conn.commit()
        cur.close()


def add_to_developer_link_table(conn: Connection, data: list) -> None:
    """Updates link table"""
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


def upload_developers(data: pd.DataFrame, conn: Connection) -> None:
    """Uploads new developers"""
    developers_data = data['developers']
    execute_batch_columns(conn, developers_data,
                          'developer', 'developer_name', page_size=100)


def upload_publishers(data: pd.DataFrame, conn: Connection) -> None:
    """Uploads new publishers"""
    publishers_data = data['publishers']
    execute_batch_columns(conn, publishers_data,
                          'publisher', 'publisher_name', page_size=100)


def upload_genres(data: pd.DataFrame, conn: Connection) -> None:
    """Uploads new genres"""
    genres = data[["genre", "user_generated", "genre", "user_generated"]]
    execute_batch_columns_for_genres(conn, genres,
                                     'genre', page_size=100)


def upload_games(data: pd.DataFrame) -> None:
    """Uploads new games"""
    platform_cache = {}
    data['platform_id'] = data.apply(
        lambda row: get_existing_platform_data(
            row['mac'], row['windows'], row['linux'], connect_d, platform_cache), axis=1)

    new_game_data = data.rename(columns={'full_price': 'price'})

    games_to_load = new_game_data[[
        'app_id', 'title', 'release_date', 'price', 'sale_price', 'platform_id']]
    execute_batch_columns_for_games(connect_d, games_to_load,
                                    'game', page_size=100)


if __name__ == "__main__":
    load_dotenv()
    configuration = environ
    connect_d = get_db_connection(configuration)

    data_frame = pd.read_csv("genres.csv")
    game_data = pd.read_csv("final_games.csv")

    try:
        upload_publishers(data_frame, connect_d)
        upload_developers(data_frame, connect_d)
        upload_genres(data_frame, connect_d)
        upload_games(game_data, connect_d)

        for row in data_frame.itertuples():
            add_to_genre_link_table(connect_d, row)
            add_to_developer_link_table(connect_d, row)
            add_to_publisher_link_table(connect_d, row)

    finally:
        connect_d.close()
