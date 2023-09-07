"""Loads reviews into the database"""

import pandas as pd
from pandas import DataFrame
from psycopg2 import Error
from psycopg2.extensions import connection
from psycopg2.extras import execute_batch

from extract import get_db_connection
from transform import remove_unnamed, remove_empty_rows


def get_game_ids_foreign_key_values(reviews_df: DataFrame) -> DataFrame:
    """Returns data-frame with game_ids from db for
    foreign keys"""
    conn = get_db_connection()
    cache_dict = dict()
    reviews_df["game_id"] = reviews_df["game_id"].apply(
        lambda row: get_game_ids(conn, row, cache_dict))
    reviews_df = remove_empty_rows(reviews_df)
    return reviews_df


def get_game_ids(conn: connection, app_id: int, cache: dict) -> int | None:
    """Returns game_id from game table from db (foreign key)"""
    if str(app_id) in cache.keys():
        return cache[str(app_id)]
    try:
        with conn.cursor() as cur:
            cur.execute("""SELECT game_id FROM game WHERE app_id = %s""", app_id)
            game_id = cur.fetchone()
            conn.close()
            game_id = game_id[["game_id"]]
            cache[str(app_id)] = game_id
    except (Error, TypeError) as e:
        print("Error at load: ", e)
        return None
    return game_id


def move_reviews_to_db(conn: connection, reviews_df: DataFrame) -> None:
    """Moves all reviews into the database"""
    data_to_insert = [tuple(row[1:]) for row in reviews_df.values]
    execute_batch(conn.cursor(), """INSERT INTO review (game_id, review_text, review_score, review_date,
    playtime_at_review, sentiment) VALUES (%s, %s, %s, %s, %s, %s)""", data_to_insert)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    conn = get_db_connection()
    reviews = pd.read_csv("reviews.csv")
    reviews = remove_unnamed(reviews)
    move_reviews_to_db(conn, reviews)