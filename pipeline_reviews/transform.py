"""Validates received review inputs"""

from datetime import datetime, date

import pandas as pd
from pandas import DataFrame
from psycopg2 import Error
from psycopg2.extensions import connection

from extract import get_db_connection


def get_release_date(game_id: int, conn: connection, cache: dict) -> date:
    """Retrieves the release date for a game with a provided ID"""
    if game_id in cache:
        return cache[game_id]
    with conn.cursor() as cur:
        cur.execute("SELECT release_date FROM game WHERE app_id = %s;", [game_id])
        release_date = cur.fetchone()["release_date"]
    cache[game_id] = release_date
    return cache[game_id]


def correct_playtime(reviews_df: DataFrame) -> DataFrame:
    """Returns a data-frame with valid playtime recordings only"""
    try:
        reviews_df_copy = reviews_df.copy()
        release_date_cache = {}
        conn = get_db_connection()
        reviews_df_copy["release_date"] = reviews_df_copy["game_id"].apply(lambda row: get_release_date(
            row, conn, release_date_cache))
        conn.close()
        time_now = datetime.now().date()
        reviews_df_copy["maximum_playtime_since_release"] = reviews_df_copy["release_date"].apply(
            lambda row: (time_now - row).total_seconds()/3600)
        reviews_df_copy = reviews_df_copy[
            reviews_df_copy["playtime_at_review"] <= reviews_df_copy["maximum_playtime_since_release"]]
        reviews_df_copy.drop(columns=["maximum_playtime_since_release","release_date"], inplace=True)
    except (Error, ValueError) as e:
        print("Error at transform: ", e)
    return reviews_df_copy


def remove_empty_rows(reviews_df: DataFrame) -> DataFrame:
    """Returns a data-frame without empty values in columns"""
    reviews_df.dropna(axis=0, how="any", inplace=True)
    return reviews_df


def change_column_types(reviews_df: DataFrame) -> DataFrame:
    """Returns a data-frame with correct data types"""
    columns_to_numeric = ["review_score","playtime_at_review"]

    for column in columns_to_numeric:
        reviews_df[column] = pd.to_numeric(reviews_df[column], errors="coerce")
        reviews_df = reviews_df.dropna(subset=[column])
    reviews_df["last_timestamp"] = reviews_df["last_timestamp"].apply(validate_time_string)
    return reviews_df


def validate_time_string(row: str) -> date | None:
    """Returns datetime object or None if wrong format"""
    try:
        return datetime.strptime(row, "%Y-%m-%d %H:%M:%S").date()
    except (TypeError, ValueError):
        return None


def correct_cell_values(reviews_df: DataFrame) -> DataFrame:
    """Drops rows with invalid cell values"""
    reviews_df = reviews_df[reviews_df["review_score"] >= 0]
    # for reviews from players who did play the game
    reviews_df = reviews_df[reviews_df["playtime_at_review"] >= 1]
    return reviews_df


def remove_duplicate_reviews(review_df: DataFrame) -> DataFrame:
    """Removes duplicate rows"""
    review_df.drop_duplicates(
        subset=["review","game_id","playtime_at_review"], inplace=True)
    return review_df


def remove_unnamed(reviews_df: DataFrame) -> DataFrame:
    """Removes automatically generated unnamed column"""
    reviews_df_copy = reviews_df.copy()
    if "Unnamed: 0" in reviews_df.columns:
        reviews_df_copy.drop(columns="Unnamed: 0", inplace=True)
    return reviews_df_copy


if __name__ == "__main__":

    reviews = pd.read_csv("reviews.csv")
    reviews = change_column_types(reviews)
    reviews = remove_empty_rows(reviews)
    reviews = correct_cell_values(reviews)
    reviews = remove_duplicate_reviews(reviews)
    reviews = correct_playtime(reviews)
    reviews = remove_unnamed(reviews)
    reviews.to_csv("reviews.csv") #! index=False potentially for load
