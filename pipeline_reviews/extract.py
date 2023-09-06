"""Retrieves reviews for a game from game IDs"""

from datetime import datetime
from urllib.parse import quote_plus

import pandas as pd
import requests


def get_review_info_for_game(game_id: int) -> dict:
    """Retrieves information about all reviews from a given game ID"""
    request = requests.get(f"https://store.steampowered.com/appreviews/{game_id}?json=1")
    reviews_info = request.json()
    return {"game_id": game_id, "number_of_total_reviews": reviews_info["query_summary"]["total_reviews"],
            "number_of_positive_reviews": reviews_info["query_summary"]["total_positive"],
            "number_of_negative_reviews": reviews_info["query_summary"]["total_negative"]}


def get_reviews_for_game(game_id: int, cursor: str) -> dict:
    """Retrieves all reviews from a given review page (cursor)
    for a chosen game by its ID"""
    cursor = quote_plus(cursor)

    try:
        request = requests.get(f"""https://store.steampowered.com/appreviews/{game_id}
                    ?json=1&num_per_page=100&cursor={cursor}""", timeout=10)
        reviews = request.json()
        next_cursor = reviews["cursor"]

    except requests.exceptions.Timeout:
        return {"error": "Timeout on the response!"}
    page_reviews = []

    for review in reviews["reviews"]:
        review_dict = dict()
        review_dict["game_id"] = game_id
        review_dict["review"] = review["review"]
        review_dict["review_score"] = review["votes_up"]
        review_dict["last_timestamp"] = datetime.fromtimestamp(
            review["timestamp_updated"]).strftime("%Y-%m-%d %H:%M:%S")
        review_dict["playtime_at_review"] = review["author"]["playtime_at_review"]
        review_dict["full_playtime"] = review["author"]["playtime_forever"]
        page_reviews.append(review_dict)
    return {"next_cursor": next_cursor, "reviews": page_reviews}


def get_all_reviews(game_ids: list[int]) -> None:
    """Combines all reviews together and all review
    information together to be set in a data-frame"""
    reviews_info = []

    for game in game_ids:
        reviews_info.append(get_review_info_for_game(game))
        if reviews_info[-1]["number_of_total_reviews"] == 0:
            continue

        cursor_list = ["*"]
        all_reviews = []

        for page in range(int(reviews_info[-1]["number_of_total_reviews"]/100)+2):
            api_response = get_reviews_for_game(game, cursor_list[page])
            if "error" in list(api_response.keys()):
                continue
            cursor = api_response["next_cursor"]
            page_reviews = api_response["reviews"]
            if not page_reviews or cursor in cursor_list:
                break
            if not cursor in cursor_list:
                cursor_list.append(cursor)
            all_reviews.extend(page_reviews)
    make_csv_files(all_reviews, reviews_info)


def make_csv_files(all_reviews: list[dict], reviews_info: list[dict]) -> None:
    """Makes data-frames from lists and creates
    csv files from both"""
    pd.DataFrame(all_reviews).to_csv("reviews.csv")
    pd.DataFrame(reviews_info).to_csv("review_info.csv")


if __name__ == "__main__":
    game_ids = [10, 666000, 15, 223056] # TODO connect to script with list of game IDs
    get_all_reviews(game_ids)
