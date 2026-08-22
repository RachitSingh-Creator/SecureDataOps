# The data sources below are used to mirror the existing environment while the
# matching resource blocks are prepared for a manual import. They do not alter
# AWS infrastructure.

data "aws_vpc" "securedataops" {
  id = var.vpc_id
}

data "aws_subnets" "securedataops" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.securedataops.id]
  }
}

data "aws_lb" "backend" {
  name = var.backend_alb_name
}

data "aws_lb_target_group" "backend" {
  name = var.backend_target_group_name
}

# The listener ARN is intentionally a required input. Do not select a listener
# by assumed port or list position; obtain and verify it with read-only AWS CLI
# inventory before planning or importing.
data "aws_lb_listener" "backend" {
  arn = var.backend_listener_arn
}

data "aws_ecs_cluster" "securedataops" {
  cluster_name = var.ecs_cluster_name
}

data "aws_ecr_repository" "backend" {
  name = var.backend_ecr_repository_name
}

data "aws_ecr_repository" "frontend" {
  name = var.frontend_ecr_repository_name
}

data "aws_iam_role" "ecs_execution" {
  name = var.ecs_execution_role_name
}

data "aws_lb_target_group" "frontend" {
  name = "securedataops-frontend-tg"
}
