variable "aws_region" {
  description = "AWS region containing the existing SecureDataOps environment."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Existing deployment environment label used only for inventory context."
  type        = string
  default     = "production"
}

variable "vpc_id" {
  description = "Existing SecureDataOps VPC ID."
  type        = string
  default     = "vpc-063c99ce2adca4c70"
}

variable "backend_alb_name" {
  description = "Existing internet-facing backend Application Load Balancer name."
  type        = string
  default     = "securedataops-alb"
}

variable "backend_target_group_name" {
  description = "Existing backend target group name."
  type        = string
  default     = "securedataops-backend-tg"
}

variable "backend_listener_arn" {
  description = "Verified ARN of the existing listener on the backend ALB; intentionally has no default."
  type        = string
}

variable "ecs_cluster_name" {
  description = "Existing ECS Fargate cluster name."
  type        = string
  default     = "securedataops-cluster1"
}

variable "backend_service_name" {
  description = "Existing ECS backend service name; retained as inventory, not managed here."
  type        = string
  default     = "securedataops-backend-service"
}

variable "frontend_service_name" {
  description = "Existing ECS frontend service name; retained as inventory, not managed here."
  type        = string
  default     = "securedataops-frontend-service"
}

variable "backend_ecr_repository_name" {
  description = "Existing backend ECR repository name."
  type        = string
  default     = "securedataops-backend"
}

variable "frontend_ecr_repository_name" {
  description = "Existing frontend ECR repository name."
  type        = string
  default     = "securedatops-frontend"
}

variable "db_instance_identifier" {
  description = "Existing encrypted Multi-AZ PostgreSQL RDS instance identifier."
  type        = string
  default     = "securedataops-db"
}

variable "rds_minimum_backup_retention_days" {
  description = "Minimum automated RDS backup retention required by the production DR baseline."
  type        = number
  default     = 7

  validation {
    condition     = var.rds_minimum_backup_retention_days >= 1 && var.rds_minimum_backup_retention_days <= 35
    error_message = "RDS automated backup retention must be between 1 and 35 days."
  }
}

variable "ecs_execution_role_name" {
  description = "Existing ECS task execution IAM role name."
  type        = string
  default     = "ecsTaskExecutionRole"
}

variable "backend_log_group_name" {
  description = "Existing CloudWatch Logs group used by the backend task."
  type        = string
  default     = "/ecs/securedataops-backend"
}
