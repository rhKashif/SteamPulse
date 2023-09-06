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


#unfinished below

resource "aws_iam_role" "steampulse_pipeline_ecs_task_execution_role" {
  name = "steampulse_pipeline_ecs_task_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      },

      {
        Action = "sts:AssumeRole",
        Principal = {
          Service = "scheduler.amazonaws.com"
        },
        Effect = "Allow",
        Sid    = ""
      }
    ]
  })

  inline_policy {
    name = "ecs-task-inline-policy"
    policy = jsonencode({
      Version = "2012-10-17",
      Statement = [
        {
          Action   = "ecs:DescribeTaskDefinition",
          Effect   = "Allow",
          Resource = "*",
          Condition = {
            "ArnLike" : {
              "ecs:cluster" : "arn:aws:ecs:eu-west-2:129033205317:cluster/steampulse_cluster"
            }
          }
        },
        {
          Action   = "ecs:DescribeTasks",
          Effect   = "Allow",
          Resource = "*",
          Condition = {
            "ArnLike" : {
              "ecs:cluster" : "arn:aws:ecs:eu-west-2:129033205317:cluster/steampulse_cluster"
            }
          }
        },
        {
          Action   = "ecs:RunTask",
          Effect   = "Allow",
          Resource = "*",
          Condition = {
            "ArnLike" : {
              "ecs:cluster" : "arn:aws:ecs:eu-west-2:129033205317:cluster/steampulse_cluster"
            }
          }
        },
        {
          Action   = "iam:PassRole",
          Effect   = "Allow",
          Resource = "*"
        }
      ]

      }
    )

  }
}

resource "aws_iam_role" "steampulse_pipeline_ecs_task_role_policy" {
  name = "steampulse_pipeline_ecs_task_role_policy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        "Action" : "sts:AssumeRole",
        "Principal" : {
          "Service" : "ecs-tasks.amazonaws.com"
        },
        Effect = "Allow",
        Sid    = ""
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "steampulse_pipeline_ecs_task_execution_role_policy_attachment" {
  role       = aws_iam_role.steampulse_pipeline_ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}


resource "aws_ecs_task_definition" "steampulse_pipeline_task_definition" {
  family                   = "steampulse_pipeline_task_definition"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024
  memory                   = 2048
  task_role_arn            = aws_iam_role.steampulse_pipeline_ecs_task_role_policy.arn
  execution_role_arn       = aws_iam_role.steampulse_pipeline_ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name   = "steampulse_pipeline_ecr"
      image  = "129033205317.dkr.ecr.eu-west-2.amazonaws.com/steampulse_pipeline_ecr:latest"
      cpu    = 10
      memory = 512
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
        }
      ]
      essential : true,

      logConfiguration : {
        "logDriver" : "awslogs",
        "options" : {
          "awslogs-create-group" : "true",
          "awslogs-group" : "/ecs/",
          "awslogs-region" : "eu-west-2",
          "awslogs-stream-prefix" : "ecs"
        }
      }
    }
  ])
}


# resource "aws_ecs_task_definition" "name" {

# }


# resource "aws_ecs_service" "name" {

# }

# resource "aws_scheduler_schedule" "name" {

# }

