"""Python Script: Build a report for email attachment"""
from datetime import datetime, timedelta
from os import environ, _Environ

import altair as alt
from altair.vegalite.v5.api import Chart
import boto3
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from functools import reduce
import pandas as pd
from pandas import DataFrame
from psycopg2 import connect
from psycopg2.extensions import connection
from xhtml2pdf import pisa


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


def convert_html_to_pdf(source_html: str, output_filename: str) -> int:
    """
    Converts a html file to a PDF 

    Args:
        source_html (str): A file containing html formatted code

        output_filename (str): A string representing the desired output PDF file name

    Returns:
        int: An int value associate with an error code

    """
    result_file = open(output_filename, "w+b")

    pisa_status = pisa.CreatePDF(
        source_html,
        dest=result_file)

    result_file.close()

    return pisa_status.err


def get_data_for_release_date(df_releases: DataFrame, index: int) -> DataFrame:
    """
    Return a DataFrame for a specific date behind the current date

    Args:
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

        index (int): An integer representing the number of days to go back from current date

    Returns:
        DataFrame: A pandas DataFrame containing all relevant game data for a specific date
    """
    date = (datetime.now() - timedelta(days=index)).strftime("%Y-%m-%d")

    return df_releases[df_releases["release_date"] == date]


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


def get_number_of_new_releases(df_releases: DataFrame) -> int:
    """
    Return the number of new releases for the previous day

    Args: 
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        int: An integer relating to the number of new games released
    """
    df_releases = get_data_for_release_date(df_releases, 1)

    return df_releases.drop_duplicates("title").shape[0]


def get_top_rated_release(df_releases: DataFrame) -> str:
    """
    Return the name of new release with the highest overall sentiment score for the previous day

    Args: 
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        str: A string relating to the title of the highest rated new game released
    """
    df_releases = get_data_for_release_date_range(df_releases, 8)
    df_ratings = df_releases.groupby("title")["sentiment"].mean(
    ).sort_values(ascending=False).reset_index()

    return df_ratings.head(1)["title"][0]


def get_most_reviewed_release(df_releases: DataFrame) -> str:
    """
    Return the name of new release with the highest overall sentiment score for the previous day

    Args: 
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        str: A string relating to the title of the highest rated new game released
    """
    df_releases = get_data_for_release_date_range(df_releases, 8)

    df_ratings = df_releases.groupby("title")["review_text"].count(
    ).sort_values(ascending=False).reset_index()

    return df_ratings.head(1)["title"][0]


def aggregate_release_data(df_releases: DataFrame) -> DataFrame:
    """
    Transform data in releases DataFrame to find aggregated data from individual releases

    Args:
        df_release (DataFrame): A DataFrame containing new release data

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


def plot_table(df_releases: DataFrame, rows: int) -> Chart:
    """
    Create a table from a given DataFrame

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data for a chart

        rows (int): An integer value representing the number of rows to be displayed

    Returns:
        Chart: A chart displaying plotted table
    """
    chart = alt.Chart(
        df_releases.reset_index().head(rows)
    ).mark_text().transform_fold(
        df_releases.columns.tolist()
    ).encode(
        alt.X(
            "key",
            type="nominal",
            axis=alt.Axis(
                orient="top",
                labelAngle=0,
                title=None,
                ticks=False
            ),
            scale=alt.Scale(padding=10),
            sort=None,
        ),
        alt.Y("index", type="ordinal", axis=None),
        alt.Text("value", type="nominal"),
    ).properties(
        width=1000,
    )
    return chart


def plot_trending_games_sentiment_table(df_releases: DataFrame) -> None:
    """
    Create a table for the top recommended games by sentiment

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted table
    """
    df_releases = get_data_for_release_date_range(df_releases, 8)
    df_merged = aggregate_release_data(df_releases)

    df_releases = df_merged.sort_values(
        by=["Community Sentiment"], ascending=False)
    df_releases = format_columns(df_releases)

    df_releases = df_releases.reset_index(drop=True)

    chart = plot_table(df_releases, 5)
    return chart


def plot_trending_games_review_table(df_releases: DataFrame) -> None:
    """
    Create a table for the top recommended games by number of reviews 

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted table
    """
    df_releases = get_data_for_release_date_range(df_releases, 8)
    df_merged = aggregate_release_data(df_releases)

    df_releases = df_merged.sort_values(
        by=["Number of Reviews"], ascending=False)
    df_releases = format_columns(df_releases)

    df_releases = df_releases.reset_index(drop=True)

    chart = plot_table(df_releases, 5)
    return chart


def plot_new_games_today_table(df_releases: DataFrame) -> None:
    """
    Create a table for the new releases today

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted table
    """
    df_releases = get_data_for_release_date(df_releases, 1)
    num_new_releases = get_number_of_new_releases(df_releases)
    df_merged = aggregate_release_data(df_releases)

    df_releases = df_merged.sort_values(
        by=["Release Date"], ascending=False)
    df_releases = format_columns(df_releases)

    df_releases = df_releases.reset_index(drop=True)

    chart = plot_table(df_releases, num_new_releases)
    return chart


def build_figure_from_plot(plot: Chart, figure_name: str) -> str:
    """
    Build a .png file for a plot and return its path

    Args:
        plot (Chart): A chart displaying plotted data

        figure_name (str): A string for use as the name of the created .png file

    Return:
        str: A string representing the path of a .png file
    """
    plot.save(f"/tmp/{figure_name}.png")
    return f"/tmp/{figure_name}.png"


def create_report(df_releases: DataFrame, dashboard_url: str) -> None:
    """
    Create a pdf file from a html string

    Args:  
        df_releases (DataFrame): A DataFrame containing new release information

        dashboard_url (str): A str representing a url link for the dashboard

    Returns:
        None
    """

    new_releases = get_number_of_new_releases(df_releases)
    top_rated_release = get_top_rated_release(df_releases)
    most_reviewed_release = get_most_reviewed_release(df_releases)

    trending_release_sentiment_table_plot = plot_trending_games_sentiment_table(
        df_releases)
    trending_release_review_table_plot = plot_trending_games_review_table(
        df_releases)
    new_release_table_plot = plot_new_games_today_table(df_releases)

    new_release_table_fig = build_figure_from_plot(
        new_release_table_plot, "table_one")
    trending_release_sentiment_fig = build_figure_from_plot(
        trending_release_sentiment_table_plot, "table_two")
    trending_release_review_fig = build_figure_from_plot(
        trending_release_review_table_plot, "table_three")

    date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    date_range = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")

    header_color = "#1b2838"
    text_color = "#f5f4f1"

    template = f'''
    <html>
    <head>
        <style>
            @page {{
                size: letter portrait;
                @frame header_frame {{           /* Static frame */
                    -pdf-frame-content: header_content;
                    left: 50pt; width: 512pt; top: 50; height: 300pt;
                }}
                @frame col1_frame {{             /* Content frame 1 */
                    left: 50pt; width: 512pt; top: 232pt; height: 365pt;
                }}
                @frame footer_frame {{           /* Static frame */
                    -pdf-frame-content: footer_content;
                    left: 50pt; width: 512pt; top: 656pt; height: 200pt;
                }}  
            }}          
            body {{
                font-family: Arial, sans-serif;
                font-size: 18px;
                text-align: left;
            }}
            h1 {{
                background-color: {header_color};
                color: {text_color};
                padding-bottom: 25px;
                padding-top: 50px;
                font-size: 32px;
                text-align: center;
                }}            
            h2 {{
                background-color: {header_color};
                color: {text_color};
                padding-top: 10px;
                font-size: 11px;
                text-align: center;
            }} 
            h3 {{
                background-color: {header_color};
                color: {text_color};
                padding-bottom: 5px;
                padding-top: 20px;
                font-size: 22px;
                text-align: center;
                }} 
            .myDiv {{
                border: 1px solid black; 
                padding: 5px;
                background-color: #f5f5f5;
            }}   
            .myDiv2 {{
                text-align: center;
            }}            
            </style>
    </head>

    <body>
        <div id="header_content">
            <h1>New Release Report</h1>
                <div class = "myDiv2">
                    <p>Number of New Releases ({date}): {new_releases}<br>
                    Top Rated Release ({date_range} - {date}): {top_rated_release}<br>
                    Most Reviewed Release ({date_range} - {date}): {most_reviewed_release}</p>
                </div>
        </div>

        <h2>New Releases</h2>
        <img src="{new_release_table_fig}" alt="Chart 1">

        <h2>Top Releases by Sentiment</h2>
        <img src="{trending_release_sentiment_fig}" alt="Chart 2">

        <h2>Top Releases by Number of Reviews</h2>
        <img src="{trending_release_review_fig}" alt="Chart 3">
        
        <div id="footer_content">
            <h3><a href={dashboard_url}>SteamPulse Dashboard</a></h3>
        SteamPulse - page <pdf:pagenumber>
        </div>


    </body>    
    </html>
    '''

    with open("test.html", "w") as file:
        file.write(template)

    convert_html_to_pdf(template, environ.get("REPORT_FILE"))


def send_email():
    """
    Send an email with an attached PDF report using Amazon Simple Email Service (SES).

    Args:
        None

    Returns:
        None
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

    client.send_raw_email(
        Source='trainee.hassan.kashif@sigmalabs.co.uk',
        Destinations=[
            'trainee.hassan.kashif@sigmalabs.co.uk',
        ],
        RawMessage={
            'Data': message.as_string()
        }
    )


def handler(event, context) -> None:
    """
    AWS Lambda function to generate a report, send it via email using Amazon SES.

    Args:
        event: AWS Lambda event
        context: AWS Lambda context  

    Return:
        None
    """
    load_dotenv()
    config = environ

    conn = get_db_connection(config)
    game_df = get_database(conn)
    game_df = format_database_columns(game_df)

    create_report(game_df, config["DASHBOARD_URL"])
    print("Report created.")
    # send_email()
    # print("Email sent.")


if __name__ == "__main__":

    handler(None, None)
