# Backup/DR guardrails are read-only. The RDS instance remains outside
# Terraform resource management; these checks only prevent a plan from silently
# accepting an environment that lacks the minimum recovery baseline.
data "aws_db_instance" "securedataops" {
  db_instance_identifier = var.db_instance_identifier
}

check "rds_backup_recovery_baseline" {
  assert {
    condition     = data.aws_db_instance.securedataops.backup_retention_period >= var.rds_minimum_backup_retention_days
    error_message = "RDS automated backup retention must be at least ${var.rds_minimum_backup_retention_days} days."
  }

  assert {
    condition     = data.aws_db_instance.securedataops.preferred_backup_window != ""
    error_message = "RDS must have a configured automated backup window."
  }

  assert {
    condition     = data.aws_db_instance.securedataops.storage_encrypted
    error_message = "RDS storage encryption is required for recoverable production backups."
  }

  assert {
    condition     = data.aws_db_instance.securedataops.multi_az
    error_message = "The production RDS instance must remain Multi-AZ for availability recovery."
  }
}
