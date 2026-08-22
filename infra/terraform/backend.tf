# This backend bucket is deliberately bootstrapped outside this configuration.
# Do not add aws_s3_bucket resources here: Terraform must initialize this
# backend before it can manage any resources. See README.md for the one-time,
# manual bootstrap and local-state migration procedure.
terraform {
  backend "s3" {
    bucket       = "securedataops-tfstate-011582457592-us-east-1"
    key          = "securedataops/production/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
