# Pipeline_games

This pipeline is used to extract data by web scraping both newly released games and game-specific data from Steam and further supplementing this with data from the Steam API. The raw data is then transformed to standardise each category and remove unnecessary or inaccurate data using the pandas library. Following this, the transformed data is uploaded using SQL to an AWS RDS database.

## Configure environment

```sh
python3 -m venv venv
source ./venv/bin/activate
pip3 install -r requirements.txt
```

## Configure environment variables

The following environment variables must be supplied in a `.env` file.

```sh
ACCESS_KEY_ID     = XXXXXXXXXXX
SECRET_ACCESS_KEY = XXXXXXXXXXX
DATABASE_NAME     = steampulse
DATABASE_USERNAME = steampulse_admin
DATABASE_PASSWORD = XXXXXXXXXXX
DATABASE_IP       = XXXXXXXXXXX
DATABASE_PORT     = XXXXXXXXXXX
```

## Run the code

Main scripts:
`python3 extract_games.py`
`python3 transform_games.py`
`python3 load_games.py`

Testing:
`pytest test_extract_games.py`
`pytest test_transform_games.py`
`pytest test_load_games.py`

## Docker image

Build the docker image

```sh
docker build -t name_of_file . --platform "linux/amd64"
```

Run the docker image locally

```sh
docker run --env-file .env name_of_file
```

## Files explained

`extract_games.py` -- script containing the code to scrape game metric data from both the Steam website and API.
`transform_games.py` -- script containing code transforming raw data into atomic rows.
`load_games.py` -- script containing code to load data into the database.

`conftest.py` -- contains a few pytest fixtures required for testing
`test_extract_games.py` -- testing script for the functions in extract_games
`test_transform_games.py` -- testing script for function in transform_games
`test_load_games.py` -- testing script for function in load_games

#### Assumptions and design decisions

We have chosen to supplement the initially scraped data from the Steam website with the Game API information to collect more data on each game which will be necessary for our pipeline.

During transformation, we decided to create unique atomic rows for the data which would be in line with our normalised schema. We have chosen not to modify the game titles as we did not want to lose data on games that are in different languages and hence would have different characters to the English alphabet. We combined the genres (from API) and user_tags (from web scraping) information to have a complete list of all associated genres and created a separate column so we could see which ones were assigned by the user. If a tag was in both genres and user-tags this would be classified as not user-generated. Any duplicate rows are removed during the transformation process.

During loading, we chose to use a psycopg2 function called execute_batch which loaded data quickly into the database. In addition we have chosen to use our schema design of 'UNIQUE' categories to prevent duplication of existing data.
