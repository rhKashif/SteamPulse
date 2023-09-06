"""Script for loading to database"""
from os import environ
from dotenv import load_dotenv
import pandas as pd
from psycopg2 import connect
from psycopg2.extras import RealDictCursor


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


def execute_batch(conn, data_frame, table, page_size=100):
    """
    Using psycopg2.extras.execute_batch() to insert the dataframe
    """

    tuples = list(zip(data_frame['developers'].unique()))
    cols = ','.join(list(data_frame.columns))
    query = "INSERT INTO %s(%s) VALUES(%%s,%%s,%%s)" % (table, cols)
    cursor = conn.cursor()
    try:
        extras.execute_batch(cursor, query, tuples, page_size)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print("Error: %s" % error)
        conn.rollback()
        cursor.close()
        return 1
    print("execute_batch() done")
    cursor.close()


def add_developer_information(conn, data: list):
    """Add developer information to database"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT exists (SELECT 1 FROM developer WHERE developer_name = %s LIMIT 1);""", [data[10]])
        result = cur.fetchone()
        if result['exists'] is True:
            cur.close()
        elif result['exists'] is False:
            cur.execute(
                """INSERT INTO developer(developer_name) VALUES (%s);""", [data[10]])
        conn.commit()
        cur.close()


def add_publisher_information(conn, data: list):
    """Add publisher information to database"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT exists (SELECT 1 FROM publisher WHERE publisher_name = %s LIMIT 1);""", [data[11]])
        result = cur.fetchone()
        if result['exists'] is True:
            cur.close()
        elif result['exists'] is False:
            cur.execute(
                """INSERT INTO publisher(publisher_name) VALUES (%s);""", [data[11]])
        conn.commit()
        cur.close()


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


if __name__ == "__main__":
    load_dotenv()
    configuration = environ
    # connection = get_db_connection(configuration)

    """    df = pd.read_csv("final_games.csv")
    for data in df.itertuples():
        add_game_information(connection, data)"""

    data_frame = pd.read_csv("genres.csv")

    """for data in df.itertuples():
        add_developer_information(connection, data)
        add_publisher_information(connection, data)
        add_genre_information(connection, data)"""

    execute_batch(conn, data_frame, developers, page_size=100)
