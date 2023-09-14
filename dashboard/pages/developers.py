"""Python Script: Build a dashboard for data visualization (developer page)"""
from datetime import datetime, timedelta
from os import environ, _Environ

import altair as alt
from altair.vegalite.v5.api import Chart
from dotenv import load_dotenv
from functools import reduce
import pandas as pd
from pandas import DataFrame
from psycopg2 import connect
from psycopg2.extensions import connection
import streamlit as st


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


def plot_genre_distribution(df_releases: DataFrame) -> Chart:
    """
    Create a line chart for the number of games released per day

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby(
        "genre").size().reset_index().sort_values(by=[0])

    df_releases.columns = ["genre", "releases_per_genres"]

    chart = alt.Chart(df_releases).mark_bar().encode(
        x=alt.Y("releases_per_genres:Q",
                title="Number of Releases"),
        y=alt.X("genre:N", title="Genre", sort="-x")
    ).properties(
        title="Releases per Genre",
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
                  df_releases["review_text"].nunique())
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


def two_column_chart_figures(plot_one: Chart, plot_two: Chart) -> None:
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
        st.altair_chart(plot_two, use_container_width=True)
    st.markdown("---")


if __name__ == "__main__":

    load_dotenv()
    config = environ

    game_df = get_database()
    game_df = format_database_columns(game_df)
    game_df = get_data_for_release_date_range(game_df, 14)

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

        games_genre_distribution_plot = plot_genre_distribution(filtered_df)

        two_column_chart_figures(games_release_frequency_plot,
                                 games_review_frequency_plot)
        two_column_chart_figures(
            games_platform_distribution_plot, games_price_distribution_plot)
        two_column_chart_figures(
            trending_sentiment_per_game_plot,  trending_reviews_per_game_plot)
        two_column_chart_figures(trending_sentiment_per_developer_plot,
                                 trending_sentiment_per_publisher_plot)

        st.altair_chart(games_genre_distribution_plot,
                        use_container_width=True)
