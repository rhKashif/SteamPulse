# Reviews ETL pipeline
## Overview

Reviews are collected for each game that was released in the past 2 weeks and is currently in the database for the project. Games included and reviews are collected from Steam website or its APIs. Reviews are received from [Steam Reviews API](https://partner.steamgames.com/doc/store/getreviews). The data retrieved from the API includes:

- review (text of the review itself)
- review_score (indication of how many people up-voted the review)
- timestamp_created (timestamp at which the review was created)
- playtime_last_2_weeks (how many hours the user played the game in the past 2 weeks)
- next_cursor (this is only used for the retrieval of next reviews according to the API docs)

The reviews are processed and transformed with the assumptions for transform mentioned in the assumptions section below. Before uploading into the database, the reviews are processed with the use of natural language processing (NLP) to get their sentiment value which is expressed in a value ranging from 1 to 5 where the lower it is the more negative it was deemed by the machine. This is later used in the calculations for game popularity.

After the sentiment analysis, the reviews are loaded into the database to be stored for later use in the project.

## Assumptions

## Limitations

# Run the project

## Configure environment

```sh
python3 -m venv venv
source ./venv/bin/activate
```

## Install the requirements for the files
```
pip3 install -r requirements.txt
python3 nltk_download.py
```

## Configure environment variables

The following environment variables must be supplied in a `.env` file.

```
DATABASE_NAME=xxx
DATABASE_USERNAME=xxx
DATABASE_PASSWORD=xxx
DATABASE_ENDPOINT=xxx
```

## Run the code
From the pipeline_reviews folder
```
python3 pipeline.py
```
## Docker image

Build the docker image

```sh
docker build -t reviews_pipeline . --platform "linux/amd64"
```

Run the docker image locally

```sh
docker run --env-file .env reviews_pipeline
```
