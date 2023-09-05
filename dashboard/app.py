"""Python Script: Build a dashboard for data visualization"""

from os import environ, _Environ
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd
from pandas import DataFrame
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
        list: A list with values corresponding to game title in the data base
    """
    titles = st.sidebar.multiselect(
        "Game Title", options=sorted(df["title"].unique()))
    return titles


def build_sidebar_release_date(df: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select game names

    Args:
        df (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with values corresponding to dates for which games were released
    """
    dates = st.sidebar.multiselect(
        "Release Date", options=df["release_date"].dt.date.unique())
    return dates


def build_sidebar_review_date(df: DataFrame) -> list:
    """
    Build sidebar with dropdown menu options to select game names

    Args:
        df (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        list: A list with values corresponding to dates for which reviews exist in the data base
    """
    dates = st.sidebar.multiselect(
        "Review Date", options=df["review_date"].dt.date.unique())
    return dates


# def headline_figures(df: DataFrame, plants: list[int], dates: list[datetime]) -> None:
#     """Build headline for dashboard to present key figures for quick view of overall data"""

#     cols = st.columns(4)

#     if len(plants) != 0:
#         df = df[df["plant_name"].isin(plants)]

#     if len(dates) != 0:
#         df = df[df["reading_time"].dt.floor("D").isin(dates)]

#     total_active_days = df.groupby(
#         pd.Grouper(key='reading_time', freq="1D")).size().count()

#     with cols[0]:
#         st.metric("Total Plants:", df["plant_name"].nunique())
#     with cols[1]:
#         st.metric("Total Days Active:",
#                   total_active_days)
#     with cols[2]:
#         st.metric("Total Readings:",
#                   df.shape[0])
#     with cols[3]:
#         st.metric("Number of Botanists :",
#                   df["botanist_name"].nunique())


# def create_chart_title(chart_title: str) -> None:
#     """Creates chart chart_title"""

#     st.markdown(f"### {chart_title.title()}")


# def plot_readings_per_plant(dataframe: DataFrame, plants: list[int], dates: list[datetime]) -> None:
#     """Create a bar chart for the readings logged per plant"""
#     if len(plants) != 0:
#         dataframe = dataframe[dataframe["plant_name"].isin(plants)]
#     if len(dates) != 0:
#         dataframe = dataframe[dataframe["reading_time"].dt.floor(
#             "D").isin(dates)]

#     readings_per_plant = dataframe.groupby(
#         "plant_name").size().reset_index()
#     readings_per_plant.columns = ["Plant Name", "Number of readings"]

#     st.title("Number of Readings per Plant")
#     st.bar_chart(data=readings_per_plant,
#                  x="Plant Name", y="Number of readings")


# def plot_average_temperatures(df: DataFrame, plants: list[int], dates: list[datetime]):
#     """Plots the average temperature of each plant"""

#     if len(plants) != 0:
#         df = df[df["plant_name"].isin(plants)]
#     if len(dates) != 0:
#         df = df[df["reading_time"].dt.floor(
#             "D").isin(dates)]

#     average_temperatures = df.groupby(
#         'plant_name')['temperature'].mean().reset_index()
#     average_temperatures.columns = ["Plant Name", "Average Temperature (°C)"]

#     st.title("Average Temperature per Plant")
#     st.bar_chart(data=average_temperatures,
#                  x="Plant Name", y="Average Temperature (°C)")


# def plot_average_soil_moisture(df: DataFrame, plants: list[int], dates: list[datetime]):
#     """Plots the average soil moisture for each plant"""
#     if len(plants) != 0:
#         df = df[df["plant_name"].isin(plants)]
#     if len(dates) != 0:
#         df = df[df["reading_time"].dt.floor(
#             "D").isin(dates)]

#     avg_soil_moisture = df.groupby('plant_name')[
#         'soil_moisture'].mean().reset_index()
#     avg_soil_moisture.columns = ["Plant Name", "Average Soil Moisture"]

#     st.title("Average Soil Moisture per Plant")
#     st.bar_chart(data=avg_soil_moisture,
#                  x="Plant Name", y="Average Soil Moisture")


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

    print(game_df)

    dashboard_header()

    selected_games = build_sidebar_title(game_df)

    selected_release_dates = build_sidebar_release_date(game_df)

    slected_review_dates = build_sidebar_review_date(game_df)

    # headline_figures(plant_df, selected_games, selected_dates)

    # plot_average_temperatures(plant_df, selected_games, selected_dates)
    # plot_average_soil_moisture(plant_df, selected_games, selected_dates)
    # plot_readings_per_plant(plant_df, selected_games, selected_dates)

    # print(plant_df.groupby('plant_name')['soil_moisture'].mean().reset_index())
