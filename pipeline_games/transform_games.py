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


if __name__ == "__main__":

    data_frame = pd.read_csv('games.csv')

    unique_tags_df = identify_unique_tags(data_frame)
    user_generated_df = create_user_generated_column(unique_tags_df)
    data_frame_no_genres = drop_unnecessary_columns(
        user_generated_df, 'genres')
    data_with_unique_tags_only = drop_unnecessary_columns(
        data_frame_no_genres, 'user_tags')
