## Report

This is for email report


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
REPORT_FILE = XXXXXXXXXXX.pdf
DASHBOARD_URL = XXXXXXXXXXX
EMAIL_SENDER = XXXXXXXXXXX
EMAIL_RECEIVER = XXXXXXXXXXX
```
## Run the code
```sh
python3 report.py
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

### Files
`lambda_function.py` - script containing code to make connection with database, extract all relevant data and build visualization plots, format them in html and convert to pdf. This pdf is emailed to a given email from a given email using the boto3 library and AWS SES. 

#### Assumptions and design decisions
Assumption that the necessary data is available, accurate, and up-to-date. This includes assumptions about data format, structure, and quality:
- Returns an error message if connection to the database fails
- If there is no data within the last two weeks the dashboard, a message will be displayed to relay

