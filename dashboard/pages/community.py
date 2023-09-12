"""Python Script: Build a dashboard for data visualization"""
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
import streamlit as st
from psycopg2 import connect
from psycopg2.extensions import connection


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


def get_database(conn_postgres: connection) -> DataFrame:
    """
    Returns redshift database transaction table as a DataFrame Object

    Args:
        conn_postgres (connection): A connection to a Postgres database

    Returns:
        DataFrame:  A pandas DataFrame containing all relevant release data
    """
    query = f"SELECT\
            game.game_id, title, release_date, price, sale_price,\
            sentiment, review_text, reviewed_at, review_score,\
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
    genre = st.sidebar.multiselect(
        "Genre:", options=df_releases["genre"].unique())
    return genre


def build_sidebar_developer(df_releases: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select game developer

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with game genres that the user selected
    """
    developer = st.sidebar.multiselect(
        "Developer:", options=df_releases["developer_name"].unique())
    return developer


def build_sidebar_publisher(df_releases: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select game publisher

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with game genres that the user selected
    """
    publisher = st.sidebar.multiselect(
        "Publisher:", options=df_releases["publisher_name"].unique())
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
        "Price (£):", min_value=min_price, max_value=max_price, value=(min_price, max_price), step=1.0)
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
        "Sentiment:", min_value=min_sentiment, max_value=max_sentiment, value=(min_sentiment, max_sentiment), step=0.1)
    return sentiment


def filter_data(df_releases: DataFrame, titles: list[str], release_dates: list[datetime], review_dates: list[datetime],
                genres: list[str], developers: list[str], publishers: list[str], platforms: list[str], minimum_price: float,
                maximum_price: float, minimum_sentiment: float, maximum_sentiment: float) -> DataFrame:
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
    if titles:
        df_releases = df_releases[df_releases["title"].isin(titles)]

    if release_dates:
        df_releases = df_releases[df_releases["release_date"].dt.floor(
            "D").isin(release_dates)]

    if review_dates:
        df_releases = df_releases[df_releases["review_date"].dt.floor(
            "D").isin(review_dates)]

    if genres:
        df_releases = df_releases[df_releases["genre"].isin(genres)]

    if developers:
        df_releases = df_releases[df_releases["developer_name"].isin(
            developers)]

    if publishers:
        df_releases = df_releases[df_releases["publisher_name"].isin(
            publishers)]

    df_releases = df_releases[df_releases[platforms].any(axis=1)]

    df_releases = df_releases[(df_releases['price'] >= minimum_price) & (
        df_releases['price'] <= maximum_price)]

    average_sentiment_by_title = df_releases.groupby('title')[
        'sentiment'].mean()
    filtered_titles = average_sentiment_by_title[
        ((average_sentiment_by_title >= minimum_sentiment) | average_sentiment_by_title.isna()) &
        ((average_sentiment_by_title <= maximum_sentiment)
         | average_sentiment_by_title.isna())
    ].index
    df_releases = df_releases[df_releases['title'].isin(filtered_titles)]

    return df_releases


def aggregate_release_data(df_releases: DataFrame) -> DataFrame:
    """
    Return key information related to a new release
    Transform data in releases DataFrame to find aggregated data from individual releases
    Args:
        df_release (DataFrame): A DataFrame containing new release data
        index (int): A int associated with a number index within the trending game list
    Returns:
        DataFrame: A DataFrame containing new release data with aggregated data for each release
    """
    average_sentiment_per_title = df_releases.groupby('title')[
        'sentiment'].mean().sort_values(
        ascending=False).dropna().reset_index()
    average_sentiment_per_title.columns = ["title", "avg_sentiment"]

    review_per_title = df_releases.groupby('title')[
        'review_text'].count().sort_values(
        ascending=False).dropna().reset_index()
    review_per_title.columns = ["title", "num_of_reviews"]

    data_frames = [df_releases, average_sentiment_per_title, review_per_title]

    df_merged = reduce(lambda left, right: pd.merge(left, right, on=['title'],
                                                    how='outer'), data_frames)

    df_merged = df_merged.drop_duplicates("title")

    desired_columns = ["title", "release_date",
                       "sale_price", "avg_sentiment", "num_of_reviews"]
    df_merged = df_merged[desired_columns]

    table_columns = ["Title", "Release Date",
                     "Price", "Community Sentiment", "Number of Reviews"]
    df_merged.columns = table_columns

    return df_merged


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
    df_releases['Community Sentiment'] = df_releases['Community Sentiment'].apply(
        lambda x: round(x, 2))
    df_releases['Community Sentiment'] = df_releases['Community Sentiment'].fillna(
        "No Sentiment")

    return df_releases


def plot_average_sentiment_per_game(df_releases: DataFrame, rows: int) -> Chart:
    """
    Create a bar chart for the average sentiment per game

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

        rows (int): An integer value representing the number of rows to be displayed

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby(
        "title")["sentiment"].mean().reset_index().dropna().sort_values(by=["sentiment"]).tail(rows)

    df_releases.columns = ["title", "average_sentiment"]

    chart = alt.Chart(df_releases).mark_bar(
    ).encode(
        x=alt.X("average_sentiment", title="Average Sentiment"),
        y=alt.Y("title", title="Release Title", sort="-x")
    ).properties(
        title="Top 5 Releases: Highest Sentiment Score",
        height=250
    )

    return chart


def plot_reviews_per_game_frequency(df_releases: DataFrame, rows: int) -> Chart:
    """
    Create a bar chart for the number of reviews per game

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

        rows (int): An integer value representing the number of rows to be displayed


    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.dropna().groupby(
        "title")["review_text"].nunique().reset_index().sort_values(by=["review_text"]).tail(rows)

    df_releases.columns = ["title", "num_of_reviews"]

    chart = alt.Chart(df_releases).mark_bar(
    ).encode(
        x=alt.X("num_of_reviews", title="Number of Reviews"),
        y=alt.Y("title", title="Release Title", sort="-x")
    ).properties(
        title="Top 5 Releases: Most Reviewed",
        height=250
    )

    return chart


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
        title="Top 5 Developers: Highest Sentiment Score",
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
        title="Top 5 Publishers: Highest Sentiment Score",
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
                title="Number of Releases"),
        y=alt.X("genre:N", title="Genre", sort="-x")
    ).properties(
        title="Top 5 Genres: New Releases",
        height=250
    )

    return chart


def plot_trending_games_table(df_releases: DataFrame) -> None:
    """
    Create a table for the top 5 recommended games

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        None
    """
    df_merged = aggregate_release_data(df_releases)

    df_merged = df_merged.sort_values(
        by=["Community Sentiment"], ascending=False)
    df_merged = format_columns(df_merged)

    df_merged = df_merged.reset_index(drop=True)

    return {"table_data": df_merged, "title": "Top 5 Recommended Games by Sentiment"}


def plot_trending_games_review_table(df_releases: DataFrame) -> dict:
    """
    Create a table for the top recommended games by number of reviews 
    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases
    Returns:
        dict: A Python dictionary containing a DataFrame with table formatted data and a table title
    """
    df_merged = aggregate_release_data(df_releases)

    df_merged = df_merged.sort_values(
        by=["Number of Reviews"], ascending=False)
    df_merged = format_columns(df_merged)

    df_merged = df_merged.reset_index(drop=True)

    return {"table_data": df_merged, "title": "Top 5 Recommended Games by Sentiment"}


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

    stops.extend(["n't"])

    important_words = ["pm", "us", "uk", "gb"]

    return [t for t in tokens
            if t not in stops
            and (len(t) > 2 or t in important_words)]


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


def plot_word_cloud_all_releases(df_releases: DataFrame) -> None:
    """
    Generate a word cloud plot based on key words from individual review text

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        None
    """
    df_releases = tokenize_review_text(df_releases)
    df_releases = lemmatize_tokens(df_releases)
    df_releases = filter_tokens(df_releases)
    review_keywords = flatten(df_releases["keywords"])
    print(df_releases)


def dashboard_header() -> None:
    """
    Build header for dashboard to give it title text

    Args:
        None

    Returns:
        None
    """

    st.title("SteamPulse")
    st.markdown("Community Insights for New Releases on Steam")


def sidebar_header() -> None:
    """
    Add text to the dashboard side bar

    Args:
        None

    Returns:
        None
    """
    with st.sidebar:
        st.markdown("Filter Options\n---")


def headline_figures(df_releases: DataFrame) -> None:
    """
    Build headline for dashboard to present key figures for quick view of overall data

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        None
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
                  df_releases["review_text"].nunique())
    with cols[2]:
        st.metric("Average Sentiment:", round(
            df_releases["sentiment"].mean(), 2))


def sub_headline_figures(df_releases: DataFrame) -> None:
    """
    Build sub-headline for dashboard to present key figures for quick view of overall data

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        None
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

    Returns:
        None
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

    Returns:
        None
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

    Returns:
        None
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


if __name__ == "__main__":

    load_dotenv()
    config = environ

    conn = get_db_connection(config)

    game_df = get_database(conn)
    game_df = format_database_columns(game_df)
    game_df = get_data_for_release_date_range(game_df, 14)

    st.set_page_config(layout="wide")

    dashboard_header()
    sidebar_header()

    selected_releases = build_sidebar_title(game_df)
    selected_release_dates = build_sidebar_release_date(game_df)
    selected_review_dates = build_sidebar_review_date(game_df)
    selected_genre = build_sidebar_genre(game_df)
    selected_developer = build_sidebar_developer(game_df)
    selected_publisher = build_sidebar_publisher(game_df)
    selected_platform = build_sidebar_platforms()
    min_price, max_price = build_sidebar_price(game_df)
    min_sentiment, max_sentiment = build_sidebar_sentiment(game_df)

    filtered_df = filter_data(game_df, selected_releases, selected_release_dates, selected_review_dates,
                              selected_genre, selected_developer, selected_publisher, selected_platform, min_price, max_price, min_sentiment, max_sentiment)

    if filtered_df.empty:
        st.markdown(
            "### Invalid Filters\n There are no releases which fit your options")
    else:
        headline_figures(filtered_df)

        sub_headline_figures(filtered_df)

        trending_games_by_sentiment = plot_trending_games_table(filtered_df)
        trending_game_by_reviews = plot_trending_games_review_table(
            filtered_df)

        trending_sentiment_per_game_plot = plot_average_sentiment_per_game(
            filtered_df, 5)
        trending_reviews_per_game_plot = plot_reviews_per_game_frequency(
            filtered_df, 5)
        games_genre_distribution_plot = plot_genre_distribution(filtered_df, 5)

        trending_sentiment_per_developer_plot = plot_average_sentiment_per_developer(
            filtered_df, 5)
        trending_sentiment_per_publisher_plot = plot_average_sentiment_per_publisher(
            filtered_df, 5)

        table_rows(trending_games_by_sentiment,
                   trending_game_by_reviews)
        first_row_figures(trending_sentiment_per_game_plot,
                          trending_reviews_per_game_plot, games_genre_distribution_plot)
        second_row_figures(trending_sentiment_per_developer_plot,
                           trending_sentiment_per_publisher_plot)

        review_word_cloud_plot = plot_word_cloud_all_releases(filtered_df)
