"""Script combining extract, transform and load"""
from os import environ
from dotenv import load_dotenv
import pandas as pd

from extract_games import get_html, parse_app_id_bs, update_game_information
from transform_games import identify_unique_genre, create_user_generated_column, drop_unnecessary_columns, convert_date_to_datetime, convert_price_to_float, check_data_is_not_null, explode_column_to_individual_rows
from load_games import get_db_connection, upload_publishers, upload_developers, upload_genres, upload_games, upload_game_genre_link, upload_game_publisher_link, upload_game_developer_link

if __name__ == "__main__":

    RELEASE_WEBSITE = "https://store.steampowered.com/search/?sort_by=Released_DESC&category1=998&supportedlang=english&ndl=1"

    website = get_html(RELEASE_WEBSITE)
    all_games = parse_app_id_bs(website)

    all_games = update_game_information(all_games)
    data_frame = pd.DataFrame(all_games)

    unique_genre_df = identify_unique_genre(data_frame)
    user_generated_df = create_user_generated_column(unique_genre_df)
    data_frame_no_genres = drop_unnecessary_columns(
        user_generated_df, 'genres')
    data_with_unique_genre_only = drop_unnecessary_columns(
        data_frame_no_genres, 'user_tags')

    data_with_unique_genre_only['release_date'] = data_with_unique_genre_only['release_date'].apply(
        convert_date_to_datetime)

    data_with_unique_genre_only['full_price'] = data_with_unique_genre_only['full_price'].apply(
        convert_price_to_float)

    data_with_unique_genre_only['sale_price'] = data_with_unique_genre_only['sale_price'].apply(
        convert_price_to_float)

    data_with_unique_genre_only['developers'] = data_with_unique_genre_only['developers'].apply(
        check_data_is_not_null)

    data_with_unique_genre_only['publishers'] = data_with_unique_genre_only['publishers'].apply(
        check_data_is_not_null)

    unique_developers = explode_column_to_individual_rows(
        data_with_unique_genre_only, 'developers')
    final_df = explode_column_to_individual_rows(
        unique_developers, 'publishers')

    game_df = final_df.copy()

    for column in ['genre', 'user_generated', 'developers', 'publishers']:
        game_df = drop_unnecessary_columns(game_df, column)

    games_df = game_df.drop_duplicates()
    games_only = games_df.copy()

    load_dotenv()
    configuration = environ
    connect_d = get_db_connection(configuration)

    try:
        upload_publishers(final_df, connect_d)
        upload_developers(final_df, connect_d)
        upload_genres(final_df, connect_d)
        upload_games(games_only, connect_d)
        upload_game_genre_link(final_df, connect_d)
        upload_game_publisher_link(final_df, connect_d)
        upload_game_developer_link(final_df, connect_d)

    finally:
        connect_d.close()
