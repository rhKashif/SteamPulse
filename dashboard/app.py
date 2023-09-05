"""Python Script: Build a dashboard for data visualization"""
import altair as alt
from os import environ, _Environ
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
from pandas import DataFrame
import streamlit as st
from psycopg2 import connect
from psycopg2.extensions import connection

st.set_page_config(layout="wide")


def get_db_connection(config_file: _Environ) -> connection:
    """
    Returns connection to the database

    Args:
        config (_Environ): A file containing sensitive values

    Returns:
        connection: A connection to a Postgres database
    """
    try:
        return connect(
            database=config_file["DB_NAME"],
            user=config_file["DB_USER"],
            password=config_file["DB_PASSWORD"],
            port=config_file["DB_PORT"],
            host=config_file["DB_HOST"]
        )
    except Exception as err:
        print("Error connecting to database.")
        raise err


def get_database(conn_postgres: connection) -> DataFrame:
    """
    Returns redshift database transaction table as a DataFrame Object

    Args:
        conn_postgres (connection): A connection to a Postgres database

    Returns:
        DataFrame:  A pandas DataFrame containing all relevant plant data
    """
    query = f""
    df = pd.read_sql_query(query, conn_postgres)

    return df


def dashboard_header() -> None:
    """
    Build header for dashboard to give it a title

    Args:
        None

    Returns:
        None
    """

    st.title("SteamPulse")
    st.markdown("Community Insights for New Releases on Steam")


def build_sidebar_title(df: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options

    Args:
        df (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list:  A list with game titles that the user selected
    """
    titles = st.sidebar.multiselect(
        "Game Title:", options=sorted(df["title"].unique()))
    return titles


def build_sidebar_release_date(df: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select release dates

    Args:
        df (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with release dates that the user selected
    """
    release_dates = st.sidebar.multiselect(
        "Release Date:", options=df["release_date"].dt.date.unique())
    return release_dates


def build_sidebar_review_date(df: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select review dates

    Args:
        df (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with review dates that the user selected
    """
    dates = st.sidebar.multiselect(
        "Review Date:", options=df["review_date"].dt.date.unique())
    return dates


def build_sidebar_genre(df: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select game genre

    Args:
        df (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with game genres that the user selected
    """
    dates = st.sidebar.multiselect(
        "Genre:", options=df["genre"].unique())
    return dates


def build_sidebar_platforms() -> list:
    """
    Build sidebar with platform selection options

    Returns:
        list: A list with selected platforms
    """
    platforms = ["mac", "windows", "linux"]
    selected_platforms = st.sidebar.multiselect(
        "Compatible Platforms:", options=platforms, default=platforms)
    return selected_platforms


def build_sidebar_sentiment(df: DataFrame) -> tuple:
    """
    Build sidebar with slider option to select range for review sentiment

    Args:
        df (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A tuple with minimum and maximum sentiment that the user has selected
    """
    sentiment = st.sidebar.slider(
        "Sentiment:", min_value=0.0, max_value=5.0, value=(0.0, 5.0), step=0.1)
    return sentiment


def headline_figures(df: DataFrame, titles: list[str], release_dates: list[datetime], review_dates: list[datetime], genres: list[str], platforms: list[str], minimum_sentiment: float, maximum_sentiment: float) -> None:
    """
    Build headline for dashboard to present key figures for quick view of overall data

    Args:
        df (DataFrame): A pandas DataFrame containing all relevant game data

        titles (list[str]):  A list with game titles that the user selected

        release_dates (list[datetime]): A list with release dates that the user selected

        review_dates (list[datetime]): A list with review dates that the user selected

        genres (list[str]): A list with game genres that the user selected

        platforms (list[str]): A list with selected platforms

    Returns:
        None
    """
    if len(titles) != 0:
        df = df[df["title"].isin(titles)]
    if len(release_dates) != 0:
        df = df[df["release_date"].dt.floor("D").isin(release_dates)]
    if len(review_dates) != 0:
        df = df[df["release_date"].dt.floor("D").isin(review_dates)]
    if len(genres) != 0:
        df = df[df["genre"].isin(genres)]
    df = df[df[platforms].any(axis=1)]
    df = df[(df['sentiment'] >= min_sentiment) &
            (df['sentiment'] <= max_sentiment)]

    cols = st.columns(3)

    with cols[0]:
        st.metric("Total Games:", df["title"].nunique())
    with cols[1]:
        st.metric("Total Reviews:",
                  df.shape[0])
    with cols[2]:
        st.metric("Average Sentiment:", df["sentiment"].mean())


def plot_reviews_per_game(df: DataFrame, titles: list[str], release_dates: list[datetime], review_dates: list[datetime], genres: list[str], platforms: list[str], minimum_sentiment: float, maximum_sentiment: float) -> None:
    """
    Create a bar chart for the number of reviews per game

    Args:
        df (DataFrame): A pandas DataFrame containing all relevant game data

        titles (list[str]):  A list with game titles that the user selected

        release_dates (list[datetime]): A list with release dates that the user selected

        review_dates (list[datetime]): A list with review dates that the user selected

        genres (list[str]): A list with game genres that the user selected

        platforms (list[str]): A list with selected platforms

    Returns:
        None
    """
    if len(titles) != 0:
        df = df[df["title"].isin(titles)]
    if len(release_dates) != 0:
        df = df[df["release_date"].dt.floor("D").isin(release_dates)]
    if len(review_dates) != 0:
        df = df[df["release_date"].dt.floor("D").isin(review_dates)]
    if len(genres) != 0:
        df = df[df["genre"].isin(genres)]
    df = df[df[platforms].any(axis=1)]
    df = df[(df['sentiment'] >= min_sentiment) &
            (df['sentiment'] <= max_sentiment)]

    df = df.groupby(
        "title").size().reset_index()
    df.columns = ["title", "num_of_reviews"]

    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X("title", title="Game Title", sort="-x"),
        y=alt.Y("num_of_reviews", title="Number of reviews"),
    ).properties(
        title="Number of Reviews per Game",
        width=800,
        height=400
    )

    # chart = alt.Chart(df).mark_bar().encode(
    #     x=alt.X("num_of_reviews", title="Number of reviews"),
    #     y=alt.Y("title", title="Game Title", sort="-x")
    # ).properties(
    #     title="Number of Reviews per Game",
    #     width=800,
    #     height=400
    # )

    st.altair_chart(chart, use_container_width=True)


def plot_games_release_frequency(df: DataFrame, titles: list[str], release_dates: list[datetime], review_dates: list[datetime], genres: list[str], platforms: list[str], minimum_sentiment: float, maximum_sentiment: float) -> None:
    """
    Create a line chart for the number of games released per day

    Args:
        df (DataFrame): A pandas DataFrame containing all relevant game data

        titles (list[str]):  A list with game titles that the user selected

        release_dates (list[datetime]): A list with release dates that the user selected

        review_dates (list[datetime]): A list with review dates that the user selected

        genres (list[str]): A list with game genres that the user selected

        platforms (list[str]): A list with selected platforms

    Returns:
        None   
    """
    if len(titles) != 0:
        df = df[df["title"].isin(titles)]
    if len(release_dates) != 0:
        df = df[df["release_date"].dt.floor("D").isin(release_dates)]
    if len(review_dates) != 0:
        df = df[df["release_date"].dt.floor("D").isin(review_dates)]
    if len(genres) != 0:
        df = df[df["genre"].isin(genres)]
    df = df[df[platforms].any(axis=1)]
    df = df[(df['sentiment'] >= min_sentiment) &
            (df['sentiment'] <= max_sentiment)]

    df = game_df.groupby("release_date")["title"].nunique().reset_index()
    df.columns = ["release_date", "count"]

    chart = alt.Chart(df).mark_line().encode(
        x=alt.X("release_date:O", title="Release Date",
                timeUnit="yearmonthdate"),
        y=alt.Y("count", title="Number of games"),
    ).properties(
        title="Games Released per Day"
    )

    st.altair_chart(chart, use_container_width=True)


def plot_games_review_frequency(df: DataFrame, titles: list[str], release_dates: list[datetime], review_dates: list[datetime], genres: list[str], platforms: list[str], minimum_sentiment: float, maximum_sentiment: float) -> None:
    """
    Create a line chart for the number of games released per day

    Args:
        df (DataFrame): A pandas DataFrame containing all relevant game data

        titles (list[str]):  A list with game titles that the user selected

        release_dates (list[datetime]): A list with release dates that the user selected

        review_dates (list[datetime]): A list with review dates that the user selected

        genres (list[str]): A list with game genres that the user selected

        platforms (list[str]): A list with selected platforms

    Returns:
        None   
    """
    if len(titles) != 0:
        df = df[df["title"].isin(titles)]
    if len(release_dates) != 0:
        df = df[df["release_date"].dt.floor("D").isin(release_dates)]
    if len(review_dates) != 0:
        df = df[df["release_date"].dt.floor("D").isin(review_dates)]
    if len(genres) != 0:
        df = df[df["genre"].isin(genres)]
    df = df[df[platforms].any(axis=1)]
    df = df[(df['sentiment'] >= min_sentiment) &
            (df['sentiment'] <= max_sentiment)]

    df = df.groupby(
        "release_date").size().reset_index()
    df.columns = ["release_date", "num_of_reviews"]
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X("release_date:O", title="Release Date",
                timeUnit="yearmonthdate"),
        y=alt.Y("num_of_reviews", title="Number of reviews"),
    ).properties(
        title="Games Reviews per Day"
    )

    st.altair_chart(chart, use_container_width=True)


def plot_platform_compatibility(df: DataFrame, titles: list[str], release_dates: list[datetime], review_dates: list[datetime], genres: list[str], platforms: list[str], minimum_sentiment: float, maximum_sentiment: float) -> None:
    """
    Create a bar chart for the platform compatibility of games

    Args:
        df (DataFrame): A pandas DataFrame containing all relevant game data

        titles (list[str]):  A list with game titles that the user selected

        release_dates (list[datetime]): A list with release dates that the user selected

        review_dates (list[datetime]): A list with review dates that the user selected

        genres (list[str]): A list with game genres that the user selected

        platforms (list[str]): A list with selected platforms

    Returns:
        None   
    """
    if len(titles) != 0:
        df = df[df["title"].isin(titles)]
    if len(release_dates) != 0:
        df = df[df["release_date"].dt.floor("D").isin(release_dates)]
    if len(review_dates) != 0:
        df = df[df["release_date"].dt.floor("D").isin(review_dates)]
    if len(genres) != 0:
        df = df[df["genre"].isin(genres)]
    df = df[df[platforms].any(axis=1)]
    df = df[(df['sentiment'] >= min_sentiment) &
            (df['sentiment'] <= max_sentiment)]

    mac = game_df.groupby("mac")['title'].nunique().reset_index()
    windows = game_df.groupby("windows")['title'].nunique().reset_index()
    linux = game_df.groupby("windows")['title'].nunique().reset_index()
    print(mac)


if __name__ == "__main__":

    load_dotenv()
    config = environ

    # conn = get_db_connection(config)

    # game_df = get_database(conn)

    game_df = pd.read_csv("mock_data.csv")
    game_df["release_date"] = pd.to_datetime(
        game_df['release_date'], format='%d/%m/%Y')
    game_df["review_date"] = pd.to_datetime(
        game_df['review_date'], format='%d/%m/%Y')
    dashboard_header()

    selected_games = build_sidebar_title(game_df)
    selected_release_dates = build_sidebar_release_date(game_df)
    selected_review_dates = build_sidebar_review_date(game_df)
    selected_genre = build_sidebar_genre(game_df)
    selected_platform = build_sidebar_platforms()
    min_sentiment, max_sentiment = build_sidebar_sentiment(game_df)

    headline_figures(game_df, selected_games, selected_release_dates,
                     selected_review_dates, selected_genre, selected_platform, min_sentiment, max_sentiment)

    plot_reviews_per_game(game_df, selected_games, selected_release_dates,
                          selected_review_dates, selected_genre, selected_platform, min_sentiment, max_sentiment)

    plot_games_release_frequency(game_df, selected_games, selected_release_dates,
                                 selected_review_dates, selected_genre, selected_platform, min_sentiment, max_sentiment)

    plot_games_review_frequency(game_df, selected_games, selected_release_dates,
                                selected_review_dates, selected_genre, selected_platform, min_sentiment, max_sentiment)

    plot_platform_compatibility(game_df, selected_games, selected_release_dates,
                                selected_review_dates, selected_genre, selected_platform, min_sentiment, max_sentiment)
