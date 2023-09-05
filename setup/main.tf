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


resource "aws_ecs_cluster" "steampulse_cluster" {
  name = "steampulse_cluster"
}



resource "aws_db_instance" "steampulse_database" {
  allocated_storage      = 10
  engine                 = "postgres"
  instance_class         = "db.t3.micro"
  identifier             = "steampulse-database"
  db_name                = var.DATABASE_NAME
  username               = var.DATABASE_USERNAME
  password               = var.DATABASE_PASSWORD
  db_subnet_group_name   = "public_subnet_group"
  vpc_security_group_ids = [resource.aws_security_group.steampulse_rds_sg.id]
  availability_zone      = "eu-west-2a"
  skip_final_snapshot    = true
  publicly_accessible    = true
}

resource "aws_security_group" "steampulse_rds_sg" {
  name        = "steampulse_rds_sg"
  description = "Allows traffic to reach steampulse RDS"
  vpc_id      = "vpc-0e0f897ec7ddc230d"

  ingress {
    description = "Allows connection to RDS"
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "steampulse_rds_sg"
  }
}

resource "aws_security_group" "steampulse_pipeline_ecs_sg" {
  name        = "steampulse_pipeline_ecs_sg"
  description = "Allows traffic for the pipeline ECS"
  vpc_id      = "vpc-0e0f897ec7ddc230d"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }


  tags = {
    Name = "steampulse_pipeline_ecs_sg"
  }
}


#unfinished

resource "aws_iam_role" "name" {
  
}


resource "aws_iam_role_policy_attachment" "name" {
  
}

resource "aws_ecs_task_definition" "name" {
  
}


resource "aws_ecs_task_definition" "name" {
  
}


resource "aws_ecs_service" "name" {
  
}

resource "aws_scheduler_schedule" "name" {
  
}