"""Validates received review inputs"""

from datetime import datetime

import pandas as pd
from pandas import DataFrame


def get_db_connection() -> connection:
    """Returns PSQL database connection"""
    return # TODO connection here


def get_release_date(game_id: int, conn: connection, cache: dict) -> datetime:
    """Retrieves the release date for a game with a provided ID"""
    if game_id in cache.keys():
        return cache[game_id]
    else:
        # TODO get data from connection
        cache[game_id] = # TODO value from above
        return cache[game_id]


def correct_playtime(reviews_df: DataFrame) -> DataFrame:
    """Returns a datatframe with valid playtime recordings only"""
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


if __name__ == "__main__":
    reviews = pd.read_csv("reviews.csv")
    reviews = correct_playtime(reviews)