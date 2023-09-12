# SteamPulse

An integrated dashboard displaying trend analysis for new releases on steam

## Configure environment

```sh
python3 -m venv venv
source ./venv/bin/activate
pip3 install -r requirements.txt
```

## Configure environment variables

The following environment variables must be supplied in a `.env` file in the root directory, and a `terraform.tfvars` file in the setup directory:

```sh
ACCESS_KEY_ID     = XXXXXXXXXXX
SECRET_ACCESS_KEY = XXXXXXXXXXX
DATABASE_NAME     = steampulse
DATABASE_USERNAME = steampulse_admin
DATABASE_PASSWORD = XXXXXXXXXXX
DATABASE_ENDPOINT = XXXXXXXXXXX
```

If hosting this service on AWS, you'll need to create your RDS to get the database endpoint.

## Setup cloud resources

**Warning** - AWS can incur unexpected costs, be sure you know what you're doing before replicating this section.

0. If you haven't already, setup [terraform](https://developer.hashicorp.com/terraform/downloads) and [docker](https://docs.docker.com/engine/install/).

1. Navigate to the setup directory.

2. `terraform init` to initalise the directory with terraform setup files.

3. `terraform apply` to construct AWS resources.

4. TODO(I haven't set this up yet, but we output should give us the db endpoint) -> add it to your env file.

5. Use `psql` to run `schema.sql` targetting your cloud database.

6. Navigate to pipeline_games.

7. Dockerise the games pipeline.

8. Test it runs locally, dockerised.

9. Push the image to the game pipeline ECR.

10. Repeat steps 6-9 for the review pipeline, dashboard, and email report directories.

11. You should now have an automated pair of pipelines, a Streamlit dashboard service, and a lambda function which emails reports to users.

### Docker image

Build the docker image

```sh
docker build -t name_of_file . --platform "linux/amd64"
```

Run the docker image locally

```sh
docker run --env-file .env name_of_file
```

### Games ETL Pipeline

## File explained

- extract_games.py -- script containing the code to scrape game metric data from both the Steam website and API.
- transform_games.py -- script containing code transforming raw data into atomic rows.
- load_games.py -- script containing code to load data into the database.

- conftest.py -- contains a few pytest fixtures required for testing
- test_extract_games.py -- testing script for the functions in extract_games
- test_transform_games.py -- testing script for function in transform_games
- test_load_games.py -- testing script for function in load_games

#### Assumptions and design decisions

We have chosen to supplement the initially scraped data from the Steam website with the Game API information to collect more data on each game which will be necessary for our pipeline.

During transformation, we decided to create unique atomic rows for the data which would be in line with our normalised schema. We have chosen not to modify the game titles as we did not want to lose data on games that are in different languages and hence would have different characters to the English alphabet. We combined the genres (from API) and user_tags (from web scraping) information to have a complete list of all associated genres and created a separate column so we could see which ones were assigned by the user. If a tag was in both genres and user-tags this would be classified as not user-generated. Any duplicate rows are removed during the transformation process.

During loading, we chose to use a psycopg2 function called execute_batch which loaded data quickly into the database. In addition we have chosen to use our schema design of 'UNIQUE' categories to prevent duplication of existing data.

## Reviews ETL pipeline

# TODO - talk about running nltk download

### Overview

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

## Streamlit Dashboard

## Email Report

#### Assumptions and design decisions

### Continuous Integration and Continuous Deployment

We have implemented continuous integration in our project by creating automated github workflows when code is pulled and pushed from the main branch. All code is maintained over a pylint score of 8 and has been tested with pytest.
