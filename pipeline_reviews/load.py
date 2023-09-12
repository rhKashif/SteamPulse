"""Loads reviews into the database"""

from pandas import DataFrame
from psycopg2 import Error
from psycopg2.extensions import connection
from psycopg2.extras import execute_batch

from transform import remove_empty_rows


def get_game_ids_foreign_key_values(conn: connection, reviews_df: DataFrame) -> DataFrame:
    """Returns data-frame with game_ids from db for
    foreign keys"""
    cache_dict = {}
    reviews_df["game_id"] = reviews_df["game_id"].apply(
        lambda row: get_game_ids(conn, row, cache_dict))
    reviews_df = remove_empty_rows(reviews_df)
    return reviews_df


def get_game_ids(conn: connection, app_id: int, cache: dict) -> int | None:
    """Returns game_id from game table from db (foreign key)"""
    if str(app_id) in cache:
        return cache[str(app_id)]
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT game_id FROM game WHERE app_id = %s""", (app_id,))
            game_id = cur.fetchone()
        game_id = game_id["game_id"]
        cache[str(app_id)] = game_id
    except (Error, TypeError) as err:
        print("Error at load: ", err)
        return None
    return game_id


def move_reviews_to_db(conn: connection, reviews_df: DataFrame) -> None:
    """Moves all reviews into the database"""
    data_to_insert = [tuple(row) for row in reviews_df.values]
    try:
        with conn.cursor() as cur:
            execute_batch(cur, """INSERT INTO review (game_id, review_text, review_score, reviewed_at,
        playtime_last_2_weeks, sentiment) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""", data_to_insert)
            conn.commit()
    except Error as err:
        print("Error at load: ", err)
    finally:
        conn.close()
