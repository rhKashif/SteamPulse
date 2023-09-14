"""Retrieves reviews for a game from game IDs"""

from datetime import datetime
from os import environ
from urllib.parse import quote_plus

from pandas import DataFrame
from dotenv import load_dotenv
from psycopg2 import connect
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor
import requests


class GamesNotFound(Exception):
    """Exception class for when a game is not found. Returns a message"""

    def __init__(self, message="No new games were found in the last 2 weeks!"):
        super().__init__(message)


def get_number_of_reviews(game_id: int) -> int:
    """Retrieves total number of all reviews from a given game ID"""
    try:
        request = requests.get(
            f"https://store.steampowered.com/appreviews/{game_id}?json=1", timeout=10)
        reviews_info = request.json()
        return reviews_info["query_summary"]["total_reviews"]
    except requests.exceptions.Timeout:
        return 0


def get_reviews_for_game(game_id: int, cursor: str) -> dict:
    """Retrieves all reviews from a given review page (cursor)
    for a chosen game by its ID"""
    cursor = quote_plus(cursor)

    try:
        request = requests.get(f"""https://store.steampowered.com/appreviews/
                {game_id}?json=1&num_per_page=100&language=english&cursor={cursor}""", timeout=10)
        reviews = request.json()
        next_cursor = reviews["cursor"]

    except requests.exceptions.Timeout:
        return {"error": "Timeout on the response!"}
    page_reviews = []

    for review in reviews["reviews"]:
        review_dict = {}
        review_dict["game_id"] = game_id
        review_dict["review"] = review["review"]
        review_dict["review_score"] = review["votes_up"]
        review_dict["last_timestamp"] = datetime.fromtimestamp(
            review["timestamp_created"]).strftime("%Y-%m-%d %H:%M:%S")
        review_dict["playtime_last_2_weeks"] = review["author"]["playtime_forever"]
        page_reviews.append(review_dict)
    return {"next_cursor": next_cursor, "reviews": page_reviews}


def get_all_reviews(game_ids: list[int]) -> DataFrame:
    """Combines all reviews together and all review
    information together to be set in a data-frame"""
    all_reviews = []

    for game in game_ids:
        number_of_total_reviews = get_number_of_reviews(game)

        if number_of_total_reviews:
            cursor_list = ["*"]
            cursor = ""
            while cursor not in cursor_list:
                api_response = get_reviews_for_game(game, cursor_list[-1])
                if "error" not in api_response:
                    cursor = api_response["next_cursor"]
                    page_reviews = api_response["reviews"]
                    if not page_reviews or cursor in cursor_list:
                        break
                    cursor_list.append(cursor)
                    all_reviews.extend(page_reviews)
    return DataFrame(all_reviews)


def get_db_connection() -> connection:
    """Returns PSQL database connection"""
    load_dotenv()
    return connect(dbname=environ["DATABASE_NAME"],
                   user=environ["DATABASE_USERNAME"],
                   host=environ["DATABASE_ENDPOINT"],
                   password=environ["DATABASE_PASSWORD"],
                   cursor_factory=RealDictCursor)


def get_game_ids(conn: connection) -> list[int] | None:
    """Returns game IDs from the past 2 weeks"""
    with conn.cursor() as cur:
        cur.execute("""SELECT app_id FROM game WHERE release_date
    BETWEEN NOW() - INTERVAL '2 WEEKS' AND NOW()""")
        game_ids = cur.fetchall()
    if game_ids:
        return [game_id["app_id"] for game_id in game_ids]
    else:
        raise GamesNotFound()
