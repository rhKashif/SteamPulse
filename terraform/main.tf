provider "aws" {
  region = "eu-west-2"
}


resource "aws_ecr_repository" "steampulse_pipeline_ecr" {
  name         = "steampulse_pipeline_ecr"
  force_delete = true

}


resource "aws_ecr_repository" "steampulse_dashboard_ecr" {
  name         = "steampulse_dashboard_ecr"
  force_delete = true
}