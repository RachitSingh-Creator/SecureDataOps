# SecureDataOps Terraform migration scaffold

This directory starts an IaC migration for the existing `us-east-1`
SecureDataOps production environment. It is intentionally **read-only**:
there are no `resource` blocks, no remote state backend, no credentials, no
database connection string, and no task-definition image tag managed here.

The configuration uses AWS data sources for the existing VPC, subnets, backend
ALB/target group, ECS cluster, ECR repositories, and ECS execution role. The
RDS identifier is inventory only so no connection metadata is read into state.
Existing ECS service names,
target-tracking settings, CloudWatch dashboard source, and log group are kept
as inventory only. The current GitHub Actions pipelines remain responsible for
building, tagging, rendering, and deploying container images.

## Initial migration workflow

1. Install a compatible Terraform CLI and authenticate the AWS CLI/provider
   with read-only access to the existing environment.
2. From this directory, run `terraform init` and then `terraform fmt -check`.
3. Run `terraform validate` and a read-only review with
   `terraform plan -refresh-only`. Confirm that the discovered VPC includes
   the expected four existing subnets and that all data-source identities
   match the environment.
4. Do **not** run `terraform apply` in this initial phase. Data sources do not
   require import and this scaffold must not create, replace, or alter AWS
   resources.

## Managing existing resources later

When a future change adds a matching Terraform `resource` block for an
already-existing AWS object, import that object into the chosen remote state
**before any normal plan or apply**:

```powershell
terraform import <resource-address> <existing-aws-id>
terraform plan
```

Review the plan for zero unintended replacements or changes before approving
an apply. Import one resource class at a time, starting with non-disruptive
inventory such as ECR or CloudWatch configuration. Do not import or manage an
ECS task definition until the CI/CD image-tag ownership and deployment flow
have been deliberately migrated.

## Inputs and state safety

The defaults identify known existing resources. Override non-secret inventory
values only through local `*.tfvars` files, which are ignored by Git. Never put
database passwords, API keys, secrets, or connection strings in Terraform
variables, source files, plans, or state. A remote encrypted state backend,
state locking, IAM permissions, and CI/CD integration are deliberate later
migration steps, not part of this scaffold.
