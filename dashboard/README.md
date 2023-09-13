# Dashboard

This is for dashboard

## Configure environment and setup requirements 

```sh
python3 -m venv venv
source ./venv/bin/activate
pip3 install -r requirements.txt
python3 setup_nltk.py
```

## Configure environment variables

The following environment variables must be supplied in a `.env` file.

```sh
AWS_ACCESS_KEY_ID     = XXXXXXXXXXX
AWS_SECRET_ACCESS_KEY = XXXXXXXXXXX
DATABASE_NAME     = steampulse
DATABASE_USERNAME = steampulse_admin
DATABASE_PASSWORD = XXXXXXXXXXX
DATABASE_ENDPOINT = XXXXXXXXXXX
DATABASE_PORT = XXXXXXXXXXX

```
## Run the code
```sh
streamlit run home.py
```
## Docker image

Build the docker image

```sh
docker build -t name_of_file . --platform "linux/amd64"
```

Run the docker image locally

```sh
docker run --env-file .env name_of_file
```
## Folders
pages - directory containing additional pages for streamlit dashboard
## Files 
`home.py` - script containing streamlit dashboard home page
`setup_nltk.py` - script containing installation for all nltk datasets

pages/`community.py` - script containing streamlit dashboard "community" page with visualizations relevant for users

pages/`developers.py` - script containing streamlit dashboard "developers" page with visualizations relevant for developers

pages/`releases.py` - script containing streamlit dashboard "releases" page with a table displaying all releases powering the visualizations

#### Assumptions and design decisions
Assumption that the necessary data is available, accurate, and up-to-date. This includes assumptions about data format, structure, and quality:
- Returns an error message if connection to the database fails
- If there is no data within the last two weeks the dashboard, a message will be displayed to relay

Assumption that the current word map will for review text will be useful and interesting for community members to see:
- More comprehensive language processing is required to increase the relevancy of words on the word map but given time constraints, this has not been implemented

Design decision - use of `format_sentiment_significant_figures` to format sentiment.