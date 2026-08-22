output "environment" {
  description = "Inventory environment label."
  value       = var.environment
}

output "vpc_id" {
  description = "Existing SecureDataOps VPC ID."
  value       = data.aws_vpc.securedataops.id
}

output "subnet_ids" {
  description = "Subnet IDs currently discovered in the existing VPC."
  value       = sort(data.aws_subnets.securedataops.ids)
}

output "backend_alb" {
  description = "Existing backend ALB inventory."
  value = {
    arn      = data.aws_lb.backend.arn
    dns_name = data.aws_lb.backend.dns_name
    name     = data.aws_lb.backend.name
  }
}

output "backend_target_group" {
  description = "Existing backend target group inventory."
  value = {
    arn          = data.aws_lb_target_group.backend.arn
    health_check = data.aws_lb_target_group.backend.health_check
    port         = data.aws_lb_target_group.backend.port
    protocol     = data.aws_lb_target_group.backend.protocol
  }
}

output "ecs_cluster_arn" {
  description = "Existing ECS cluster ARN."
  value       = data.aws_ecs_cluster.securedataops.arn
}

output "ecs_service_names" {
  description = "Existing ECS services retained as inventory only."
  value       = local.existing_ecs_services
}

output "ecr_repository_urls" {
  description = "Existing ECR repository URLs; image tags remain CI/CD-owned."
  value = {
    backend  = data.aws_ecr_repository.backend.repository_url
    frontend = data.aws_ecr_repository.frontend.repository_url
  }
}

output "rds_instance_identifier" {
  description = "Existing RDS instance identifier retained as inventory only."
  value       = var.db_instance_identifier
}

output "ecs_execution_role_arn" {
  description = "Existing ECS task execution role ARN."
  value       = data.aws_iam_role.ecs_execution.arn
}

output "backend_autoscaling_inventory" {
  description = "Existing backend target-tracking policy settings retained as inventory."
  value       = local.existing_backend_autoscaling
}

output "sre_configuration_inventory" {
  description = "Existing SRE configuration locations retained as inventory."
  value       = local.existing_sre_configuration
}
