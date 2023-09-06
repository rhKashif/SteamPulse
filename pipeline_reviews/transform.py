"""Validates received review inputs"""

from datetime import datetime
from os import environ

from dotenv import load_dotenv
import pandas as pd
from pandas import DataFrame
from psycopg2 import connect, Error
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor


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
        with conn.cursor() as cur:
            cur.execute("SELECT release_date FROM game WHERE app_id = %s;", [game_id])
            release_date = cur.fetchone()["release_date"]
        cache[game_id] = release_date
        return cache[game_id]


def correct_playtime(reviews_df: DataFrame) -> DataFrame:
    """Returns a data-frame with valid playtime recordings only"""
    try:
        release_date_cache = {}
        conn = get_db_connection()
        reviews_df["release_date"] = reviews_df["game_id"].apply(lambda row: get_release_date(
            row, conn, release_date_cache))
        time_now = datetime.now()
        reviews_df["maximum_playtime_since_release"] = reviews_df["release_date"].apply(
            lambda row: (time_now - row).total_seconds()/3600)
        reviews_df = reviews_df[
            reviews_df["playtime_at_review"] <= reviews_df["maximum_playtime_since_release"]]
        reviews_df = reviews_df[
            reviews_df["full_playtime"] <= reviews_df["maximum_playtime_since_release"]]
        reviews_df.drop(columns=["maximum_playtime_since_release","release_date"], inplace=True)
    except Error as e:
        print("Connection Error: ", e)
    return reviews_df


def remove_empty_rows(reviews_df: DataFrame) -> DataFrame:
    """Returns a data-frame without empty values in columns"""
    reviews_df.dropna(axis=1, how="any", inplace=True)
    return reviews_df


def change_column_types(reviews_df: DataFrame) -> DataFrame:
    """Returns a data-frame with correct data types"""
    columns_to_numeric = ["review_score","playtime_at_review","full_playtime"]

    for column in columns_to_numeric:
        reviews_df[column] = pd.to_numeric(reviews_df[column], errors="coerce")
        reviews_df = reviews_df.dropna(subset=[column])
    reviews_df["last_timestamp"] = reviews_df["last_timestamp"].apply(validate_time_string)
    return reviews_df


def validate_time_string(row: str) -> datetime | None:
    """Returns datetime object or None if wrong format"""
    try:
        return datetime.strptime(row, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return None


def correct_cell_values(reviews_df: DataFrame) -> DataFrame:
    """Drops rows with invalid cell values"""
    columns = ["review_score", "playtime_at_review", "full_playtime"]

    for column in columns:
        reviews_df = reviews_df[reviews_df[column] >= 0]
    # for reviews from players who did play the game
    reviews_df = reviews_df[reviews_df["playtime_at_review"] > 1]
    reviews_df = reviews_df[reviews_df["playtime_at_review"] <= reviews_df["full_playtime"]]
    return reviews_df


def remove_duplicate_reviews(review_df: DataFrame) -> DataFrame:
    """Removes duplicate rows"""
    review_df.drop_duplicates(
        subset=["review","game_id","playtime_at_review","full_playtime"], inplace=True)
    return review_df


if __name__ == "__main__":

    reviews = pd.read_csv("reviews.csv")
    reviews = change_column_types(reviews)
    reviews = remove_empty_rows(reviews)
    reviews = correct_cell_values(reviews)
    reviews = remove_duplicate_reviews(reviews)
    reviews = correct_playtime(reviews)
    if "Unnamed: 0" in reviews.columns:
        reviews.drop(columns="Unnamed: 0", inplace=True)
    reviews.to_csv("reviews2.csv") #! index=False potentially for load