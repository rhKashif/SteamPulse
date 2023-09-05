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

Main script:
`python3 extract_games.py`

Testing:
`pytest test_extract_games.py`

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

extract_games.py -- is the script containing the code to scrape game metric data from both the Steam website and API.
conftest.py -- contains a few pytest fixtures required for testing
test_extract_games.py -- testing script for the functions in extract_games

#### Assumptions and design decisions

We have chosen to supplement the initially scraped data from the Steam website with the Game API information to collect more data on each game which will be necessary for our pipeline.
