"""File with unit tests for sentiment.py"""

from unittest.mock import MagicMock

from sentiment import remove_stopwords, isolate_non_stop_words, get_sentiment_values


def test_remove_stopwords(fake_review):
    """Verifies that the function correctly removes punctuation
    and stop words provided"""
    assert remove_stopwords(fake_review, ["fail"], [";", ","]) == "Test review"


def test_isolate_non_stop_words(monkeypatch, fake_df_sentiment):
    """Verifies that a data-frame column review is correctly modified
    to not include punctuation and stop words"""
    monkeypatch.setattr("sentiment.stopwords.words", lambda *args: ["fail"])
    returned_df = isolate_non_stop_words(fake_df_sentiment)
    assert "clean_review" in returned_df.columns
    assert "Test review" in returned_df["clean_review"].values


def test_get_sentiment_values(fake_df_sentiment, monkeypatch):
    """Verifies that sentiment values are correctly returned and formatted"""
    fake_df_sentiment.rename(columns={"review": "clean_review"}, inplace=True)
    fake_sentiment_analyser = MagicMock()
    fake_sentiment_analyser.polarity_scores.return_value = {"compound": 0}
    monkeypatch.setattr("sentiment.SentimentIntensityAnalyzer",
                lambda *args: fake_sentiment_analyser)
    returned_df = get_sentiment_values(fake_df_sentiment)
    assert returned_df["sentiment"].values[0] == 2.5
