"""Script for loading to database"""
from os import environ
from dotenv import load_dotenv
import pandas as pd
from psycopg2 import connect, Error
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor, execute_batch


def get_db_connection(config) -> connection:
    """Connect to the database with game data"""
    try:
        return connect(
            user=config['DATABASE_USERNAME'],
            password=config['DATABASE_PASSWORD'],
            host=config['DATABASE_ENDPOINT'],
            port=config['DATABASE_PORT'],
            database=config['DATABASE_NAME'],
            cursor_factory=RealDictCursor)
    except (Error, ValueError) as err:
        return f"Error connecting to database. {err}"


def execute_batch_columns(conn: connection, data: pd.DataFrame, table: str, column: str, page_size=100) -> None:
    """batch execution of adding specified data to the database"""
    tuples = list(zip(data.unique()))
    query = sql.SQL("""INSERT INTO {table}({column})
            VALUES(%s) ON CONFLICT ({column}) DO NOTHING;""").format(
        table=sql.Identifier(table), column=sql.Identifier(column))
    with conn.cursor() as cur:
        try:
            execute_batch(cur, query, tuples, page_size)
            conn.commit()
            print("execute_batch() done")
        except Error as err:
            print(f"Error: {err}")
            conn.rollback()


def execute_batch_columns_for_genres(conn: connection, data: pd.DataFrame, table: str, page_size=100) -> None:
    """batch execution of adding genres into the database"""
    tuples = [tuple(x) for x in data.to_numpy()]
    cols = 'genre,user_generated'

    query = """INSERT INTO %s(%s) SELECT %%s,%%s WHERE NOT EXISTS
            (SELECT genre_id FROM genre
            WHERE genre = %s AND user_generated = %s);""").format(
        table=sql.Identifier(table), cols=sql.SQL(cols))
    with conn.cursor() as cur:
        try:
            execute_batch(cur, query, tuples, page_size)
            conn.commit()
            print("execute_batch() done")
        except Error as err:
            print(f"Error: {err}")
            conn.rollback()


def execute_batch_columns_for_games(conn: connection, data: pd.DataFrame, table: str, page_size=100) -> None:
    """batch execution of adding games into the database"""
    tuples = [tuple(x) for x in data.to_numpy()]
    cols = ','.join(list(data.columns))
    query = sql.SQL("""INSERT INTO {table}({cols}) VALUES (%s,%s,%s,%s,%s,%s)
            ON CONFLICT (app_id) DO NOTHING RETURNING game_id;""").format(
        table=sql.Identifier(table), cols=sql.SQL(cols))
    with conn.cursor() as cur:
        try:
            execute_batch(cur, query, tuples, page_size)
            conn.commit()
            print("execute_batch() done")
        except Error as err:
            print(f"Error: {err}")
            conn.rollback()


def get_existing_platform_data(mac_c, windows_c, linux_c, conn: connection, cache: dict) -> int | None:
    """Retrieves the existing data for platform using cache and return platform_id"""
    value = f'{mac_c} {windows_c} {linux_c}'
    if value in cache.keys():
        return cache[value]

    with conn.cursor() as cur:
        cur.execute("""SELECT platform_id FROM platform
                    WHERE mac = %s AND windows = %s AND linux = %s;""",
                    [mac_c, windows_c, linux_c])
        id_value = cur.fetchone()['platform_id']
        cache[value] = id_value
        return cache[value]


def get_all_game_genre_ids(conn: connection, data: list) -> list[tuple]:
    """Returns all game_genre_ids for linking table"""
    tuples = [tuple(x) for x in data.to_numpy()]
    query = """SELECT game.game_id, genre.genre_id FROM genre CROSS JOIN game
            WHERE game.app_id = %s AND genre.genre = %s AND user_generated = %s;"""
    all_ids = []
    for line in tuples:
        with conn.cursor() as cur:
            cur.execute(query, line)
            game_genre = cur.fetchall()
            all_ids.append(
                (game_genre[0]['game_id'], game_genre[0]['genre_id'],
                 game_genre[0]['game_id'], game_genre[0]['genre_id']))
    return all_ids


def get_all_publisher_game_ids(conn: connection, data: list) -> list[tuple]:
    """Returns all game_publisher ids for linking table"""
    tuples = [tuple(x) for x in data.to_numpy()]
    query = """SELECT game.game_id, publisher.publisher_id FROM publisher CROSS JOIN game
            WHERE game.app_id = %s AND publisher.publisher_name = %s;"""
    all_ids = []
    for line in tuples:
        with conn.cursor() as cur:
            cur.execute(query, line)
            game_genre = cur.fetchall()
            all_ids.append(
                (game_genre[0]['game_id'], game_genre[0]['publisher_id'],
                 game_genre[0]['game_id'], game_genre[0]['publisher_id']))
    return all_ids


def get_all_developer_game_ids(conn: connection, data: list) -> list[tuple]:
    """Returns all game_developer ids for linking table"""
    tuples = [tuple(x) for x in data.to_numpy()]
    query = """SELECT game.game_id, developer.developer_id FROM developer CROSS JOIN game
            WHERE game.app_id = %s AND developer.developer_name = %s;"""
    all_ids = []
    for line in tuples:
        with conn.cursor() as cur:
            cur.execute(query, line)
            game_genre = cur.fetchall()
            all_ids.append(
                (game_genre[0]['game_id'], game_genre[0]['developer_id'],
                 game_genre[0]['game_id'], game_genre[0]['developer_id']))
    return all_ids


def add_to_genre_link_table(conn: connection, tuples: list, page_size=100) -> None:
    """Updates genre link table"""
    query = """INSERT INTO game_genre_link(game_id, genre_id) SELECT %s, %s
                WHERE NOT EXISTS (SELECT game_id, genre_id
                FROM game_genre_link WHERE game_id = %s AND genre_id = %s);"""
    with conn.cursor() as cur:
        try:
            execute_batch(cur, query, tuples, page_size)
            conn.commit()
            print("execute_batch() done")
        except Error as err:
            print(f"Error: {err}")
            conn.rollback()


def add_to_publisher_link_table(conn: connection, tuples: list, page_size=100) -> None:
    """Updates publisher link table"""
    query = """INSERT INTO game_publisher_link(game_id, publisher_id)
                SELECT %s, %s WHERE NOT EXISTS (SELECT game_id, publisher_id 
                FROM game_publisher_link WHERE game_id = %s AND publisher_id = %s);"""
    with conn.cursor() as cur:
        try:
            execute_batch(cur, query, tuples, page_size)
            conn.commit()
            print("execute_batch() done")
        except Error as err:
            print(f"Error: {err}")
            conn.rollback()


def add_to_developer_link_table(conn: connection, tuples: list, page_size=100) -> None:
    """Updates developer link table"""
    query = """INSERT INTO game_developer_link(game_id, developer_id)
                SELECT %s, %s WHERE NOT EXISTS (SELECT game_id, developer_id
                FROM game_developer_link WHERE game_id = %s AND developer_id = %s);"""
    with conn.cursor() as cur:
        try:
            execute_batch(cur, query, tuples, page_size)
            conn.commit()
            print("execute_batch() done")
        except Error as err:
            print(f"Error: {err}")
            conn.rollback()


def upload_developers(data: pd.DataFrame, conn: connection) -> None:
    """Uploads new developers"""
    developers_data = data['developers']
    execute_batch_columns(conn, developers_data,
                          'developer', 'developer_name', page_size=100)


def upload_publishers(data: pd.DataFrame, conn: connection) -> None:
    """Uploads new publishers"""
    publishers_data = data['publishers']
    execute_batch_columns(conn, publishers_data,
                          'publisher', 'publisher_name', page_size=100)


def upload_genres(data: pd.DataFrame, conn: connection) -> None:
    """Uploads new genres"""
    genres = data[["genre", "user_generated", "genre", "user_generated"]]
    execute_batch_columns_for_genres(conn, genres,
                                     'genre', page_size=100)


def upload_games(data: pd.DataFrame, conn: connection) -> None:
    """Uploads new games"""
    platform_cache = {}
    data['platform_id'] = data.apply(
        lambda row: get_existing_platform_data(
            row['mac'], row['windows'], row['linux'], conn, platform_cache), axis=1)

    new_game_data = data.rename(columns={'full_price': 'price'})

    games_to_load = new_game_data[[
        'app_id', 'title', 'release_date', 'price', 'sale_price', 'platform_id']]
    execute_batch_columns_for_games(conn, games_to_load,
                                    'game', page_size=100)


def upload_game_genre_link(data: pd.DataFrame, conn: connection) -> None:
    """Uploads to game_genre_linking table"""
    game_genre = data[["app_id", "genre", "user_generated"]]
    id_tuples = get_all_game_genre_ids(conn, game_genre)
    add_to_genre_link_table(conn, id_tuples, page_size=100)


def upload_game_publisher_link(data: pd.DataFrame, conn: connection) -> None:
    """Uploads to game_publisher table"""
    game_publisher = data[["app_id", "publishers"]].drop_duplicates()
    id_tuples = get_all_publisher_game_ids(conn, game_publisher)
    add_to_publisher_link_table(conn, id_tuples, page_size=100)


def upload_game_developer_link(data: pd.DataFrame, conn: connection) -> None:
    """Uploads to game_publisher table"""
    game_developer = data[["app_id", "developers"]].drop_duplicates()
    id_tuples = get_all_developer_game_ids(conn, game_developer)
    add_to_developer_link_table(conn, id_tuples, page_size=100)


if __name__ == "__main__":
    load_dotenv()
    configuration = environ
    connect_d = get_db_connection(configuration)

    final_df = pd.read_csv("genres.csv")
    game_data = pd.read_csv("final_games.csv")

    try:
        upload_publishers(final_df, connect_d)
        upload_developers(final_df, connect_d)
        upload_genres(final_df, connect_d)
        upload_games(game_data, connect_d)
        upload_game_genre_link(final_df, connect_d)
        upload_game_publisher_link(final_df, connect_d)
        upload_game_developer_link(final_df, connect_d)

    finally:
        connect_d.close()
