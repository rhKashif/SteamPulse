"""Python Script: Build a dashboard for data visualization (developer page)"""
from os import environ

import altair as alt
from altair.vegalite.v5.api import Chart
from dotenv import load_dotenv
import pandas as pd
from pandas import DataFrame
import streamlit as st

from utility_functions import (get_database,
                               aggregate_data,
                               format_database_columns,
                               get_data_for_release_date_range,
                               sidebar_header,
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
                               headline_figures,
                               sub_headline_figures,
                               two_column_chart_figures)

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


def plot_games_release_frequency(df_releases: DataFrame) -> Chart:
    """
    Create a line chart for the number of games released per day

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby("release_date")[
        "title"].nunique().reset_index()
    df_releases.columns = ["release_date", "num_of_games"]

    chart = alt.Chart(df_releases).mark_line(
        color="#44bd4f"
    ).encode(
        x=alt.X("release_date:O", title="Release Date",
                timeUnit="yearmonthdate"),
        y=alt.Y("num_of_games:Q", title="Number of Games")
    ).properties(
        title="New Releases per Day",
    )

    return chart


def plot_games_review_frequency(df_releases: DataFrame) -> Chart:
    """
    Create a line chart for the number of games released per day

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby(
        "review_date")["review_text"].nunique().reset_index()

    df_releases.columns = ["review_date", "num_of_reviews"]

    chart = alt.Chart(df_releases).mark_line(
        color="#44bd4f"
    ).encode(
        x=alt.X("review_date:O", title="Review Date",
                timeUnit="yearmonthdate"),
        y=alt.Y("num_of_reviews:Q", title="Number of Reviews"),
    ).properties(
        title="New Reviews per Day",
    )

    return chart


def plot_average_sentiment_per_game(df_releases: DataFrame) -> Chart:
    """
    Create a bar chart for the average sentiment per game

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

        rows (int): An integer value representing the number of rows to be displayed

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby(
        "title")["sentiment"].mean().reset_index().dropna()

    df_releases.columns = ["title", "average_sentiment"]

    chart = alt.Chart(df_releases).mark_bar(
    ).encode(
        x=alt.X("average_sentiment", title="Average Sentiment"),
        y=alt.Y("title", title="Release Title")
    ).properties(
        title="Releases: Sentiment Score",
    )

    return chart


def plot_reviews_per_game_frequency(df_releases: DataFrame) -> Chart:
    """
    Create a bar chart for the number of reviews per game

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

        rows (int): An integer value representing the number of rows to be displayed


    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.dropna().groupby(
        "title")["review_text"].nunique().reset_index()

    df_releases.columns = ["title", "num_of_reviews"]

    chart = alt.Chart(df_releases).mark_bar(
    ).encode(
        x=alt.X("num_of_reviews", title="Number of Reviews"),
        y=alt.Y("title", title="Release Title")
    ).properties(
        title="Releases: Most Reviewed",
    )

    return chart


def plot_average_sentiment_per_developer(df_releases: DataFrame) -> Chart:
    """
    Create a bar chart for the average sentiment per developer

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

        rows (int): An integer value representing the number of rows to be displayed

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby(
        "developer_name")["sentiment"].mean().reset_index().dropna().sort_values(by=["sentiment"])

    df_releases.columns = ["developer", "average_sentiment"]

    chart = alt.Chart(df_releases).mark_bar(
    ).encode(
        x=alt.X("average_sentiment", title="Average Sentiment"),
        y=alt.Y("developer", title="Release Title", sort="-x")
    ).properties(
        title="Developers: Sentiment Score",
    )

    return chart


def plot_average_sentiment_per_publisher(df_releases: DataFrame) -> Chart:
    """
    Create a bar chart for the average sentiment per publisher

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

        rows (int): An integer value representing the number of rows to be displayed

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby(
        "publisher_name")["sentiment"].mean().reset_index().dropna().sort_values(by=["sentiment"])

    df_releases.columns = ["publisher", "average_sentiment"]

    chart = alt.Chart(df_releases).mark_bar(
    ).encode(
        x=alt.X("average_sentiment", title="Average Sentiment"),
        y=alt.Y("publisher", title="Release Title", sort="-x")
    ).properties(
        title="Publishers: Sentiment Score",
    )

    return chart


def plot_platform_distribution(df_releases: DataFrame) -> Chart:
    """
    Create a bar chart for the platform compatibility of games

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    try:
        mac_compatibility = df_releases.groupby("mac")['title'].nunique()[True]
    except KeyError:
        mac_compatibility = 0
    try:
        windows_compatibility = df_releases.groupby(
            "windows")['title'].nunique()[True]
    except KeyError:
        windows_compatibility = 0
    try:
        linux_compatibility = df_releases.groupby(
            "linux")['title'].nunique()[True]
    except KeyError:
        linux_compatibility = 0

    compatibility_df = pd.DataFrame({"platform": ['mac', 'windows', "linux"],
                                     "compatibility": [mac_compatibility, windows_compatibility, linux_compatibility]})

    chart = alt.Chart(compatibility_df).mark_bar().encode(
        x=alt.X("compatibility", title="Compatible Games"),
        y=alt.Y("platform", title="Platform", sort="-x"),
    ).properties(
        title="Releases Compatibility per Platform",
        width=800,
        height=350
    )

    return chart


def plot_genre_by_release(df_releases: DataFrame) -> Chart:
    """
    Create a line chart for the number of games released per day

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases[["game_id", "title", "genre"]]

    df_releases = df_releases.drop_duplicates()

    df_releases = df_releases.groupby(
        "genre").size().reset_index().sort_values(by=[0])

    chart = alt.Chart(df_releases).mark_bar().encode(
        x=alt.Y("0:Q",
                title="Number of Releases"),
        y=alt.X("genre:N", title="Genre", sort="-x")
    ).properties(
        title="Genre Popularity by Number of Releases",
    )

    return chart


def plot_genre_by_sentiment(df_releases: DataFrame) -> Chart:
    """
    Create a line chart for the number of games released per day

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases[["game_id", "title", "genre", "avg_sentiment"]]
    df_releases = df_releases.drop_duplicates()

    df_releases_sentiment_sum = df_releases.groupby(
        "genre")["avg_sentiment"].mean().reset_index().sort_values(by=["avg_sentiment"]).dropna()

    print(df_releases_sentiment_sum)

    chart = alt.Chart(df_releases_sentiment_sum).mark_bar().encode(
        x=alt.Y("avg_sentiment:Q",
                title="Average Sentiment"),
        y=alt.X("genre:N", title="Genre", sort="-x")
    ).properties(
        title="Genre Popularity by Community Sentiment",
    )

    return chart


def plot_price_distribution(df_releases: DataFrame) -> Chart:
    """
    Create a histogram chart for range of game price

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.drop_duplicates("title")

    chart = alt.Chart(df_releases).mark_bar().encode(
        alt.X('price:Q', bin=alt.Bin(maxbins=20), title='Game Price Range'),
        alt.Y('count():Q', title='Number of Games')
    ).properties(
        title='Game Price Range Histogram',
    )

    return chart


def dashboard_header() -> None:
    """
    Build header for dashboard to give it title text
    """

    st.title("SteamPulse")
    st.markdown("Developer Insights for New Releases on Steam")


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
            "### Invalid:\n No releases to display")
    else:
        headline_figures(filtered_df)

        sub_headline_figures(filtered_df)

        games_release_frequency_plot = plot_games_release_frequency(
            filtered_df)
        games_review_frequency_plot = plot_games_review_frequency(
            filtered_df)

        games_platform_distribution_plot = plot_platform_distribution(
            filtered_df)
        games_price_distribution_plot = plot_price_distribution(filtered_df)

        trending_sentiment_per_game_plot = plot_average_sentiment_per_game(
            filtered_df)
        trending_reviews_per_game_plot = plot_reviews_per_game_frequency(
            filtered_df)

        trending_sentiment_per_developer_plot = plot_average_sentiment_per_developer(
            filtered_df)
        trending_sentiment_per_publisher_plot = plot_average_sentiment_per_publisher(
            filtered_df)

        games_genre_by_release_plot = plot_genre_by_release(filtered_df)
        games_genre_by_sentiment_plot = plot_genre_by_sentiment(filtered_df)

        two_column_chart_figures(games_release_frequency_plot,
                                 games_review_frequency_plot)
        two_column_chart_figures(games_platform_distribution_plot,
                                 games_price_distribution_plot)
        two_column_chart_figures(trending_sentiment_per_game_plot,
                                 trending_reviews_per_game_plot)
        two_column_chart_figures(trending_sentiment_per_developer_plot,
                                 trending_sentiment_per_publisher_plot)
        two_column_chart_figures(games_genre_by_release_plot,
                                 games_genre_by_sentiment_plot)
