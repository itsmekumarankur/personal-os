terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = "ap-south-1"
}

data "aws_caller_identity" "current" {}

data "aws_vpc" "default" { default = true }

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_secretsmanager_secret" "anthropic" { name = "agentic-evals-tracing/anthropic-key" }

locals {
  image = "${data.aws_caller_identity.current.account_id}.dkr.ecr.ap-south-1.amazonaws.com/agentic-evals-tracing:latest"
}

# ---------- Logs ----------
resource "aws_cloudwatch_log_group" "this" {
  name              = "/ecs/agentic-evals-tracing"
  retention_in_days = 7
}

# ---------- IAM: execution role, read only this secret ----------
resource "aws_iam_role" "execution" {
  name = "agentic-evals-tracing-exec-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "execution" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "read_secrets" {
  name = "read-agentic-evals-tracing-secret"
  role = aws_iam_role.execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [data.aws_secretsmanager_secret.anthropic.arn]
    }]
  })
}

# ---------- Security groups ----------
resource "aws_security_group" "alb" {
  name   = "agentic-evals-tracing-alb-sg"
  vpc_id = data.aws_vpc.default.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "service" {
  name   = "agentic-evals-tracing-service-sg"
  vpc_id = data.aws_vpc.default.id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id] # only the load balancer can reach the container
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ---------- Load balancer ----------
resource "aws_lb" "this" {
  name               = "agentic-evals-tracing-alb"
  load_balancer_type = "application"
  subnets            = data.aws_subnets.default.ids
  security_groups    = [aws_security_group.alb.id]
  idle_timeout       = 60
}

resource "aws_lb_target_group" "this" {
  name        = "agentic-evals-tracing-tg"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = data.aws_vpc.default.id

  health_check {
    path     = "/health"
    interval = 30
    timeout  = 10
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

# ---------- ECS ----------
resource "aws_ecs_cluster" "this" {
  name = "agentic-evals-tracing-cluster"
}

resource "aws_ecs_task_definition" "this" {
  family                   = "agentic-evals-tracing"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.execution.arn

  container_definitions = jsonencode([{
    name         = "agent"
    image        = local.image
    essential    = true
    portMappings = [{ containerPort = 8000 }]
    command      = ["uvicorn", "main:app_factory", "--factory", "--host", "0.0.0.0", "--port", "8000"]
    environment = [
      { name = "TRACE_CONTENT", value = "truncate" },
      { name = "TRACE_SAMPLE_RATE", value = "1.0" }
    ]
    secrets = [
      { name = "ANTHROPIC_API_KEY", valueFrom = data.aws_secretsmanager_secret.anthropic.arn }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.this.name
        awslogs-region        = "ap-south-1"
        awslogs-stream-prefix = "agent"
      }
    }
  }])
}

resource "aws_ecs_service" "this" {
  name                              = "agentic-evals-tracing-service"
  cluster                           = aws_ecs_cluster.this.id
  task_definition                   = aws_ecs_task_definition.this.arn
  desired_count                     = 1
  launch_type                       = "FARGATE"
  health_check_grace_period_seconds = 60

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.service.id]
    assign_public_ip = true # default VPC has no NAT; needed to pull the image and reach the API
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = "agent"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.http]
}

output "app_url" {
  value = "http://${aws_lb.this.dns_name}"
}
