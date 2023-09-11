# Reviews ETL pipeline
## Overview

This project focuses on the systematic collection and analysis of reviews for recently released video games within a 2-week time-frame. The reviews are sourced from the Steam website and its associated APIs, primarily using the [Steam Reviews API](https://partner.steamgames.com/doc/store/getreviews) for data acquisition of the reviews. The collected data comprises essential information about each review, including:

- **Review**: The textual content of the review.
- **Review Score**: An indication of the review's popularity, reflecting the number of up-votes received.
- **Timestamp Created**: The timestamp indicating when the review was submitted.
- **Playtime Last 2 Weeks**: Hours, that the user spent playing the game in the past 2 weeks.
- **Next Cursor**: A parameter used exclusively for the next retrieval of reviews, as specified in the API documentation.

### Data Processing and Transformation

Before integration into the project's database, the collected reviews undergo processing and transformation in alignment with predefined assumptions. To enhance their utility and relevance, we employ Natural Language Processing (NLP) techniques. Notably, sentiment analysis is conducted to assign a sentiment value to each review, expressed on a scale ranging from 1 to 5. A lower sentiment value suggests a more negative assessment by the automated analysis. This sentiment analysis data is used in calculations related to game popularity.

### Database Integration

Following sentiment analysis and processing, the reviews are seamlessly integrated into the project's database. This database serves as a repository for future utilisation within the project, providing a structured and accessible resource for ongoing analysis and assessment. The database to use was chosen to be PostgreSQL as it provided easy to use management tools and has strong security features.

### Cloud Integration and Automated Workflow

The project includes a Dockerfile which is uploaded on AWS Elastic Container Registry (ECR) and is used within a step function on AWS, activated daily with report created from the reviews and other data after the reviews gathering and transforming was completed. The script for review gathering also includes logs into the terminal of possible failures to retrieve/transform/load the data which are useful to see in AWS console to debug for later.

## Assumptions

During the data extracting phase, certain assumptions were made of the data, specifically:

- **Timestamp created** will always be in UNIX time format and will always be correct.
- **Review score** includes not both negative and positive votes (up + down) but only positive.
- The schema for the table reviews has a unique constraint: `UNIQUE(game_id, review_text, review_score, reviewed_at, sentiment)`. The assumption is that there will not be a review for any recently reviewed games that have all of the same values; this is to ensure that the same review is not included twice when gathering more reviews for the games that are already present in the database.
- Since the reviews API does not include the name of the game, it is assumed that the API correctly picks up reviews for the game with the correct game ID as it could not be verified.
- The project also assumes that the data presented in the overview above, will be present. This is assumed from various data gathering runs. Although not all of the API's promised keys were present, the ones included seemed to be.

## Limitations

Unfortunately, this project encountered certain limitations stemming from issues identified within the Steam Reviews API. For example, where the language for the endpoint was set to English - it would pick up some reviews in Spanish and other languages. Some ways were attempted to translate the reviews but proved to not work that well and since most received reviews were in English, this idea was moved to a potential future addition to the project.

Moreover, the API would not display 100 reviews per page when the endpoint was set to show 100 reviews per page. However, since the project focused on recent released games which would not have many reviews, this was deemed to not be a big disadvantage.

Even though it was assumed that the same cursor received from the endpoint with the same cursor would mean there are no more reviews for the game, it was noted that - it isn't always the case as when tested for old very popular games, only a small fraction of reviews could be gathered and most would not show up. It was also noticed that some cursors that could not be retrieved from a given game ID when looping through the pages of reviews, would show a page full of reviews when set to a random cursor in the endpoint: showing that there are more cursors available for a given game ID but were not accessible from the Steam API's endpoint. This anomaly implied the existence of undisclosed cursors associated with a given game ID within the Steam API, which were beyond the project's reach.

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
