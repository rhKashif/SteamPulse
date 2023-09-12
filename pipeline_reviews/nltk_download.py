"""Downloads necessary packages from nltk for sentiment.py"""

import nltk


if __name__ == "__main__":
    nltk.download('stopwords')
    nltk.download('vader_lexicon')
