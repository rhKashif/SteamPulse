"""Python Script: Build a dashboard for data visualization (community page)"""
from datetime import datetime, timedelta
from os import environ, _Environ

import altair as alt
from altair.vegalite.v5.api import Chart
from collections import defaultdict
from dotenv import load_dotenv
from functools import reduce
from nltk import pos_tag
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import pandas as pd
from pandas import DataFrame
from pandas.core.common import flatten
from psycopg2 import connect
from psycopg2.extensions import connection
import streamlit as st
from wordcloud import WordCloud

from utility_functions import (get_database,
                               aggregate_data,
                               format_columns,
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
                               two_column_chart_figures,
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


def format_data_for_table(df_releases: DataFrame) -> DataFrame:
    """
    Return key information related to a new release in a format ready for table plotting 

    Args:
        df_release (DataFrame): A DataFrame containing new release data
    Returns:
        DataFrame: A DataFrame containing new release data with aggregated data for each release
    """
    df_releases = df_releases.drop_duplicates("title")
    df_releases = df_releases.dropna(subset=["review_text"])
    desired_columns = ["title", "release_date",
                       "sale_price", "avg_sentiment", "num_of_reviews"]
    df_releases = df_releases[desired_columns]

    table_columns = ["Title", "Release Date",
                     "Price", "Community Sentiment", "No. of Reviews"]
    df_releases.columns = table_columns

    df_releases["Community Sentiment"] = df_releases["Community Sentiment"].apply(
        format_sentiment_significant_figures)

    return df_releases


def plot_average_sentiment_per_developer(df_releases: DataFrame, rows: int) -> Chart:
    """
    Create a bar chart for the average sentiment per developer

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

        rows (int): An integer value representing the number of rows to be displayed

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby(
        "developer_name")["sentiment"].mean().reset_index().dropna().sort_values(by=["sentiment"]).tail(rows)

    df_releases.columns = ["developer", "average_sentiment"]

    chart = alt.Chart(df_releases).mark_bar(
    ).encode(
        x=alt.X("average_sentiment", title="Average Sentiment"),
        y=alt.Y("developer", title="Release Title", sort="-x")
    ).properties(
        title="Top Developers by Sentiment",
        height=250
    )

    return chart


def plot_average_sentiment_per_publisher(df_releases: DataFrame, rows: int) -> Chart:
    """
    Create a bar chart for the average sentiment per publisher

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

        rows (int): An integer value representing the number of rows to be displayed

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby(
        "publisher_name")["sentiment"].mean().reset_index().dropna().sort_values(by=["sentiment"]).tail(rows)

    df_releases.columns = ["publisher", "average_sentiment"]

    chart = alt.Chart(df_releases).mark_bar(
    ).encode(
        x=alt.X("average_sentiment", title="Average Sentiment"),
        y=alt.Y("publisher", title="Release Title", sort="-x")
    ).properties(
        title="Top Publishers by Sentiment",
        height=250

    )

    return chart


def plot_trending_games_table(df_releases: DataFrame) -> dict:
    """
    Create a table for the top recommended games

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        dict: A Python dictionary containing a formatted DataFrame for table plot
        and an associated title for the table
    """
    df_merged = format_data_for_table(df_releases)

    df_merged = df_merged.sort_values(
        by=["Community Sentiment"], ascending=False)
    df_merged = format_columns(df_merged)

    df_merged = df_merged.reset_index(drop=True)

    return {"table_data": df_merged, "title": "Top Games by Sentiment"}


def plot_trending_games_review_table(df_releases: DataFrame) -> dict:
    """
    Create a table for the top recommended games by number of reviews 
    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases
    Returns:
        dict: A Python dictionary containing a formatted DataFrame for table plot
        and an associated title for the table
    """
    df_merged = format_data_for_table(df_releases)

    df_merged = df_merged.sort_values(
        by=["No. of Reviews"], ascending=False)
    df_merged = format_columns(df_merged)

    df_merged = df_merged.reset_index(drop=True)

    return {"table_data": df_merged, "title": "Top Games by Number of Reviews"}


def tokenize_review_text(df_releases: DataFrame) -> DataFrame:
    """
    Normalize and tokenize review text for each review and add this data to a new column

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        DataFrame: A DataFrame containing filtered data related to new releases with a new
        column for tokenized review_text
    """
    df_releases.dropna(subset=["review_text"], inplace=True)
    df_releases["keywords"] = df_releases["review_text"].str.lower()
    df_releases["keywords"] = df_releases["keywords"].apply(word_tokenize)

    return df_releases


def get_wordnet_tags(tokens: list) -> list:
    """
    Get the pos tags for a set of tokens, and return the tokens in a way the 
    lemmatizer can interpret

    Args:
        tokens (list): A list containing tokens extracted from review text

    Returns:
        list: A list of tags which the lemmatizer can interpret
    """
    tag_map = defaultdict(lambda: "n")
    tag_map['J'] = "a"
    tag_map['V'] = "v"
    tag_map['R'] = "r"

    tagged_tokens = pos_tag(tokens)

    tagged_tokens = [(token[0], tag_map[token[1][0]])
                     for token in tagged_tokens]

    return tagged_tokens


def lemmatize_tokens(df_releases: DataFrame) -> DataFrame:
    """
    Lemmatize tokens text for each tokenized review

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        DataFrame: A DataFrame containing filtered data related to new releases with a lemmatization
        applied to the tokenized review_text column
    """
    lemma = WordNetLemmatizer()

    df_releases["keywords"] = df_releases["keywords"].apply(get_wordnet_tags)
    df_releases["keywords"] = df_releases["keywords"].apply(
        lambda tokens: [lemma.lemmatize(word=token[0], pos=token[1]) for token in tokens])

    return df_releases


def get_filtered_tokens(tokens):
    """
    Filter out punctuation, stop words, and very short words 

    Args:
        tokens (list): A list containing lemmatized tokens 

    Returns:
        list: A list containing filtered tokens
    """
    stops = stopwords.words("english")

    stops.extend(["play", "get", "still", "game"])

    return [t for t in tokens
            if t not in stops
            and (len(t) > 2)]


def filter_tokens(df_releases: DataFrame) -> DataFrame:
    """
    Filter out punctuation, stop words, and very short words

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        DataFrame: A DataFrame containing filtered data related to new releases with filtered
        keywords
    """

    df_releases["keywords"] = df_releases["keywords"].apply(
        get_filtered_tokens)
    df_releases["keywords"] = df_releases["keywords"].apply(
        lambda tokens: [x.replace("'", "") for x in tokens])

    return df_releases


def plot_word_cloud_all_releases(df_releases: DataFrame) -> WordCloud:
    """
    Generate a word cloud plot based on key words from individual review text

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        WordCloud: A word cloud object 
    """
    df_releases = tokenize_review_text(df_releases)
    df_releases = lemmatize_tokens(df_releases)
    df_releases = filter_tokens(df_releases)

    review_keywords = flatten(df_releases["keywords"])
    review_keywords = pd.Series(review_keywords)
    review_keywords_counts = review_keywords.value_counts()

    word_cloud = WordCloud(
        width=1000,
        height=600,
        background_color="#171a21"
    )
    word_cloud.generate_from_frequencies(review_keywords_counts)

    return word_cloud


def plot_word_cloud_all_releases_genre(df_releases: DataFrame) -> WordCloud:
    """
    Generate a word cloud plot based on genres for each release

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        WordCloud: A word cloud object 
    """
    genre_keywords = flatten(df_releases["genre"])
    genre_keywords = pd.Series(genre_keywords)
    genre_keywords_counts = genre_keywords.value_counts()

    word_cloud = WordCloud(
        width=1000,
        height=600,
        background_color="#171a21"
    )
    word_cloud.generate_from_frequencies(genre_keywords_counts)

    return word_cloud


def dashboard_header() -> None:
    """
    Build header for dashboard to give it title text
    """

    st.title("SteamPulse")
    st.markdown("Community Insights for New Releases on Steam")


def plot_table(table_one: Chart) -> None:
    """
    Build figures relating to release and review frequency for dashboard

    Args:
        plot_one (Chart): A chart displaying plotted data
    """
    st.markdown(f"{table_one['title']}")
    st.table(table_one["table_data"].head(5).style.set_properties(
        **{'font-size': '16px'}))

    st.markdown("---")


def wordcloud_rows(wordcloud_one: Chart, wordcloud_two: Chart) -> None:
    """
    Build figures relating to release and review frequency for dashboard

    Args:
        plot_one (Chart): A chart displaying plotted data

        plot_two (Chart): A chart displaying plotted data
    """
    cols = st.columns(2)
    with cols[0]:
        st.markdown(f"Word Map: Review Text")
        st.image(wordcloud_one.to_array())
    with cols[1]:
        st.markdown(f"Word Map: Genre")
        st.image(wordcloud_two.to_array())

    st.markdown("---")


if __name__ == "__main__":

    st.set_page_config(layout="wide")

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

        trending_games_by_sentiment = plot_trending_games_table(filtered_df)
        trending_game_by_reviews = plot_trending_games_review_table(
            filtered_df)

        trending_sentiment_per_developer_plot = plot_average_sentiment_per_developer(
            filtered_df, 5)
        trending_sentiment_per_publisher_plot = plot_average_sentiment_per_publisher(
            filtered_df, 5)

        plot_table(trending_games_by_sentiment)

        plot_table(trending_game_by_reviews)

        two_column_chart_figures(trending_sentiment_per_developer_plot,
                                 trending_sentiment_per_publisher_plot)

        if not filtered_df["review_text"].dropna().empty and filtered_df["title"].nunique() == 1:
            review_word_cloud_plot = plot_word_cloud_all_releases(filtered_df)
            genre_word_cloud_plot = plot_word_cloud_all_releases_genre(
                filtered_df)

            wordcloud_rows(review_word_cloud_plot, genre_word_cloud_plot)
        elif filtered_df["review_text"].dropna().empty and filtered_df["title"].nunique() == 1:
            st.markdown("### Insufficient data for word cloud plots")
        else:
            st.markdown(
                "#### Select Individual Title to Generate a WordCloud")
