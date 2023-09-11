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
