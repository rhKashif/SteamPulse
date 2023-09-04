"""Retrieves reviews for a game from game IDs"""

from urllib.parse import quote_plus
from datetime import datetime

import requests
import pandas as pd


def get_review_info_for_game(game_id: int) -> dict:
    """Retrieves information about all reviews from a given game ID"""
    request = requests.get(f"https://store.steampowered.com/appreviews/{game_id}?json=1")
    reviews_info = request.json()
    return {"number_of_total_reviews": reviews_info["query_summary"]["total_reviews"],
            "number_of_positive_reviews": reviews_info["query_summary"]["total_positive"],
            "number_of_negative_reviews": reviews_info["query_summary"]["total_negative"]}


def get_reviews_for_game(game_id: int, cursor: str) -> (str,list[dict]):
    """Retrieves all reviews from a given review page (cursor)
    for a chosen game by its ID"""
    cursor = quote_plus(cursor)
    request = requests.get(f"""https://store.steampowered.com/appreviews/{game_id}
                ?json=1&num_per_page=100&cursor={cursor}""")
    reviews = request.json()
    next_cursor = reviews["cursor"]
    page_reviews = []

    for review in reviews["reviews"]:
        review_dict = dict()
        review_dict["game_id"] = game_id
        review_dict["review"] = review["review"]
        review_dict["review_score"] = review["votes_up"]
        review_dict["last_timestamp"] = datetime.fromtimestamp(review["timestamp_updated"]).strftime("%Y-%m-%d %H:%M:%S")
        review_dict["playtime_at_review"] = review["author"]["playtime_at_review"]
        review_dict["full_playtime"] = review["author"]["playtime_forever"]
        page_reviews.append(review_dict)
    return next_cursor, page_reviews


def get_all_reviews(game_ids: list[int]) -> None:
    """Creates a csv file for all review info and
    reviews for each game csv file"""
    review_info = []

    for game in game_ids:
        review_info.append(get_review_info_for_game(game))
        if review_info[-1]["number_of_total_reviews"] == 0:
            continue

        cursor_list = ["*"]
        all_reviews = []

        for page in range(int(review_info[-1]["number_of_total_reviews"]/100)+2):
            cursor, page_reviews = get_reviews_for_game(game, cursor_list[page])
            if not page_reviews or cursor in cursor_list:
                break
            if not cursor in cursor_list:
                cursor_list.append(cursor)
            all_reviews.extend(page_reviews)
    pd.DataFrame(all_reviews).to_csv("reviews.csv")
    pd.DataFrame(review_info).to_csv("review_info.csv")


if __name__ == "__main__":
    game_ids = get_game_ids() # TODO connect to script with list of game IDs
    get_all_reviews(game_ids)
