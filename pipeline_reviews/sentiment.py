"""Sentiment analysis on extracted reviews"""

from pandas import DataFrame
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer


def remove_stopwords(review: str, stop_words: list[str], punctuation: list[str]) -> str:
    """Returns review without stop words and most punctuation"""
    review = "".join(letter for letter in review if letter not in punctuation)
    split_review = review.replace("\n"," ").split(" ")
    return " ".join(word for word in split_review if word.lower() not in stop_words)


def isolate_non_stop_words(reviews_df: DataFrame) -> DataFrame:
    """Returns a data-frame ready to process for sentiment scores
    with cleaned text in reviews section"""
    stop_words = stopwords.words("english")
    punctuation_and_more = ["/",".",",","@","£","#","+","=","_",
            "-",")","(","*","^","%","$","~","`","'",'"',"<",">","1",
            "0","2","3","4","5","6","7","8","9",";",":","|","{","}","[","]"]
    reviews_df["clean_review"] = reviews_df["review"].apply(
        lambda review: remove_stopwords(review, stop_words, punctuation_and_more))
    return reviews_df


def get_sentiment_values(reviews_df: DataFrame) -> DataFrame:
    """Returns a data-frame with sentiment scores for each review"""
    vader = SentimentIntensityAnalyzer()
    reviews_df_copy = reviews_df.copy()
    reviews_df_copy["sentiment"] = reviews_df_copy["clean_review"].apply(lambda review:
                    vader.polarity_scores(review)["compound"])
    reviews_df_copy["sentiment"] = reviews_df_copy["sentiment"].apply(
            lambda score: round((score + 1)/2 * 5, 1))
    reviews_df_copy.drop(columns=["clean_review"], inplace=True)
    return reviews_df_copy
