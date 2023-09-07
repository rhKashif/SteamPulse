"""Script for loading to database"""
from os import environ
from dotenv import load_dotenv
import pandas as pd
from psycopg2 import connect, DatabaseError, sql
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
    tuples = tuples = list(zip(data_frame.unique()))
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


def get_existing_data(variable_name: str, table_name: str, value_name: str, value: str, conn: connect, cache: dict):
    """Retrieves the existing data and adds to a cache dict given a provided value and table"""
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                sql.SQL("""SELECT {variable_name} FROM {table_name} WHERE {value_name} = %s;""").format(
                    variable_name=sql.Identifier(variable_name), table_name=sql.Identifier(table_name),
                    value_name=sql.Identifier(value_name)), [value])
            id_value = cur.fetchone()[variable_name]
            cache[value] = id_value
    except:
        return None


def check_if_in_cache(name: str, cache: dict):
    if name in cache.keys():
        return None
    return name


if __name__ == "__main__":
    load_dotenv()
    configuration = environ
    connection = get_db_connection(configuration)

    data_frame = pd.read_csv("genres.csv")

    developers_cache = {}
    data_frame["developers"].apply(lambda row: get_existing_data("developer_id", "developer", "developer_name",
                                                                                 row, connection, developers_cache))
    new_developers = data_frame["developers"].apply(
        lambda row: check_if_in_cache(row, developers_cache)).dropna(axis=0)

    execute_batch_columns(connection, new_developers,
                          'developer', 'developer_name', page_size=100)

    # execute_batch_columns(connection, data_frame,'publisher', 'publisher_name', page_size=100)
