"""Pipeline script to run all reviews extracting, transforming and loading"""

from datetime import datetime

from psycopg2 import Error

from extract import get_db_connection, get_game_ids, get_all_reviews, GamesNotFound
from transform import transform_reviews, remove_unnamed
from sentiment import isolate_non_stop_words, get_sentiment_per_game, get_sentiment_values
from load import get_game_ids_foreign_key_values, move_reviews_to_db

try:
    time_started = datetime.now()
    print("Extracting...")
    db_connection = get_db_connection()
    game_ids = get_game_ids(db_connection)
    # TODO add multiprocessing for this:
    reviews = get_all_reviews(game_ids)
    time_finished_extract = datetime.now()
    print(f"Total extraction time: {time_finished_extract - time_started} seconds.")
    print("Transforming...")
    reviews = transform_reviews(reviews)
    time_finished_transform = datetime.now()
    print(f"Total transforming time: {time_finished_transform - time_finished_extract} seconds.")
    print("Getting sentiment values...")
    reviews = isolate_non_stop_words(reviews)
    reviews = get_sentiment_values(reviews)
    each_game_sentiment = get_sentiment_per_game(reviews)
    reviews = remove_unnamed(reviews)
    time_finished_sent = datetime.now()
    print(f"Total sentiment value retrieval time: {time_finished_sent - time_finished_transform} seconds.")
    print("Loading...")
    reviews = get_game_ids_foreign_key_values(reviews)
    move_reviews_to_db(db_connection, reviews)
    time_finished_pipeline = datetime.now()
    print(f"Total time: {time_finished_pipeline - time_started} seconds.")
except Error as e:
    print("Connection Error: ", e)
except GamesNotFound as e:
    print(e)