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
            database=config_file["DATABASE_NAME"],
            user=config_file["DATABASE_USERNAME"],
            password=config_file["DATABASE_PASSWORD"],
            port=config_file["DATABASE_PORT"],
            host=config_file["DATABASE_ENDPOINT"]
        )
    except Exception as err:
        print("Error connecting to database.")
        raise err


@st.cache_data(ttl="600s")
def get_database() -> DataFrame:
    """
    Returns redshift database transaction table as a DataFrame Object

    Args:
        conn_postgres (connection): A connection to a Postgres database

    Returns:
        DataFrame:  A pandas DataFrame containing all relevant release data
    """
    conn_postgres = get_db_connection(config)

    query = f"SELECT\
            game.game_id, title, release_date, price, sale_price,\
            review_id, sentiment, review_text, reviewed_at, review_score,\
            genre, user_generated,\
            developer_name,\
            publisher_name,\
            mac, windows, linux\
            FROM game\
            LEFT JOIN review ON\
            review.game_id=game.game_id\
            LEFT JOIN platform ON\
            game.platform_id=platform.platform_id\
            LEFT JOIN game_developer_link as developer_link ON\
            game.game_id=developer_link.game_id\
            LEFT JOIN developer ON\
            developer_link.developer_id=developer.developer_id\
            LEFT JOIN game_genre_link as genre_link ON\
            game.game_id=genre_link.game_id\
            LEFT JOIN genre ON\
            genre_link.genre_id=genre.genre_id\
            LEFT JOIN game_publisher_link as publisher_link ON\
            game.game_id=publisher_link.game_id\
            LEFT JOIN publisher ON\
            publisher_link.publisher_id=publisher.publisher_id;"

    df_releases = pd.read_sql_query(query, conn_postgres)

    return df_releases


def get_data_for_release_date_range(df_releases: DataFrame, index: int) -> DataFrame:
    """
    Return a DataFrame for a range of dates behind the current date
    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data
        index (int): An integer representing the number of days to go back from current date
    Returns:
        DataFrame: A pandas DataFrame containing all relevant game data for a specific date
    """
    date_week_ago = (datetime.now() - timedelta(days=index)
                     ).strftime("%Y-%m-%d")

    return df_releases[df_releases["release_date"] >= date_week_ago]


def format_database_columns(df_releases: DataFrame) -> DataFrame:
    """
    Format columns within the database to the correct data types
    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases
    Returns:
        DataFrame: A DataFrame containing filtered data related to new releases 
        with columns in the correct data types
    """
    df_releases["release_date"] = pd.to_datetime(
        df_releases['release_date'], format='%d/%m/%Y')
    df_releases["review_date"] = pd.to_datetime(
        df_releases['reviewed_at'], format='%d/%m/%Y')

    return df_releases


def build_sidebar_title(df_releases: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list:  A list with game titles that the user selected
    """
    titles = st.sidebar.multiselect(
        "Release Title:", options=sorted(df_releases["title"].unique()))
    return titles


def build_sidebar_release_date(df_releases: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select release dates

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with release dates that the user selected
    """
    release_dates = st.sidebar.multiselect(
        "Release Date:", options=df_releases["release_date"].dt.date.unique())
    return release_dates


def build_sidebar_review_date(df_releases: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select review dates

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with review dates that the user selected
    """
    review_dates = st.sidebar.multiselect(
        "Review Date:", options=df_releases["review_date"].dt.date.unique())
    return review_dates


def build_sidebar_genre(df_releases: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select game genre

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with game genres that the user selected
    """
    df_releases = df_releases[df_releases["genre"].notna()]
    selection = df_releases["genre"].unique()

    genre = st.sidebar.multiselect("Genre:", options=selection)
    return genre


def build_sidebar_developer(df_releases: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select game developer

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with game genres that the user selected
    """
    df_releases = df_releases[df_releases["developer_name"].notna()]
    selection = df_releases["developer_name"].unique()

    developer = st.sidebar.multiselect("Developer:", options=selection)
    return developer


def build_sidebar_publisher(df_releases: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select game publisher

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with game genres that the user selected
    """
    df_releases = df_releases[df_releases["publisher_name"].notna()]
    selection = df_releases["publisher_name"].unique()

    publisher = st.sidebar.multiselect("Publisher:", options=selection)
    return publisher


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


def build_sidebar_price(df_releases: DataFrame) -> tuple:
    """
    Build sidebar with slider option to select range for review sentiment

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A tuple with minimum and maximum sentiment that the user has selected
    """
    max_price = df_releases["price"].max()
    min_price = df_releases["price"].min()
    price = st.sidebar.slider(
        "Price (£):", min_value=min_price, max_value=max_price,
        value=(min_price, max_price), step=1.0)

    return price


def build_sidebar_sentiment(df_releases: DataFrame) -> tuple:
    """
    Build sidebar with slider option to select range for review sentiment

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A tuple with minimum and maximum sentiment that the user has selected
    """
    max_sentiment = df_releases["sentiment"].max()
    min_sentiment = df_releases["sentiment"].min()

    sentiment = st.sidebar.slider(
        "Sentiment:", min_value=min_sentiment, max_value=max_sentiment,
        value=(min_sentiment, max_sentiment), step=0.1)
    return sentiment


def build_sidebar_number_of_reviews(df_releases: DataFrame) -> tuple:
    """
    Build sidebar with slider option to select range for number of reviews

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A tuple with minimum and maximum number of reviews that the user has selected
    """
    max_number_of_reviews = df_releases["review_id"].nunique()
    min_number_of_reviews = 0

    number_of_reviews = st.sidebar.slider(
        "Number of Reviews:", min_value=min_number_of_reviews, max_value=max_number_of_reviews,
        value=(min_number_of_reviews, max_number_of_reviews), step=1)
    return number_of_reviews


def filter_data(df_releases: DataFrame, filter: dict) -> DataFrame:
    """
    Apply live filtering according to sidebar filters to the data frame

    Args:
        df_releases (DataFrame): A DataFrame containing all data related to new releases

        titles (list[str]):  A list with game titles that the user selected

        release_dates (list[datetime]): A list with release dates that the user selected

        review_dates (list[datetime]): A list with review dates that the user selected

        genres (list[str]): A list with game genres that the user selected

        platforms (list[str]): A list with selected platforms

    Returns:
        DataFrame: A DataFrame containing filtered data related to new releases

    """
    if filter[SELECTED_RELEASES]:
        df_releases = df_releases[df_releases["title"].isin(
            filter[SELECTED_RELEASES])]

    if filter[SELECTED_RELEASE_DATES]:
        df_releases = df_releases[df_releases["release_date"].dt.floor(
            "D").isin(filter[SELECTED_RELEASE_DATES])]

    if filter[SELECTED_REVIEW_DATES]:
        df_releases = df_releases[df_releases["review_date"].dt.floor(
            "D").isin(filter[SELECTED_REVIEW_DATES])]

    if filter[SELECTED_GENRE]:
        df_releases = df_releases[df_releases["genre"].isin(
            filter[SELECTED_GENRE])]

    if filter[SELECTED_DEVELOPER]:
        df_releases = df_releases[df_releases["developer_name"].isin(
            filter[SELECTED_DEVELOPER])]

    if filter[SELECTED_PUBLISHER]:
        df_releases = df_releases[df_releases["publisher_name"].isin(
            filter[SELECTED_PUBLISHER])]

    df_releases = df_releases[df_releases[filter[SELECTED_PLATFORM]].any(
        axis=1)]

    df_releases = df_releases[(df_releases['price'] >= filter[PRICE][0]) & (
        df_releases['price'] <= filter[PRICE][1])]

    average_sentiment_by_title = df_releases.groupby('title')[
        'sentiment'].mean()
    filtered_titles = average_sentiment_by_title[
        ((average_sentiment_by_title >= filter[SENTIMENT][0]) | average_sentiment_by_title.isna()) &
        ((average_sentiment_by_title <= filter[SENTIMENT][1])
         | average_sentiment_by_title.isna())
    ].index
    df_releases = df_releases[df_releases['title'].isin(filtered_titles)]

    df_releases = df_releases[(df_releases['num_of_reviews'] >= filter[REVIEWS][0]) & (
        df_releases['num_of_reviews'] <= filter[REVIEWS][1])]

    return df_releases


def calculate_sum_sentiment(sentiment: float, score: int) -> float:
    """
    Calculates total sentiment score by multiplying sentiment associated with
    a review multiplied by the review_score (represents the number of users who
    agree with this review)

    Args:
        sentiment (float): A value associated with how positive or negative the
        review is considered to be

        score (int): A value associated with the number of users who up-voted a 
        review

    Returns:
        float: A sentiment value which takes into account the number of users
        who agreed with a given review
    """
    if score != 0:
        return sentiment * (score + 1)
    return sentiment


def aggregate_data(df_releases: DataFrame) -> DataFrame:
    """
    Transform data in releases DataFrame to find aggregated sentiment from individual reviews
    Args:
        df_release (DataFrame): A DataFrame containing new release data
    Returns:
        DataFrame: A DataFrame containing new release data with aggregated data for each release
    """

    df_releases["weighted_sentiment"] = df_releases.apply(lambda row:
                                                          calculate_sum_sentiment(row["sentiment"], row["review_score"]), axis=1)

    review_rows_count = df_releases.groupby(
        "game_id")["weighted_sentiment"].count()
    total_sum_scores = df_releases.groupby(
        "game_id")["weighted_sentiment"].sum()
    total_weights = df_releases.groupby("game_id")[
        "review_score"].sum()

    total_weights = total_weights + review_rows_count
    total_sentiment_scores = total_sum_scores / total_weights

    df_releases["avg_sentiment"] = df_releases["game_id"].apply(
        lambda row: round(total_sentiment_scores.loc[row], 1))

    review_per_title = df_releases.groupby('game_id')[
        'review_id'].nunique()
    review_per_title = review_per_title.to_frame()

    review_per_title.columns = ["num_of_reviews"]

    data_frames = [df_releases, review_per_title]

    df_merged = reduce(lambda left, right: pd.merge(left, right, on=['game_id'],
                                                    how='outer'), data_frames)

    df_merged.drop(["weighted_sentiment"], axis=1, inplace=True)

    return df_merged


def format_sentiment_significant_figures(sentiment: float) -> str:
    """
    Normalize sentiment values to be strings and reduce to 3 significant figures

    Args:
        sentiment (float): A float representing the sentiment value 
        associated with a review

    Returns:
        str: A string representing the sentiment value, 
        formatted to one decimal place
    """
    return str(sentiment)[:3]


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


def format_columns(df_releases: DataFrame) -> DataFrame:
    """
    Format columns in DataFrame for display

    Args:
        df_release (DataFrame): A DataFrame containing new release data

    Returns:
        DataFrame: A DataFrame containing data with formatted columns
    """
    df_releases['Price'] = df_releases['Price'].apply(
        lambda x: f"£{x:.2f}")
    df_releases['Release Date'] = df_releases['Release Date'].dt.strftime(
        '%d/%m/%Y')
    df_releases['Community Sentiment'] = df_releases['Community Sentiment'].fillna(
        "No Sentiment")

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


def plot_genre_distribution(df_releases: DataFrame, rows: int) -> Chart:
    """
    Create a line chart for the number of games released per day

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

        rows (int): An integer value representing the number of rows to be displayed

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby(
        "genre").size().reset_index().sort_values(by=[0]).tail(rows)

    df_releases.columns = ["genre", "releases_per_genres"]

    chart = alt.Chart(df_releases).mark_bar().encode(
        x=alt.Y("releases_per_genres:Q",
                title="No. of Releases"),
        y=alt.X("genre:N", title="Genre", sort="-x")
    ).properties(
        title="Top Genres by No. of Releases",
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

    return {"table_data": df_merged, "title": "Top Recommended Games by Sentiment"}


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

    return {"table_data": df_merged, "title": "Top Recommended Games by No. of Reviews"}


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


def sidebar_header() -> None:
    """
    Add text to the dashboard side bar
    """
    with st.sidebar:
        st.markdown("Filter Options\n---")


def headline_figures(df_releases: DataFrame) -> None:
    """
    Build headline for dashboard to present key figures for quick view of overall data

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases
    """
    cols = st.columns(3)
    st.markdown(
        """
        <style>
            [data-testid="stMetricValue"] {
            font-size: 25px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with cols[0]:
        st.metric("Total Releases:", df_releases["title"].nunique())
    with cols[1]:
        st.metric("Total Reviews:",
                  df_releases["review_id"].nunique())
    with cols[2]:
        st.metric("Average Sentiment:", round(
            df_releases["sentiment"].mean(), 2))


def sub_headline_figures(df_releases: DataFrame) -> None:
    """
    Build sub-headline for dashboard to present key figures for quick view of overall data

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases
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

    cols = st.columns(3)
    st.markdown(
        """
        <style>
            [data-testid="stMetricValue"] {
            font-size: 25px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    with cols[0]:
        st.metric("Most Released Genre:", df_releases["genre"].mode()[0])
    with cols[1]:
        st.metric("Most Reviewed Release:", df_releases["title"].mode()[0])
    with cols[2]:
        st.metric("Most Compatible Platform",
                  compatibility_df["platform"].max().capitalize())

    st.markdown("---")


def first_row_figures(plot_one: Chart, plot_two: Chart, plot_three: Chart) -> None:
    """
    Build figures relating to release and review frequency for dashboard

    Args:
        plot_one (Chart): A chart displaying plotted data

        plot_two (Chart): A chart displaying plotted data

        plot_three (Chart): A chart displaying plotted data
    """
    cols = st.columns(3)
    with cols[0]:
        st.altair_chart(plot_one, use_container_width=True)
    with cols[1]:
        st.altair_chart(plot_two, use_container_width=True)
    with cols[2]:
        st.altair_chart(plot_three, use_container_width=True)

    st.markdown("---")


def second_row_figures(plot_one: Chart, plot_two: Chart) -> None:
    """
    Build figures relating to release and review frequency for dashboard

    Args:
        plot_one (Chart): A chart displaying plotted data

        plot_two (Chart): A chart displaying plotted data
    """
    cols = st.columns(2)
    with cols[0]:
        st.altair_chart(plot_one, use_container_width=True)
    with cols[1]:
        st.altair_chart(plot_two,
                        use_container_width=True)

    st.markdown("---")


def table_rows(table_one: Chart, table_two: Chart) -> None:
    """
    Build figures relating to release and review frequency for dashboard

    Args:
        plot_one (Chart): A chart displaying plotted data

        plot_two (Chart): A chart displaying plotted data
    """
    cols = st.columns(2)
    with cols[0]:
        st.markdown(f"{table_one['title']}")
        st.table(table_one["table_data"].head(5).style.set_properties(
            **{'font-size': '16px'}))
    with cols[1]:
        st.markdown(f"{table_two['title']}")
        st.table(table_two["table_data"].head(5).style.set_properties(
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

    filter_dictionary = {
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

    filtered_df = filter_data(game_df, filter_dictionary)

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
        games_genre_distribution_plot = plot_genre_distribution(filtered_df, 5)

        table_rows(trending_games_by_sentiment,
                   trending_game_by_reviews)
        first_row_figures(trending_sentiment_per_developer_plot,
                          trending_sentiment_per_publisher_plot, games_genre_distribution_plot)

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
