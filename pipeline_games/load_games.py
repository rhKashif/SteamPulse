"""Script for loading to database"""
from os import environ
from dotenv import load_dotenv
import pandas as pd
from psycopg2 import connect, DatabaseError
from psycopg2.extras import RealDictCursor, execute_batch


def get_db_connection(config):
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


def execute_batch_columns(conn, data_frame: pd.DataFrame, table: str, column: str, page_size=100):
    """Using psycopg2.extras.execute_batch() to insert the dataframe"""
    tuples = list(zip(data_frame['developers'].unique()))
    cols = column
    query = "INSERT INTO %s(%s) VALUES(%%s)" % (table, cols)
    cursor = conn.cursor()
    try:
        execute_batch(cursor, query, tuples, page_size)
        conn.commit()
    except (Exception, DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1
    print("execute_batch() done")
    cursor.close()


def add_game_information(conn, data: list):
    """Add game information to database"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT developer_id FROM developer WHERE developer_name = %s;""",
            [data[10]])
        developer_id = cur.fetchone()['developer_id']
        cur.execute(
            """SELECT publisher_id FROM publisher WHERE publisher_name = %s;""",
            [data[11]])
        publisher_id = cur.fetchone()['publisher_id']
        cur.execute(
            """SELECT platform_id FROM platform WHERE mac = %s AND windows = %s AND linux = %s;""",
            [data[8], data[7], data[9]])
        platform_id = cur.fetchone()['platform_id']
        cur.execute(
            """INSERT INTO game(app_id, title, release_date, price, sale_price, developer_id, publisher_id, platform_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);""",
            [data[2], data[3], data[4], data[5], data[6], developer_id, publisher_id, platform_id])
        conn.commit()
        cur.close()


def add_genre_information(conn, data: list):
    """Add genre information for specific game"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT game_id FROM game WHERE app_id = %s;""",
            [data[2]])
        game_id = cur.fetchone()['game_id']
        cur.execute(
            """INSERT INTO genre(genre, user_generated, game_id)
            VALUES (%s, %s, %s);""",
            [data[12], data[13], game_id])
        conn.commit()
        cur.close()


def get_existing_data(table_name: str, value: str, conn: connect, cache: dict):
    """Retrieves the existing data for a game with a provided value and table"""
    if value in cache.keys():
        return cache[value]
    else:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
        try: 
            cur.execute(
                """SELECT developer_id FROM developer WHERE developer_name = %s;""", [value])
            id_value = cur.fetchone()['developer_id']
        cache[value] = id_value
        except:
            ## add in the value if it does not exist and then return the cache
        return cache[value]


if __name__ == "__main__":
    load_dotenv()
    configuration = environ
    connection = get_db_connection(configuration)

    data_frame = pd.read_csv("genres.csv")

    developers_cache = {}
    data_frame["developers"] = data_frame["developers"].apply(lambda row: get_release_date("developers",
                                                                                           row, connection, developers_cache))

    print(developers_cache)

    # execute_batch_columns(connection, data_frame,'developer', 'developer_name', page_size=100)

    # execute_batch_columns(connection, data_frame,'publisher', 'publisher_name', page_size=100)
