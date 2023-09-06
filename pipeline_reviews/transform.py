"""Validates received review inputs"""

from datetime import datetime
from os import environ

import pandas as pd
from pandas import DataFrame
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor
from psycopg2 import connect
from psycopg2.extensions import connection


def get_db_connection() -> connection:
    """Returns PSQL database connection"""
    load_dotenv()
    return connect(dbname=environ["DATABASE_NAME"],
                    user=environ["DATABASE_USERNAME"],
                    host=environ["DATABASE_ENDPOINT"],
                    password=environ["DATABASE_PASSWORD"],
                    cursor_factory=RealDictCursor)


def get_release_date(game_id: int, conn: connection, cache: dict) -> datetime:
    """Retrieves the release date for a game with a provided ID"""
    if game_id in cache.keys():
        return cache[game_id]
    else:
        # TODO get data from connection
        cache[game_id] = # TODO value from above
        return cache[game_id]


def correct_playtime(reviews_df: DataFrame) -> DataFrame:
    """Returns a data-frame with valid playtime recordings only"""
    release_date_cache = {}
    conn = get_db_connection()
    reviews_df["release_date"] = reviews_df["game_id"].apply(lambda row: get_release_date(
        row, conn, release_date_cache))
    time_now = datetime.now()
    reviews_df["maximum_playtime_since_release"] = reviews_df["release_date"].apply(
        lambda row: (time_now - row).seconds/3600)
    reviews_df["playtime_at_review"] = reviews_df[
        reviews_df["playtime_at_review"] < reviews_df["maximum_playtime_since_release"]]
    reviews_df["full_playtime"] = reviews_df[
        reviews_df["full_playtime"] < reviews_df["maximum_playtime_since_release"]]
    reviews_df.drop(columns=["maximum_playtime_since_release","release_date"], inplace=False)
    return reviews_df


def remove_empty_rows(reviews_df: DataFrame) -> DataFrame:
    """Returns a data-frame without empty values in columns"""
    reviews_df = reviews_df[reviews_df["game_id"].notna() & reviews_df["review"].notna()
        & reviews_df["review_score"].notna() & reviews_df["playtime_at_review"].notna()
        & reviews_df["full_playtime"].notna()]
    return reviews_df


def change_column_types(reviews_df: DataFrame) -> DataFrame:
    """Returns a data-frame with correct data types"""
    # TODO


if __name__ == "__main__":

    reviews = pd.read_csv("reviews.csv")
    reviews = remove_empty_rows(reviews)
    reviews = change_column_types(reviews)
    reviews = correct_playtime(reviews)