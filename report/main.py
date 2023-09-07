"""Python Script: Build a report for email attachment"""
import base64
from datetime import datetime
from os import environ, _Environ

import altair as alt
from altair.vegalite.v5.api import Chart
from dotenv import load_dotenv
import pandas as pd
from pandas import DataFrame
import streamlit as st
from psycopg2 import connect
from psycopg2.extensions import connection


from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from xhtml2pdf import pisa
import plotly_express as px
import boto3


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
        DataFrame:  A pandas DataFrame containing all relevant release data
    """
    query = f""
    df_releases = pd.read_sql_query(query, conn_postgres)

    return df_releases


def convert_html_to_pdf(source_html, output_filename):
    # open output file for writing (truncated binary)
    result_file = open(output_filename, "w+b")

    # convert HTML to PDF
    pisa_status = pisa.CreatePDF(
        source_html,                # the HTML to convert
        dest=result_file)           # file handle to recieve result

    # close output file
    result_file.close()                 # close output file

    return pisa_status.err


def create_report(fig1, fig2, fig3):
    # Generate graphs as HTML images
    # fig1 = px.scatter(df1, x='Column1', y='Column2')
    # fig2 = px.bar(df2, x='Category', y='Count')
    # fig3 = px.line(df3, x='Date', y='Value')

    img_bytes1 = fig1.to_image(format="png")
    img_bytes2 = fig2.to_image(format="png")
    img_bytes3 = fig3.to_image(format="png")

    img1 = base64.b64encode(img_bytes1).decode("utf-8")
    img2 = base64.b64encode(img_bytes2).decode("utf-8")
    img3 = base64.b64encode(img_bytes3).decode("utf-8")

    # Create the HTML template
    template = f'''
    <h1>Your SteamPulse Report</h1>
    <p>Here are some visualizations and data tables:</p>
    
    <h2>Graph 1</h2>
    <img style="width: 400px; height: 300px" src="data:image/png;base64,{img1}">
    
    <h2>Graph 2</h2>
    <img style="width: 400px; height: 300px" src="data:image/png;base64,{img2}">
    
    <h2>Graph 3</h2>
    <img style="width: 400px; height: 300px" src="data:image/png;base64,{img3}">
    '''

    convert_html_to_pdf(template, environ.get("REPORT_FILE"))


def send_email():

    client = boto3.client("ses",
                          region_name="eu-west-2",
                          aws_access_key_id=environ["AWS_ACCESS_KEY_ID"],
                          aws_secret_access_key=environ["AWS_SECRET_ACCESS_KEY"])

    message = MIMEMultipart()
    message["Subject"] = "Local Test"

    attachment = MIMEApplication(open(environ.get("REPORT_FILE"), 'rb').read())
    attachment.add_header('Content-Disposition',
                          'attachment', filename='report.pdf')
    message.attach(attachment)

    print(message)

    client.send_raw_email(
        Source='trainee.hassan.kashif@sigmalabs.co.uk',
        Destinations=[
            'trainee.hassan.kashif@sigmalabs.co.uk',
        ],
        RawMessage={
            'Data': message.as_string()
        }
    )


def plot_reviews_per_game_frequency(df_releases: DataFrame) -> Chart:
    """
    Create a bar chart for the number of reviews per game

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = df_releases.groupby(
        "title").size().reset_index()
    df_releases.columns = ["title", "num_of_reviews"]

    chart = px.bar(df_releases, x='num_of_reviews', y='title')

    return chart


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

    chart = px.line(df_releases, x='release_date', y='num_of_games')

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
        "release_date").size().reset_index()
    df_releases.columns = ["release_date", "num_of_reviews"]

    chart = px.line(df_releases, x='release_date', y='num_of_reviews')

    return chart


def handler(event, context):
    game_df = pd.read_csv("mock_data.csv")
    game_df["release_date"] = pd.to_datetime(
        game_df['release_date'], format='%d/%m/%Y')
    game_df["review_date"] = pd.to_datetime(
        game_df['review_date'], format='%d/%m/%Y')

    reviews_per_game_release_frequency_plot = plot_reviews_per_game_frequency(
        game_df)
    games_release_frequency_plot = plot_games_release_frequency(game_df)
    games_review_frequency_plot = plot_games_review_frequency(game_df)
    create_report(reviews_per_game_release_frequency_plot,
                  games_release_frequency_plot, games_review_frequency_plot)
    print("Report created.")
    send_email()
    print("Email sent.")


if __name__ == "__main__":
    # Temporary mock data

    # Start of dashboard script
    load_dotenv()
    config = environ

    # conn = get_db_connection(config)

    # game_df = get_database(conn)

    print(handler(None, None))
