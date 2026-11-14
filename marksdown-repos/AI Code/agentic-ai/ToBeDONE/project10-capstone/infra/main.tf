terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}

provider "aws" {
  region = var.region
}

data "aws_caller_identity" "current" {}
data "aws_vpc" "default" { default = true }

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# Created once by hand (see README). Terraform only reads them, so secret values never enter the state.
data "aws_secretsmanager_secret" "anthropic" { name = "${var.name}/anthropic-key" }
data "aws_secretsmanager_secret" "api_keys" { name = "${var.name}/api-keys" }

locals {
  https = var.certificate_arn != ""
}

# ---------- Image repository ----------
resource "aws_ecr_repository" "this" {
  name                 = var.name
  image_tag_mutability = "IMMUTABLE" # a tag can never be overwritten, so a tag always means the same code
  force_delete         = true        # lets terraform destroy remove it in a learning stack; remove for production

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_lifecycle_policy" "this" {
  repository = aws_ecr_repository.this.name
  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep the last 20 images"
      selection    = { tagStatus = "any", countType = "imageCountMoreThan", countNumber = 20 }
      action       = { type = "expire" }
    }]
  })
}

# ---------- Logs ----------
resource "aws_cloudwatch_log_group" "this" {
  name              = "/ecs/${var.name}"
  retention_in_days = var.log_retention_days
}

# ---------- IAM: the container can read exactly these two secrets ----------
resource "aws_iam_role" "execution" {
  name = "${var.name}-exec-role"
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
  name = "read-${var.name}-secrets"
  role = aws_iam_role.execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["secretsmanager:GetSecretValue"]
      Resource = [data.aws_secretsmanager_secret.anthropic.arn, data.aws_secretsmanager_secret.api_keys.arn]
    }]
  })
}

# ---------- Network ----------
resource "aws_security_group" "alb" {
  name   = "${var.name}-alb-sg"
  vpc_id = data.aws_vpc.default.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  dynamic "ingress" {
    for_each = local.https ? [1] : []
    content {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "service" {
  name   = "${var.name}-service-sg"
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

# ---------- Persistent storage for the database: EFS ----------
resource "aws_security_group" "efs" {
  name   = "${var.name}-efs-sg"
  vpc_id = data.aws_vpc.default.id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.service.id]
  }
}

resource "aws_efs_file_system" "data" {
  encrypted = true
  tags      = { Name = var.name }
}

resource "aws_efs_mount_target" "data" {
  for_each        = toset(data.aws_subnets.default.ids)
  file_system_id  = aws_efs_file_system.data.id
  subnet_id       = each.value
  security_groups = [aws_security_group.efs.id]
}

# The access point makes every file belong to user 10001, the user the container runs as.
resource "aws_efs_access_point" "data" {
  file_system_id = aws_efs_file_system.data.id

  posix_user {
    uid = 10001
    gid = 10001
  }

  root_directory {
    path = "/platform"
    creation_info {
      owner_uid   = 10001
      owner_gid   = 10001
      permissions = "750"
    }
  }
}

# ---------- Load balancer ----------
resource "aws_lb" "this" {
  name                       = "${var.name}-alb"
  load_balancer_type         = "application"
  subnets                    = data.aws_subnets.default.ids
  security_groups            = [aws_security_group.alb.id]
  idle_timeout               = 120 # a chat can include several model calls
  drop_invalid_header_fields = true
}

resource "aws_lb_target_group" "this" {
  name        = "${var.name}-tg"
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
    type             = local.https ? "redirect" : "forward"
    target_group_arn = local.https ? null : aws_lb_target_group.this.arn

    dynamic "redirect" {
      for_each = local.https ? [1] : []
      content {
        port        = "443"
        protocol    = "HTTPS"
        status_code = "HTTP_301"
      }
    }
  }
}

resource "aws_lb_listener" "https" {
  count             = local.https ? 1 : 0
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.this.arn
  }
}

# ---------- ECS ----------
resource "aws_ecs_cluster" "this" {
  name = "${var.name}-cluster"
}

resource "aws_ecs_task_definition" "this" {
  family                   = var.name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.execution.arn

  volume {
    name = "data"
    efs_volume_configuration {
      file_system_id     = aws_efs_file_system.data.id
      transit_encryption = "ENABLED"
      authorization_config {
        access_point_id = aws_efs_access_point.data.id
        iam             = "DISABLED"
      }
    }
  }

  container_definitions = jsonencode([{
    name         = "agent"
    image        = "${aws_ecr_repository.this.repository_url}:${var.image_tag}"
    essential    = true
    portMappings = [{ containerPort = 8000 }]
    mountPoints  = [{ sourceVolume = "data", containerPath = "/data", readOnly = false }]
    environment = [
      { name = "DB_PATH", value = "/data/platform.db" },
      { name = "MODEL", value = var.model },
      { name = "LOG_LEVEL", value = "INFO" },
    ]
    secrets = [
      { name = "ANTHROPIC_API_KEY", valueFrom = data.aws_secretsmanager_secret.anthropic.arn },
      { name = "API_KEYS_JSON", valueFrom = data.aws_secretsmanager_secret.api_keys.arn },
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        awslogs-group         = aws_cloudwatch_log_group.this.name
        awslogs-region        = var.region
        awslogs-stream-prefix = "agent"
      }
    }
  }])
}

resource "aws_ecs_service" "this" {
  name                              = "${var.name}-service"
  cluster                           = aws_ecs_cluster.this.id
  task_definition                   = aws_ecs_task_definition.this.arn
  desired_count                     = 1 # SQLite allows one writer: do not raise this before changing the store
  launch_type                       = "FARGATE"
  health_check_grace_period_seconds = 60

  # Stop the old task before starting the new one, so two tasks never write to the same database file.
  # The price is a short gap during each deployment.
  deployment_minimum_healthy_percent = 0
  deployment_maximum_percent         = 100

  # If the new version never becomes healthy, ECS puts the previous version back by itself.
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.service.id]
    assign_public_ip = true # the default VPC has no NAT gateway; needed to pull the image and reach the API
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.this.arn
    container_name   = "agent"
    container_port   = 8000
  }

  depends_on = [aws_lb_listener.http, aws_lb_listener.https, aws_efs_mount_target.data]
}

# ---------- Alarms ----------
resource "aws_sns_topic" "alerts" {
  name = "${var.name}-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alarm_email == "" ? 0 : 1
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

resource "aws_cloudwatch_metric_alarm" "errors_5xx" {
  alarm_name          = "${var.name}-5xx"
  alarm_description   = "The service returned server errors. Check the logs for level=ERROR."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "HTTPCode_Target_5XX_Count"
  dimensions          = { LoadBalancer = aws_lb.this.arn_suffix }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 5
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "unhealthy" {
  alarm_name          = "${var.name}-unhealthy-target"
  alarm_description   = "The load balancer sees no healthy container."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  dimensions          = { LoadBalancer = aws_lb.this.arn_suffix, TargetGroup = aws_lb_target_group.this.arn_suffix }
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 3
  threshold           = 0
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "cpu" {
  alarm_name          = "${var.name}-cpu"
  alarm_description   = "CPU has been high for 15 minutes."
  namespace           = "AWS/ECS"
  metric_name         = "CPUUtilization"
  dimensions          = { ClusterName = aws_ecs_cluster.this.name, ServiceName = aws_ecs_service.this.name }
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  threshold           = 80
  comparison_operator = "GreaterThanThreshold"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

# The application writes one JSON line per event. These filters turn chosen events into metrics.
resource "aws_cloudwatch_log_metric_filter" "guardrail" {
  name           = "${var.name}-guardrail-events"
  log_group_name = aws_cloudwatch_log_group.this.name
  pattern        = "{ $.event = \"guardrail\" }"

  metric_transformation {
    name      = "GuardrailEvents"
    namespace = "AgentPlatform"
    value     = "1"
  }
}

resource "aws_cloudwatch_log_metric_filter" "auth_failed" {
  name           = "${var.name}-auth-failures"
  log_group_name = aws_cloudwatch_log_group.this.name
  pattern        = "{ $.event = \"auth_failed\" }"

  metric_transformation {
    name      = "AuthFailures"
    namespace = "AgentPlatform"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "guardrail" {
  alarm_name          = "${var.name}-guardrail-spike"
  alarm_description   = "Many guardrail events in 5 minutes: possible attack or a prompt that misbehaves."
  namespace           = "AgentPlatform"
  metric_name         = "GuardrailEvents"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 20
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

resource "aws_cloudwatch_metric_alarm" "auth_failed" {
  alarm_name          = "${var.name}-auth-failures"
  alarm_description   = "Many failed logins in 5 minutes: someone may be guessing keys."
  namespace           = "AgentPlatform"
  metric_name         = "AuthFailures"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 20
  comparison_operator = "GreaterThanThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

# ---------- Outputs ----------
output "app_url" {
  value = "${local.https ? "https" : "http"}://${aws_lb.this.dns_name}"
}

output "ecr_repository_url" {
  value = aws_ecr_repository.this.repository_url
}

output "log_group" {
  value = aws_cloudwatch_log_group.this.name
}
