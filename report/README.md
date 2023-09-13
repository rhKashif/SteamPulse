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

### Foldername

#### Assumptions and design decisions
