# Live_pipeline

This is for live_pipeline

## Configure environment

```sh
python3 -m venv venv
source ./venv/bin/activate
pip3 install -r requirements.txt
```

## Configure environment variables

The following environment variables must be supplied in a `.env` file.

## Run the code

Main scripts:
`python3 extract_games.py`
`python3 transform_games.py`

Testing:
`pytest test_extract_games.py`
`pytest test_transform_games.py`

## Docker image

Build the docker image

```sh
docker build -t name_of_file . --platform "linux/amd64"
```

Run the docker image locally

```sh
docker run --env-file .env name_of_file
```

## File explained

extract_games.py -- script containing the code to scrape game metric data from both the Steam website and API.
transform_games.py -- script containing code transforming raw data into atomic rows.

conftest.py -- contains a few pytest fixtures required for testing
test_extract_games.py -- testing script for the functions in extract_games
test_transform_games.py -- testing script for function in transform_games

#### Assumptions and design decisions

We have chosen to supplement the initially scraped data from the Steam website with the Game API information to collect more data on each game which will be necessary for our pipeline.
During transformation, we decided to create unique atomic rows for the data which would be in line with our normalised schema. We have chosen not to modify the game titles as we did not want to lose data on games that are in different languages and hence would have different characters to the English alphabet. We combined the genres (from API) and user_tags (from web scraping) information to have a complete list of all associated genres and created a separate column so we could see which ones were assigned by the user. If a tag was in both genres and user-tags this would be classified as not user-generated. Any duplicate rows are removed during the transformation process.
