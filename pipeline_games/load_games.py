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
    except TypeError:
        return "None"


def get_existing_data_for_genre(value: list, conn: connect, cache: dict) -> None:
    """Retrieves the existing data and adds to a cache dict given a provided value and table"""
    print(value)
    # if value in cache.keys():
    #    return cache[value]
    # try:
    #    with conn.cursor(cursor_factory=RealDictCursor) as cur:
   #         cur.execute("""SELECT genre_id FROM genre WHERE genre = %s AND user_generated = %s;""", [
    #                    genre, user])
   #         id_value = cur.fetchone()['genre_id']
    #        cache[value] = id_value
   #         cur.close()
   # except TypeError:
   #     return "None"


def check_if_in_cache(name: str, cache: dict) -> str | None:
    """Check if the name passed in exists int the cache dictionary"""
    if name in cache.keys():
        return None
    return name


def get_existing_platform_data(conn: connect) -> dict | None:
    """Retrieves the existing data and adds to a cache dict given a provided value and table"""
    cache = {}
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""SELECT * FROM platform;""")
            platforms = cur.fetchall()
            cur.close()
            for line in platforms:
                cache[line["platform_id"]] = dict(line)
            return cache
    except TypeError:
        return None


def add_game_information(conn, data: list, platform_value: int) -> None:
    """Add game information to database"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT exists (SELECT 1 FROM game WHERE app_id = %s LIMIT 1);""", [data[2]])
        result = cur.fetchone()
        if result['exists'] is True:
            cur.close()
        elif result['exists'] is False:
            cur.execute(
                """INSERT INTO game(app_id, title, release_date, price, sale_price, platform_id)
            VALUES (%s, %s, %s, %s, %s, %s);""",
                [data[2], data[3], data[4], data[5], data[6], platform_value])
        conn.commit()
        cur.close()


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


def find_platform_id_for_row(cache: dict, data: list) -> int:
    """Returns platform id based on cache dict for platform"""
    platforms_for_row = {'mac': data[8],
                         'windows': data[7], 'linux': data[9]}
    for key, value in cache.items():
        if platforms_for_row.items() <= value.items():
            return key
        return None


if __name__ == "__main__":
    load_dotenv()
    configuration = environ
    connection = get_db_connection(configuration)

    data_frame = pd.read_csv("genres.csv")
    game_data = pd.read_csv("final_games.csv")

    try:

        """developers_cache = {}
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
                              'publisher', 'publisher_name', page_size=100)"""

        genres_cache = {}
        data_frame['genre_id'] = data_frame.apply(
            lambda row: get_existing_data_for_genre(
                row, connection, genres_cache))

        genres_data = data_frame[data_frame.genre_id == "None"]
        # print(data_frame)

        # genres = data_frame.copy()
        # genres['genre'] = genres["genre"].apply(
        # lambda row: check_if_in_cache(row, genres_cache)).dropna(axis=0)
        # print(genres)

        # genres = genres[['genre', 'user_generated']].drop_duplicates()

        # execute_batch_columns_for_genres(connection, genres,
        # 'genre', page_size=100)

        """platform_cache = get_existing_platform_data(connection)

        for row in game_data.itertuples():
            platform_id = find_platform_id_for_row(platform_cache, row)
            add_game_information(connection, row, platform_id)

        for row in data_frame.itertuples():
            add_to_genre_link_table(connection, row)
            add_to_developer_link_table(connection, row)
            add_to_publisher_link_table(connection, row)"""

    finally:
        connection.close()
