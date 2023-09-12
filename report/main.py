"""Python Script: Build a report for email attachment"""
from datetime import datetime, timedelta
from os import environ, _Environ

import altair as alt
from altair.vegalite.v5.api import Chart
import boto3
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
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
    query = f""
    df_releases = pd.read_sql_query(query, conn_postgres)

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


def get_number_of_new_releases(df_releases: DataFrame) -> int:
    """
    Return the number of new releases for the previous day

    Args: 
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        int: An integer relating to the number of new games released
    """
    date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    return df_releases[df_releases["release_date"] == date].reset_index().shape[0]


def get_top_rated_release(df_releases: DataFrame) -> str:
    """
    Return the name of new release with the highest overall sentiment score for the previous day

    Args: 
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

    Returns:
        str: A string relating to the title of the highest rated new game released
    """
    df_releases = get_data_for_release_date(df_releases, 1)
    df_ratings = df_releases.groupby("title")["sentiment"].mean().reset_index()

    return df_ratings.head(1)["title"][0]


def get_release_information(df_releases: DataFrame, index: int) -> dict:
    """
    Return key information related to a new release

    Args:
        df_release (DataFrame): A DataFrame containing new release data

        index (int): A int associated with a number index within the trending game list

    Return:
        dict: A python dictionary containing all information relating to a game title
    """
    df_trending_game = df_releases.groupby(
        "title")["sentiment"].mean().reset_index().iloc[index]

    release_name = df_trending_game["title"]
    sentiment = round(df_trending_game["sentiment"], 1)
    release_df = df_releases[df_releases["title"]
                             == f"{release_name}"].reset_index().head(1)

    game_information = {
        "name": release_name,
        "sentiment": sentiment,
        "price": release_df["price"][0],
        "sale_price": release_df["sale_price"][0],
        "release_date": release_df["release_date"][0].strftime("%Y-%m-%d"),
        "mac_compatibility": release_df["mac"][0],
        "windows_compatibility": release_df["windows"][0],
        "linux_compatibility": release_df["linux"][0]
    }

    return game_information


def format_trending_game_information(df_releases: DataFrame, index: int) -> str:
    """
    Return information of new releases with the highest overall sentiment score for the previous day

    Args: 
        df_releases (DataFrame): A pandas DataFrame containing all relevant game data

        index (int): A int associated with a number index within the trending game list

    Returns:
        str: A string relating to the information of selected trending new game released in html format
    """
    df_releases = get_data_for_release_date(df_releases, 1)

    release_information = get_release_information(df_releases, index)

    html_template = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            p {{
                margin: 20px;
                line-height: 1.4;
            }}
        </style>
    </head>
    <body>
        <p><b>{release_information["name"]}</b><br>
        Price: £{release_information["price"]}<br>
        Sale Price: £{release_information["sale_price"]}<br>
        Average Sentiment: {release_information["sentiment"]}<br>
        Release Date: {release_information["release_date"]}<br>
        Platform Compatibility:<br>
        - Mac: {release_information["mac_compatibility"]}<br>
        - Windows: {release_information["windows_compatibility"]}<br>
        - Linux: {release_information["linux_compatibility"]}<br>
    </body>
    </html>
    """

    return html_template


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


def create_report(df_releases: DataFrame) -> None:
    """
    Create a pdf file from a html string

    Args:  
        df_releases (DataFrame): A DataFrame containing new release information

    Returns:
        None
    """

    new_releases = get_number_of_new_releases(df_releases)
    top_rated_release = get_top_rated_release(df_releases)
    trending_game_one = format_trending_game_information(df_releases, 0)
    trending_game_two = format_trending_game_information(df_releases, 1)
    trending_game_three = format_trending_game_information(df_releases, 1)

    reviews_per_game_release_frequency_plot = plot_reviews_per_game_frequency(
        df_releases)
    games_release_frequency_plot = plot_games_release_frequency(df_releases)
    games_review_frequency_plot = plot_games_review_frequency(df_releases)
    trending_games_plot = plot_top_trending_games(df_releases)

    fig1 = build_figure_from_plot(
        reviews_per_game_release_frequency_plot, "chart_one")
    fig2 = build_figure_from_plot(
        games_release_frequency_plot, "chart_two")
    fig3 = build_figure_from_plot(
        games_review_frequency_plot, "chart_three")
    fig4 = build_figure_from_plot(
        trending_games_plot, "chart_four")

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
                    left: 50pt; width: 512pt; top: 50; height: 350pt;
                }}
                @frame col1_frame {{             /* Content frame 1 */
                    left: 44pt; width: 245pt; top: 200pt; height: 365pt;
                }}
                @frame col2_frame {{             /* Content frame 2 */
                    left: 323pt; width: 245pt; top: 200pt; height: 365pt;
                }}
                @frame footer_frame {{           /* Static frame */
                    -pdf-frame-content: footer_content;
                    left: 50pt; width: 512pt; top: 650pt; height: 330pt;
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
                    <p>Number of new releases: {new_releases}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Top rated release: {top_rated_release}</p>
                </div>
            </div>
        <div id="footer_content">
            <h1>SteamPulse</h1>
        SteamPulse - page <pdf:pagenumber>
        </div>

        <h2>Number of Reviews per Release</h2>
        <img src="{fig1}" alt="Chart 1">

        <h2>New Releases per Day</h2>
        <img src="{fig2}" alt="Chart 2">
        
        <h2>New Reviews per Day</h2>
        <img src="{fig4}" alt="Chart 3">

        <h2>New Reviews per Day</h2>
        <img src="{fig3}" alt="Chart 4">

        <p>Trending games:</p>
        <div class = "myDiv">
            <p>{trending_game_one}</p>
        </div>
        <div class = "myDiv">
            <p>{trending_game_two}</p>
        </div>
        <div class = "myDiv">
            <p>{trending_game_three}</p>
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
        width=800,
        height=500
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
        width=800,
        height=400
    )

    return chart


def plot_top_trending_games(df_releases: DataFrame) -> Chart:
    """
    Create a line chart for the number of games released per day

    Args:
        df_releases (DataFrame): A DataFrame containing filtered data related to new releases

    Returns:
        Chart: A chart displaying plotted data
    """
    df_releases = get_data_for_release_date(df_releases, 1)

    df_releases = df_releases.groupby(
        "title")["sentiment"].mean().reset_index()

    df_releases.columns = ["title", "sentiment"]
    custom_ticks = [i for i in range(
        0, 6)]

    chart = alt.Chart(df_releases).mark_bar(
        color="#44bd4f"
    ).encode(
        y=alt.Y("title", title="Release Date"),
        x=alt.X("sentiment:Q", title="Sentiment Rating", axis=alt.Axis(
            values=custom_ticks, tickMinStep=1, titlePadding=10)),
    ).properties(
        width=800,
        height=500
    )

    return chart


def handler(event, context) -> None:
    """
    AWS Lambda function to generate a report, send it via email using Amazon SES.

    Args:
        event: AWS Lambda event
        context: AWS Lambda context  

    Return:
        None
    """
    game_df = pd.read_csv("mock_data.csv")
    game_df["release_date"] = pd.to_datetime(
        game_df['release_date'], format='%d/%m/%Y')
    game_df["review_date"] = pd.to_datetime(
        game_df['review_date'], format='%d/%m/%Y')

    # conn = get_db_connection(config)
    # game_df = get_database(conn)

    create_report(game_df)
    print("Report created.")
    send_email()
    print("Email sent.")


if __name__ == "__main__":

    load_dotenv()
    config = environ
    handler(None, None)
