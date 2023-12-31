"""Script for transforming games data"""
import pandas as pd
from pandas._libs.tslibs.timestamps import Timestamp
import numpy as np


def identify_unique_genre(data: pd.DataFrame) -> pd.DataFrame:
    """Generates a genre column from user_tags and genres"""
    data['genre'] = data['user_tags'].astype(str) + "," + data["genres"]
    data = explode_column_to_individual_rows(data, 'genre')
    data = data.drop_duplicates()
    return data


def create_user_generated_column(data: pd.DataFrame) -> pd.DataFrame:
    """Compares tag to genres and determine if tag is user-generated or not"""
    data['user_generated'] = np.where(
        np.isin(data['genre'], data['genres']), False, True)

    return data


def drop_unnecessary_columns(data: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """Removes the no longer need columns"""
    data = data.drop(column_name, axis=1)

    return data


def convert_date_to_datetime(date: str) -> Timestamp | None:
    """Validates date, if appropriate"""
    try:
        new_date = pd.to_datetime(date, format="%d %b, %Y")
    except ValueError:
        new_date = None

    return new_date


def convert_price_to_float(price: str | float) -> float:
    """Changes all prices to floats"""
    price = str(price)
    if '£' in price:
        new_price = price.replace('£', '')
        return float(new_price)
    return 0.00


def explode_column_to_individual_rows(data: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """Make unique rows for each unique element in column"""
    data[column_name] = data[column_name].str.split(',')
    data = data.explode(column_name)

    return data


def check_data_is_not_null(data_value: str) -> str:
    if str(data_value) in ['N/A', 'None', 'Null', 'nan', 'NaN', '']:
        return "Data not provided"
    return data_value


if __name__ == "__main__":

    data_frame = pd.read_csv('games.csv')

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

    final_df.to_csv('genres.csv')

    for column in ['genre', 'user_generated', 'developers', 'publishers']:
        final_df = drop_unnecessary_columns(final_df, column)

    games_df = final_df.drop_duplicates()
    games_df.to_csv('final_games.csv')
