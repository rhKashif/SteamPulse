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
            [data[10]])
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
    connection = get_db_connection(configuration)

    df = pd.read_csv("transformed_data.csv")
    for data in df.itertuples():
        print(data[2])

        break
