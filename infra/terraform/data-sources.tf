# This initial migration reads existing infrastructure only. It intentionally
# contains no resources, task definitions, secrets, or remote-state backend.

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
