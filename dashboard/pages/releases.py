"""Python Script: Build a dashboard for data visualization (releases page)"""
from datetime import datetime, timedelta
from os import environ, _Environ

from dotenv import load_dotenv
from functools import reduce
import pandas as pd
from pandas import DataFrame
from psycopg2 import connect
from psycopg2.extensions import connection
import streamlit as st

from utility_functions import (get_database,
                               aggregate_data,
                               format_columns,
                               get_data_for_release_date_range,
                               format_database_columns,
                               build_sidebar_title,
                               build_sidebar_release_date,
                               build_sidebar_review_date,
                               build_sidebar_genre,
                               build_sidebar_developer,
                               build_sidebar_publisher,
                               build_sidebar_platforms,
                               build_sidebar_price,
                               build_sidebar_sentiment,
                               build_sidebar_number_of_reviews,
                               filter_data,
                               sidebar_header,
                               headline_figures,
                               sub_headline_figures,
                               format_sentiment_significant_figures)

SELECTED_RELEASES = "selected_releases"
SELECTED_RELEASE_DATES = "selected_release_dates"
SELECTED_REVIEW_DATES = "selected_review_dates"
SELECTED_GENRE = "selected_genre"
SELECTED_DEVELOPER = "selected_developer"
SELECTED_PUBLISHER = "selected_publisher"
SELECTED_PLATFORM = "selected_platform"
PRICE = "price"
MIN_PRICE = "min_price"
MAX_PRICE = "min_price"
SENTIMENT = "sentiment"
MIN_SENTIMENT = "min_sentiment"
MAX_SENTIMENT = "max_sentiment"
REVIEWS = "review"
MIN_REVIEWS = "min_reviews"
MAX_REVIEWS = "max_reviews"


def plot_new_games_today_table(df_releases: DataFrame) -> None:
    """
    Create a table for the new releases today

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases
    """
    df_releases = df_releases.drop_duplicates("title")

    desired_columns = ["title", "release_date",
                       "sale_price", "avg_sentiment", "num_of_reviews"]
    df_releases = df_releases[desired_columns]

    table_columns = ["Title", "Release Date",
                     "Price", "Community Sentiment", "Number of Reviews"]
    df_releases.columns = table_columns

    df_releases["Community Sentiment"] = df_releases["Community Sentiment"].apply(
        format_sentiment_significant_figures)

    df_releases['Community Sentiment'] = df_releases['Community Sentiment'].replace(
        "nan", "No Sentiment")

    df_releases = df_releases.sort_values(
        by=["Release Date"], ascending=False)
    df_releases = format_columns(df_releases)

    df_releases = df_releases.reset_index(drop=True)

    return {"table_data": df_releases, "title": "All New Releases"}


def dashboard_header() -> None:
    """
    Build header for dashboard to give it title text
    """

    st.title("SteamPulse")
    st.markdown("List of New Releases on Steam")


if __name__ == "__main__":

    load_dotenv()
    config = environ

    game_df = get_database()
    game_df = aggregate_data(game_df)
    game_df = format_database_columns(game_df)
    game_df = get_data_for_release_date_range(game_df, 14)

    dashboard_header()
    sidebar_header()

    filter_dict = {
        SELECTED_RELEASES: build_sidebar_title(game_df),
        SELECTED_RELEASE_DATES: build_sidebar_release_date(game_df),
        SELECTED_REVIEW_DATES: build_sidebar_review_date(game_df),
        SELECTED_GENRE: build_sidebar_genre(game_df),
        SELECTED_DEVELOPER: build_sidebar_developer(game_df),
        SELECTED_PUBLISHER: build_sidebar_publisher(game_df),
        SELECTED_PLATFORM: build_sidebar_platforms(),
        PRICE: build_sidebar_price(game_df),
        SENTIMENT: build_sidebar_sentiment(game_df),
        REVIEWS: build_sidebar_number_of_reviews(game_df),
    }
    filtered_df = filter_data(game_df, filter_dict)

    if filtered_df.empty:
        st.markdown(
            "### Invalid Filters\n There are no releases which fit your options")
    else:
        headline_figures(filtered_df)

        sub_headline_figures(filtered_df)

        game_table = plot_new_games_today_table(filtered_df)

        st.markdown(f"{game_table['title']}")
        st.table(game_table["table_data"].style.set_properties(
            **{'font-size': '16px'}))
