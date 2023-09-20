provider "aws" {
  region = "eu-west-2"
}

resource "aws_ecr_repository" "steampulse_game_pipeline_ecr" {
  name         = "steampulse_game_pipeline_ecr"
  force_delete = true

}

resource "aws_ecr_repository" "steampulse_review_pipeline_ecr" {
  name         = "steampulse_review_pipeline_ecr"
  force_delete = true

}

resource "aws_ecr_repository" "steampulse_dashboard_ecr" {
  name         = "steampulse_dashboard_ecr"
  force_delete = true
}

resource "aws_ecr_repository" "steampulse_lambda_ecr" {
  name         = "steampulse_lambda_ecr"
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
      },


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
              "ecs:cluster" : aws_ecs_cluster.steampulse_cluster.arn
            }
          }
        },
        {
          Action   = "ecs:DescribeTasks",
          Effect   = "Allow",
          Resource = "*",
          Condition = {
            "ArnLike" : {
              "ecs:cluster" : aws_ecs_cluster.steampulse_cluster.arn
            }
          }
        },
        {
          Action   = "ecs:RunTask",
          Effect   = "Allow",
          Resource = "*",
          Condition = {
            "ArnLike" : {
              "ecs:cluster" : aws_ecs_cluster.steampulse_cluster.arn
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

resource "aws_ecs_task_definition" "steampulse_review_pipeline_task_definition" {
  family                   = "steampulse_review_pipeline_task_definition"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024
  memory                   = 2048
  task_role_arn            = aws_iam_role.steampulse_pipeline_ecs_task_role_policy.arn
  execution_role_arn       = aws_iam_role.steampulse_pipeline_ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name   = "steampulse_review_pipeline_ecr"
      image  = "${aws_ecr_repository.steampulse_review_pipeline_ecr.repository_url}:latest"
      cpu    = 10
      memory = 512

      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
        }
      ]

      essential : true,
      environment : [

        {
          "name" : "ACCESS_KEY_ID",
          "value" : var.ACCESS_KEY_ID
        },
        {
          "name" : "SECRET_ACCESS_KEY",
          "value" : var.SECRET_ACCESS_KEY
        },
        {
          "name" : "DATABASE_NAME",
          "value" : var.DATABASE_NAME
        },
        {
          "name" : "DATABASE_USERNAME",
          "value" : var.DATABASE_USERNAME
        },
        {
          "name" : "DATABASE_PASSWORD",
          "value" : var.DATABASE_PASSWORD
        },
        {
          "name" : "DATABASE_ENDPOINT",
          "value" : "${aws_db_instance.steampulse_database.address}"
        },
        {
          "name" : "DATABASE_PORT",
          "value" : "5432"
        }
      ]



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

resource "aws_ecs_task_definition" "steampulse_game_pipeline_task_definition" {
  family                   = "steampulse_game_pipeline_task_definition"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024
  memory                   = 2048
  task_role_arn            = aws_iam_role.steampulse_pipeline_ecs_task_role_policy.arn
  execution_role_arn       = aws_iam_role.steampulse_pipeline_ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name   = "steampulse_game_pipeline_ecr"
      image  = "${aws_ecr_repository.steampulse_game_pipeline_ecr.repository_url}:latest"
      cpu    = 10
      memory = 512

      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
        }
      ]

      essential : true,
      environment : [

        {
          "name" : "ACCESS_KEY_ID",
          "value" : var.ACCESS_KEY_ID
        },
        {
          "name" : "SECRET_ACCESS_KEY",
          "value" : var.SECRET_ACCESS_KEY
        },
        {
          "name" : "DATABASE_NAME",
          "value" : var.DATABASE_NAME
        },
        {
          "name" : "DATABASE_USERNAME",
          "value" : var.DATABASE_USERNAME
        },
        {
          "name" : "DATABASE_PASSWORD",
          "value" : var.DATABASE_PASSWORD
        },
        {
          "name" : "DATABASE_ENDPOINT",
          "value" : "${aws_db_instance.steampulse_database.address}"
        },
        {
          "name" : "DATABASE_PORT",
          "value" : "5432"
        }
      ]

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

resource "aws_ecs_task_definition" "steampulse_dashboard_task_definition" {
  family                   = "steampulse_dashboard_task_definition"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024
  memory                   = 4096
  task_role_arn            = aws_iam_role.steampulse_pipeline_ecs_task_role_policy.arn
  execution_role_arn       = aws_iam_role.steampulse_pipeline_ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name   = "steampulse_dashboard_ecr"
      image  = "${aws_ecr_repository.steampulse_dashboard_ecr.repository_url}:latest"
      cpu    = 10
      memory = 1024

      portMappings = [
        {
          "name" : "8501-mapping",
          "containerPort" : 8501,
          "hostPort" : 8501,
          "protocol" : "tcp",
          "appProtocol" : "http"
        },
        {
          "name" : "80-mapping",
          "containerPort" : 80,
          "hostPort" : 80,
          "protocol" : "tcp",
          "appProtocol" : "http"
        }
      ]

      essential : true,

      environment : [

        {
          "name" : "ACCESS_KEY_ID",
          "value" : var.ACCESS_KEY_ID
        },
        {
          "name" : "SECRET_ACCESS_KEY",
          "value" : var.SECRET_ACCESS_KEY
        },
        {
          "name" : "DATABASE_NAME",
          "value" : var.DATABASE_NAME
        },
        {
          "name" : "DATABASE_USERNAME",
          "value" : var.DATABASE_USERNAME
        },
        {
          "name" : "DATABASE_PASSWORD",
          "value" : var.DATABASE_PASSWORD
        },
        {
          "name" : "DATABASE_ENDPOINT",
          "value" : "${aws_db_instance.steampulse_database.address}"
        },
        {
          "name" : "DATABASE_PORT",
          "value" : "5432"
        }
      ]

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

resource "aws_scheduler_schedule" "steampulse_game_pipeline_schedule" {
  name                = "steampulse_game_pipeline_schedule"
  description         = "Runs the steampulse game pipeline on a cron schedule"
  schedule_expression = "cron(0 */3 * * ? *)"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_ecs_cluster.steampulse_cluster.arn
    role_arn = aws_iam_role.steampulse_pipeline_ecs_task_execution_role.arn

    ecs_parameters {
      task_definition_arn = aws_ecs_task_definition.steampulse_game_pipeline_task_definition.arn
      launch_type         = "FARGATE"

      network_configuration {
        assign_public_ip = true
        security_groups  = [aws_security_group.steampulse_pipeline_ecs_sg.id]
        subnets          = ["subnet-03b1a3e1075174995", "subnet-0667517a2a13e2a6b", "subnet-0cec5bdb9586ed3c4"]
      }
    }
  }
}

resource "aws_scheduler_schedule" "steampulse_review_report_schedule" {
  name                = "steampulse_review_report_schedule"
  description         = "Runs the steampulse step function, which runs review pipeline then email report on a cron schedule"
  schedule_expression = "cron(30 8 * * ? *)"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_sfn_state_machine.steampulse_state_machine.arn
    role_arn = aws_iam_role.steampulse_sfn_role.arn
  }
}

resource "aws_security_group" "steampulse_dashboard_sg" {
  name   = "steampulse_dashboard_sg"
  vpc_id = "vpc-0e0f897ec7ddc230d"
  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 80
    to_port     = 80
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
}

resource "aws_ecs_service" "steampulse_streamlit_service" {
  name            = "steampulse_streamlit_service"
  cluster         = aws_ecs_cluster.steampulse_cluster.id
  task_definition = aws_ecs_task_definition.steampulse_dashboard_task_definition.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  # load_balancer {
  #   target_group_arn = aws_lb_target_group.steampulse-lb-target-group.arn
  #   container_name = "steampulse_dashboard_ecr"
  #   container_port   = 8501
  # }

  network_configuration {
    subnets          = ["subnet-03b1a3e1075174995", "subnet-0cec5bdb9586ed3c4", "subnet-0667517a2a13e2a6b"]
    security_groups  = [aws_security_group.steampulse_dashboard_sg.id]
    assign_public_ip = true
  }
}





resource "aws_lambda_permission" "steampulse_lambda_allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.steampulse_email_lambda.function_name
  principal     = "events.amazonaws.com"

}

resource "aws_lambda_function" "steampulse_email_lambda" {
  image_uri     = "${aws_ecr_repository.steampulse_lambda_ecr.repository_url}:latest"
  package_type  = "Image"
  function_name = "steampulse_email_lambda"
  role          = aws_iam_role.steampulse_lambda_iam.arn
  timeout       = 300
  memory_size   = 256

  environment {
    variables = {
      ACCESS_KEY_ID     = var.ACCESS_KEY_ID,
      SECRET_ACCESS_KEY = var.SECRET_ACCESS_KEY,
      DATABASE_NAME     = var.DATABASE_NAME,
      DATABASE_USERNAME = var.DATABASE_USERNAME,
      DATABASE_PASSWORD = var.DATABASE_PASSWORD,
      DATABASE_ENDPOINT = "${aws_db_instance.steampulse_database.address}"
      DATABASE_PORT     = "5432",
      DASHBOARD_URL     = var.DASHBOARD_URL,
      DASHBOARD_IMAGE   = var.DASHBOARD_IMAGE,
      EMAIL_SENDER      = var.EMAIL_SENDER,
      EMAIL_RECEIVER    = var.EMAIL_RECEIVER,
      REPORT_FILE       = var.REPORT_FILE

    }
  }

}


resource "aws_iam_role" "steampulse_lambda_iam" {
  name = "steampulse_lambda_iam"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
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
}



resource "aws_iam_role" "steampulse_sfn_role" {
  name = "steampulse_sfn_role"

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
      },

      {
        Action = "sts:AssumeRole",
        Principal = {
          Service = "states.amazonaws.com"
        },
        Effect = "Allow",
        Sid    = ""
      },



    ]
  })

  inline_policy {
    name = "sfn-task-inline-policy"

    policy = jsonencode({
      Version = "2012-10-17",

      Statement = [
        {
          Action   = "ecs:DescribeTaskDefinition",
          Effect   = "Allow",
          Resource = "*",
          Condition = {
            "ArnLike" : {
              "ecs:cluster" : aws_ecs_cluster.steampulse_cluster.arn
            }
          }
        },
        {
          Action   = "ecs:DescribeTasks",
          Effect   = "Allow",
          Resource = "*",
          Condition = {
            "ArnLike" : {
              "ecs:cluster" : aws_ecs_cluster.steampulse_cluster.arn
            }
          }
        },
        {
          "Effect" : "Allow",
          "Action" : [
            "logs:CreateLogDelivery",
            "logs:CreateLogStream",
            "logs:GetLogDelivery",
            "logs:UpdateLogDelivery",
            "logs:DeleteLogDelivery",
            "logs:ListLogDeliveries",
            "logs:PutLogEvents",
            "logs:PutResourcePolicy",
            "logs:DescribeResourcePolicies",
            "logs:DescribeLogGroups",
            "logs:GetLogEvents",
            "logs:PutLogEvents",
            "logs:CreateLogStream",
            "logs:DescribeLogStreams",
            "logs:PutRetentionPolicy",
            "logs:CreateLogGroup"
          ],
          "Resource" : "*"
        },
        {
          Action   = "ecs:RunTask",
          Effect   = "Allow",
          Resource = "*",
          Condition = {
            "ArnLike" : {
              "ecs:cluster" : aws_ecs_cluster.steampulse_cluster.arn
            }
          }
        },
        {
          Action   = "iam:PassRole",
          Effect   = "Allow",
          Resource = "*"
        },
        {
          Action   = "lambda:InvokeFunction",
          Effect   = "Allow",
          Resource = "*"

        },
        {
          Action   = "states:StartExecution",
          Effect   = "Allow",
          Resource = "*"
        }
      ]
      }
    )
  }
}

resource "aws_cloudwatch_log_group" "steampulse_log_group_for_sfn" {
  name = "steampulse_sfn_log"
}



resource "aws_sfn_state_machine" "steampulse_state_machine" {
  name     = "steampulse_state_machine"
  role_arn = aws_iam_role.steampulse_sfn_role.arn

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.steampulse_log_group_for_sfn.arn}:*"
    include_execution_data = true
    level                  = "ERROR"
  }
  definition = <<EOF
  {
    "Comment" : "SteamPulse step function",
    "StartAt" : "ReviewGather",

    "States" : {
      "ReviewGather": {
      "Type": "Task",
      "Resource": "arn:aws:states:::ecs:runTask",
      "Parameters": {
        "LaunchType": "FARGATE",
        "Cluster": "${aws_ecs_cluster.steampulse_cluster.arn}",
        "TaskDefinition": "${aws_ecs_task_definition.steampulse_review_pipeline_task_definition.arn}",
        "NetworkConfiguration": {
          "AwsvpcConfiguration": {
            "SecurityGroups": [
              "${aws_security_group.steampulse_pipeline_ecs_sg.id}"
            ],
            "Subnets": [
              "subnet-03b1a3e1075174995",
              "subnet-0cec5bdb9586ed3c4",
              "subnet-0667517a2a13e2a6b"
            ]
          }
        }
        },
      "Next": "ReportEmail"
      },


      "ReportEmail" : {
        "Type" : "Task",
        "Resource" : "${aws_lambda_function.steampulse_email_lambda.arn}",
        "End" : true
      }
    }
  }
  EOF
}

# resource "aws_lb" "steampulse-load-balancer" {
#   name               = "steampulse-load-balancer"
#   internal           = false
#   load_balancer_type = "application"

#   subnets = ["subnet-03b1a3e1075174995", "subnet-0667517a2a13e2a6b", "subnet-0cec5bdb9586ed3c4"]
#   security_groups = [aws_security_group.steampulse_dashboard_sg.id]

#   tags = {
#     Environment = "production"
#   }
# }

# resource "aws_lb_target_group" "steampulse-lb-target-group" {
#   name        = "steampulse-lb-target-group"
#   port        = 80
#   protocol    = "HTTP"
#   target_type = "ip"
#   vpc_id      = "vpc-0e0f897ec7ddc230d"
# }




# resource "aws_eip" "steampulse_lb_elastic_ip" {
#   domain = "vpc"
# }