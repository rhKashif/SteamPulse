"""Python Script: Build a report for email attachment"""
import base64
from datetime import datetime, timedelta
from os import environ, _Environ

import altair as alt
from altair.vegalite.v5.api import Chart
from dotenv import load_dotenv
import pandas as pd
from pandas import DataFrame
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
    """
    """
    # open output file for writing (truncated binary)
    result_file = open(output_filename, "w+b")

    # convert HTML to PDF
    pisa_status = pisa.CreatePDF(
        source_html,                # the HTML to convert
        dest=result_file)           # file handle to recieve result

    # close output file
    result_file.close()                 # close output file

    return pisa_status.err


def get_new_releases(df_releases: DataFrame) -> int:
    """
    Return the number of new releases for the previous day

    Args: 
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        int: An integer relating to the number of new games released
    """
    date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    return df_releases[df_releases["release_date"] == date].shape[0]


def get_top_rated_release(df_releases: DataFrame) -> int:
    """
    Return the name of new release with the highest overall sentiment score

    Args: 
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        int: An integer relating to the number of new games released
    """
    date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    return df_releases[df_releases["release_date"] == date].shape[0]


def create_report(df_releases: DataFrame, chart_one: Chart, chart_two: Chart, chart_three: Chart):
    """
    """

    new_releases = get_new_releases(df_releases)
    chart_one.save("/tmp/chart_one.png")
    chart_two.save("/tmp/chart_two.png")
    chart_three.save("/tmp/chart_three.png")

    fig1 = "/tmp/chart_one.png"
    fig2 = "/tmp/chart_two.png"
    fig3 = "/tmp/chart_three.png"

    # background_color = "#1b2838"
    header_color = "#1b2838"

    # header_color = "#66c0f4"
    text_color = "#f5f4f1"

    template = f'''
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 18px;
                text-align: center;

            }}
            h1, {{
                background-color: {header_color};
                color: {text_color};
                padding: 50px;
                font-size: 32px;
                text-align: center;
            }}
            h2 {{
                background-color: {header_color};
                color: {text_color};
                padding-top: 15px;
                padding-bottom: 0px;
            }}
        </style>
    </head>
    <body>
        <h1>Your SteamPulse Report</h1>
        <p>Number of new releases: {new_releases}</p>
        
        <h2>Chart 1</h2>
        <img src="{fig1}" alt="Chart 1">
        
        <h2>Chart 2</h2>
        <img src="{fig2}" alt="Chart 2">
        
        <h2>Chart 3</h2>
        <img src="{fig3}" alt="Chart 3">
    </body>    
    </html>
    '''
    with open("test.html", "w") as file:
        file.write(template)

    convert_html_to_pdf(template, environ.get("REPORT_FILE"))


def send_email():
    """
    """
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
    custom_ticks = [i for i in range(
        0, df_releases["num_of_reviews"].max() + 1)]

    chart = alt.Chart(df_releases).mark_bar(
    ).encode(
        x=alt.X("num_of_reviews", title="Number of Reviews",
                axis=alt.Axis(values=custom_ticks, tickMinStep=1, titlePadding=10)),
        y=alt.Y("title", title="Release Title", sort="-x")
    ).properties(
        title="Number of Reviews per Release",
        width=800,
        height=400
    )

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
    custom_ticks = [i for i in range(
        0, df_releases["num_of_games"].max() + 1)]

    chart = alt.Chart(df_releases).mark_line(
        color="#44bd4f"
    ).encode(
        x=alt.X("release_date:O", title="Release Date",
                timeUnit="yearmonthdate"),
        y=alt.Y("num_of_games:Q", title="Number of Games",
                axis=alt.Axis(values=custom_ticks, tickMinStep=1, titlePadding=10))
    ).properties(
        title="New Releases per Day",
        width=800,
        height=400
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
        "release_date").size().reset_index()
    df_releases.columns = ["release_date", "num_of_reviews"]
    custom_ticks = [i for i in range(
        0, df_releases["num_of_reviews"].max() + 1)]

    chart = alt.Chart(df_releases).mark_line(
        color="#44bd4f"
    ).encode(
        x=alt.X("release_date:O", title="Release Date",
                timeUnit="yearmonthdate"),
        y=alt.Y("num_of_reviews:Q", title="Number of Reviews", axis=alt.Axis(
            values=custom_ticks, tickMinStep=1, titlePadding=10)),
    ).properties(
        title="New Reviews per Day",
        width=800,
        height=400
    )

    return chart


def handler(event, context):
    """
    """
    game_df = pd.read_csv("mock_data.csv")
    game_df["release_date"] = pd.to_datetime(
        game_df['release_date'], format='%d/%m/%Y')
    game_df["review_date"] = pd.to_datetime(
        game_df['review_date'], format='%d/%m/%Y')

    reviews_per_game_release_frequency_plot = plot_reviews_per_game_frequency(
        game_df)
    games_release_frequency_plot = plot_games_release_frequency(game_df)
    games_review_frequency_plot = plot_games_review_frequency(game_df)
    create_report(game_df, reviews_per_game_release_frequency_plot,
                  games_release_frequency_plot, games_review_frequency_plot)
    print("Report created.")
    # send_email()
    # print("Email sent.")


if __name__ == "__main__":
    # Temporary mock data

    # Start of dashboard script
    load_dotenv()
    config = environ

    # conn = get_db_connection(config)

    # game_df = get_database(conn)

    print(handler(None, None))
