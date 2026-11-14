# ============================================================
# Terraform = Infrastructure as Code (IaC)
#
# This file tells AWS:
# "Create the infrastructure needed to run my Agentic AI app."
#
# Overall:
#
# Terraform
#    |
#    +--> VPC / Subnets
#    +--> ECS Cluster
#    +--> ECS Task (our Docker container)
#    +--> IAM permissions
#    +--> Security Group
#    +--> ECS Service
#    |
#    +--> Run Agent API on AWS Fargate
# ============================================================


terraform {
  # Tell Terraform which AWS provider to use.
  # "~> 5.0" means use a compatible 5.x version.
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}


# AWS region where everything will be created.
provider "aws" {
  region = "ap-south-1"
}


# ------------------------------------------------------------
# EXISTING NETWORK
# ------------------------------------------------------------

# Find the existing DEFAULT VPC.
# We are not creating a new VPC here.
data "aws_vpc" "default" {
  default = true
}


# Find all subnets belonging to that VPC.
# ECS will use these subnets to run our container.
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}


# ------------------------------------------------------------
# ECS CLUSTER
# ------------------------------------------------------------

# ECS Cluster = logical home for our containers.
#
# Think:
# ECS Cluster
#    |
#    +--> Agentic AI container
#
resource "aws_ecs_cluster" "this" {
  name = "agentic-project1-cluster"
}


# ------------------------------------------------------------
# ECS TASK DEFINITION
# ------------------------------------------------------------

# Task Definition = blueprint for how our container should run.
#
# It defines:
# - Which Docker image?
# - How much CPU/memory?
# - Which port?
# - Which secrets?
#
resource "aws_ecs_task_definition" "this" {

  family = "agentic-project1"

  # Fargate means AWS manages the underlying servers.
  requires_compatibilities = ["FARGATE"]

  # Each task gets its own network interface/IP.
  network_mode = "awsvpc"

  # Small demo workload:
  # 0.25 vCPU + 512 MB RAM
  cpu    = "256"
  memory = "512"

  # IAM role ECS uses to start the container
  # and access required AWS resources.
  execution_role_arn = aws_iam_role.execution.arn


  # Container configuration.
  #
  # Docker image:
  # ECR --> Docker image --> ECS/Fargate
  #
  container_definitions = jsonencode([{
    name = "agent"

    image = "<your_account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-project1:latest"

    # Our FastAPI application listens on port 8000.
    portMappings = [{
      containerPort = 8000
    }]

    # Get ANTHROPIC_API_KEY from AWS Secrets Manager.
    #
    # IMPORTANT:
    # API key is NOT hardcoded into the Docker image.
    secrets = [{
      name      = "ANTHROPIC_API_KEY"
      valueFrom = "arn:aws:secretsmanager:ap-south-1:<your_account_id>:secret:agentic-project1/anthropic-key"
    }]
  }])
}


# ------------------------------------------------------------
# IAM ROLE
# ------------------------------------------------------------

# IAM Role = permissions/identity given to ECS.
#
# This allows ECS tasks to assume this role.
resource "aws_iam_role" "execution" {

  name = "agentic-project1-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"

      # ECS Tasks are allowed to use this role.
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}


# Give ECS the standard permissions required
# to pull the image and start the container.
resource "aws_iam_role_policy_attachment" "execution" {

  role = aws_iam_role.execution.name

  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}


# Give the ECS execution role permission to access
# Secrets Manager.
#
# This allows the container to retrieve ANTHROPIC_API_KEY.
resource "aws_iam_role_policy_attachment" "secrets" {

  role = aws_iam_role.execution.name

  policy_arn = "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
}


# ------------------------------------------------------------
# SECURITY GROUP
# ------------------------------------------------------------

# Security Group = firewall for our ECS task.
resource "aws_security_group" "service" {

  name   = "agentic-project1-sg"
  vpc_id = data.aws_vpc.default.id


  # Allow incoming HTTP/TCP traffic on port 8000.
  #
  # 0.0.0.0/0 = from anywhere on the internet.
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }


  # Allow the container to make outbound connections.
  #
  # Required for things like:
  # ECS -> Anthropic API
  # ECS -> Secrets Manager
  # ECS -> External APIs
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}


# ------------------------------------------------------------
# ECS SERVICE
# ------------------------------------------------------------

# ECS Service = keeps our application running.
#
# desired_count = 1
# means:
#
#       ECS
#        |
#        +--> Keep 1 Agent container running
#
resource "aws_ecs_service" "this" {

  name = "agentic-project1-service"

  # Run the service inside our ECS cluster.
  cluster = aws_ecs_cluster.this.id

  # Use the task definition/blueprint above.
  task_definition = aws_ecs_task_definition.this.arn

  # Keep one container running.
  desired_count = 1

  # AWS manages the servers using Fargate.
  launch_type = "FARGATE"


  # Network configuration for the container.
  network_configuration {

    # Run the task inside these subnets.
    subnets = data.aws_subnets.default.ids

    # Apply our firewall rules.
    security_groups = [aws_security_group.service.id]

    # Give the task a public IP.
    # This allows it to communicate with the internet.
    assign_public_ip = true
  }
}


# ------------------------------------------------------------
# OUTPUT
# ------------------------------------------------------------

# After "terraform apply", print the ECS cluster name.
output "cluster_name" {
  value = aws_ecs_cluster.this.name
}


# ============================================================
# BIG PICTURE
#
# Docker Image
#      |
#      v
#     ECR
#      |
#      v
# ECS Fargate
#      |
#      +--> FastAPI container :8000
#      |
#      +--> Secrets Manager --> ANTHROPIC_API_KEY
#      |
#      +--> Internet --> Anthropic API
#
# Terraform creates and connects all these AWS components.
# ============================================================