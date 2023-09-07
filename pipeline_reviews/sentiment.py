"""Sentiment analysis on extracted reviews"""

import pandas as pd
from pandas import DataFrame
from pandas.core.series import Series
import nltk
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer

from transform import change_column_types #! diff import here check red


def remove_stopwords(review: str, stop_words: list[str], punctuation: list[str]) -> str:
    """Returns review without stop words and most punctuation"""
    review = "".join(letter for letter in review if letter not in punctuation)
    split_review = review.replace("\n"," ").split(" ")
    return " ".join(word for word in split_review if word.lower() not in stop_words)


def isolate_non_stop_words(reviews_df: DataFrame) -> DataFrame:
    """Returns a data-frame ready to process for sentiment scores
    with cleaned text in reviews section"""
    nltk.download('stopwords')
    stop_words = stopwords.words('english')
    punctuation_and_more = ["/",".",",","@","£","#","+","=","_",
            "-",")","(","*","^","%","$","~","`","'",'"',"<",">","1",
            "0","2","3","4","5","6","7","8","9",";",":","|","{","}","[","]"]
    reviews_df["clean_review"] = reviews_df["review"].apply(
        lambda review: remove_stopwords(review, stop_words, punctuation_and_more))
    return reviews_df


def get_sentiment_values(reviews_df: DataFrame) -> DataFrame:
    """Returns a data-frame with sentiment scores for each review"""
    nltk.download('vader_lexicon')
    vader = SentimentIntensityAnalyzer()
    reviews_df["sentiment"] = reviews_df["clean_review"].apply(lambda review:
                    vader.polarity_scores(review)["compound"])
    reviews_df["sentiment"] = reviews_df["sentiment"].apply(
            lambda score: round((score + 1)/2 * 5, 1))
    reviews_df.drop(columns=["clean_review"], inplace=True)
    return reviews_df


def get_sentiment_per_game(reviews_df: DataFrame) -> Series:
    """Returns pandas series object with sentiment scores overall
    for each game ID"""
    each_game_sentiment_overall = reviews_df.groupby("game_id").sum("sentiment")["sentiment"]
    n_cols = reviews_df.groupby("game_id").count()["sentiment"]
    each_game_sentiment_overall = each_game_sentiment_overall.transform(
        lambda score: score/n_cols[score.index])
    return each_game_sentiment_overall


if __name__ == "__main__":
    reviews = pd.read_csv("reviews.csv")
    reviews = change_column_types(reviews) #! instead do a full transform here
    reviews = isolate_non_stop_words(reviews)
    reviews = get_sentiment_values(reviews)
    each_game_sentiment = get_sentiment_per_game(reviews)
    reviews.to_csv("reviews.csv")
    #! add unnamed:0 removal again
