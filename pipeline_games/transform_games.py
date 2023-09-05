"""Script for transforming games data"""
import pandas as pd
import numpy as np


def identify_unique_tags(data: pd.DataFrame) -> pd.DataFrame:
    """Generates a tags column from user_tags and genres"""
    data['tags'] = data['user_tags'].astype(str) + "," + data["genres"]
    data['tags'] = data['tags'].str.split(',')
    data = data.explode('tags')

    data = data.drop_duplicates()
    return data


def create_user_generated_column(data: pd.DataFrame) -> pd.DataFrame:
    """Compares tag to genres and determine if tag is user-generated or not"""
    data['user_generated'] = np.where(
        np.isin(data['tags'], data['genres']), False, True)

    return data


def drop_unnecessary_columns(data: pd.DataFrame, column_name: str) -> pd.DataFrame:
    """Removes the no longer need columns"""
    data = data.drop(column_name, axis=1)

    return data


def convert_date_to_datetime(date: str):
    """Validates date if appropriate"""
    try:
        new_date = pd.to_datetime(date, format="%d %b, %Y")
    except AttributeError:
        new_date = 'invalid'

    return new_date


def convert_price_to_float(price: str) -> float:
    """Changes all prices to floats"""
    if str(price)[0] == '£':
        return float(price[1:])
    return 0.00


def explode_column_to_individual_rows(data: pd.DataFrame, column_name: str):
    """Make unique rows for each unique element in column"""
    data[column_name] = data[column_name].str.split(',')
    data = data.explode(column_name)

    return data


if __name__ == "__main__":

    data_frame = pd.read_csv('games.csv')

    unique_tags_df = identify_unique_tags(data_frame)
    user_generated_df = create_user_generated_column(unique_tags_df)
    data_frame_no_genres = drop_unnecessary_columns(
        user_generated_df, 'genres')
    data_with_unique_tags_only = drop_unnecessary_columns(
        data_frame_no_genres, 'user_tags')

    data_with_unique_tags_only['release_date'] = data_with_unique_tags_only['release_date'].apply(
        convert_date_to_datetime)

    data_with_unique_tags_only['full price'] = data_with_unique_tags_only['full price'].apply(
        convert_price_to_float)

    data_with_unique_tags_only['sale price'] = data_with_unique_tags_only['sale price'].apply(
        convert_price_to_float)

    unique_developers = explode_column_to_individual_rows(
        data_with_unique_tags_only, 'developers')
    final_df = explode_column_to_individual_rows(
        unique_developers, 'publishers')

    final_df.to_csv('transformed_data.csv')
