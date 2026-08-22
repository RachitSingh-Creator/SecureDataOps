# SecureDataOps Terraform migration scaffold

This directory starts an IaC migration for the existing `us-east-1`
SecureDataOps production environment. It contains import-ready resource blocks
for only the safest existing components: the backend and frontend ECR
repositories, backend ALB and target group, its listener, ECS cluster, and ECS
task execution role. Its production-safe S3 backend configuration has no
credentials, database connection string, or task-definition image tag.

The configuration uses AWS data sources for the existing VPC, subnets, backend
ALB/target group, ECS cluster, ECR repositories, and ECS execution role. The
RDS identifier is inventory only so no connection metadata is read into state.
Existing ECS service names,
target-tracking settings, CloudWatch dashboard source, and log group are kept
as inventory only. The current GitHub Actions pipelines remain responsible for
building, tagging, rendering, and deploying container images.

## Remote state: one-time manual bootstrap

The configuration uses an S3 backend at
`s3://securedataops-tfstate-011582457592-us-east-1/securedataops/production/terraform.tfstate`.
The bucket is intentionally **not** an `aws_s3_bucket` resource in this
configuration: it must exist before Terraform can initialize its backend.

The backend uses S3 native locking (`use_lockfile = true`), which is the
current replacement for DynamoDB locking. DynamoDB locking is not used because
it is deprecated. Native S3 lockfiles require Terraform 1.10 or later; the
configuration's version constraint was raised accordingly (and remains within
the previously supported Terraform 1.x range).

Bootstrap the following outside this Terraform directory, using a dedicated
administrator identity. These are the only AWS resources/actions required
before backend initialization; review the commands, account, and region before
running them. They are documentation only and have **not** been run by this
migration.

```powershell
$StateBucket = "securedataops-tfstate-011582457592-us-east-1"
$Region = "us-east-1"

# Create the bucket in us-east-1. Confirm the globally unique name is owned by
# the intended AWS account before continuing.
aws s3api create-bucket --bucket $StateBucket --region $Region

# Require version recovery, SSE-S3 encryption, account-only ownership, and no
# public access. The backend's encrypt=true also requests SSE-S3 for state and
# lock objects.
aws s3api put-bucket-versioning --bucket $StateBucket --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket $StateBucket --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-public-access-block --bucket $StateBucket --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-ownership-controls --bucket $StateBucket --ownership-controls 'Rules=[{ObjectOwnership=BucketOwnerEnforced}]'
```

Before initialization, grant the Terraform operator least-privilege access to
the bucket: `s3:ListBucket` on the bucket; `s3:GetObject` and `s3:PutObject` on
the state object; and `s3:GetObject`, `s3:PutObject`, and `s3:DeleteObject` on
the adjacent `terraform.tfstate.tflock` object. Do not grant deletion on the
state object. Also retain access to previous object versions for recovery.

### GitHub Actions validation access

Terraform validation is isolated in
`.github/workflows/terraform-validation.yml`; it does not run application
builds or deployments and it never runs `terraform apply`. It uses the same
GitHub OIDC authentication pattern as the existing deployment workflows, but
requires a **separate Terraform validation IAM role**. Do not reuse the
deployment role unless it is replaced with a role that has only the policy
below and an appropriately scoped OIDC trust relationship.

Before enabling a successful Terraform CI run, an AWS administrator must:

1. Create or update the dedicated role trust policy to allow this repository's
   GitHub Actions OIDC subject for the `main` branch (matching the workflow's
   trigger) to call `sts:AssumeRoleWithWebIdentity`.
2. Attach a policy that permits only the state-object/lock-object S3 actions
   listed above, plus read-only inventory actions: `ec2:DescribeVpcs`,
   `ec2:DescribeSubnets`, `ecr:DescribeRepositories`,
   `ecs:DescribeClusters`, `elasticloadbalancing:DescribeListeners`,
   `elasticloadbalancing:DescribeLoadBalancers`,
   `elasticloadbalancing:DescribeTargetGroups`, and `iam:GetRole`.
3. Set the non-secret GitHub Actions repository variables
   `TERRAFORM_AWS_ROLE_ARN` (the dedicated role ARN) and
   `TERRAFORM_BACKEND_LISTENER_ARN` (the already-verified listener ARN).

The workflow applies an inline session policy that further restricts the OIDC
session to precisely those S3 state/lock paths and inventory reads. It has no
AWS permissions to create, update, delete, import, or apply infrastructure.
It intentionally fails with setup guidance until both repository variables are
configured; no credentials are hard-coded in the workflow.

### One-time local-state migration

Perform this only after the bootstrap is complete and a backup of the current
local state is held securely. It migrates state metadata only; it does not
create, alter, import, or delete AWS infrastructure.

```powershell
# Run from infra/terraform with authenticated AWS credentials. Do not add
# credentials to backend.tf, tfvars, source control, or a plan file.
Copy-Item terraform.tfstate terraform.tfstate.pre-s3-migration-backup
terraform init -migrate-state
terraform state list
```

Accept the migration prompt only after confirming the destination bucket and
key shown by Terraform exactly match the backend above. Confirm the state
object has a current version in S3, retain the local backup outside source
control, and then run the normal plan workflow below. Do not use
`terraform init -reconfigure` for this first migration because it discards the
previous backend configuration instead of offering to copy state.

## Initial migration workflow

1. Install a compatible Terraform CLI and authenticate the AWS CLI/provider
   with read-only access to the existing environment.
2. Complete the one-time remote-state bootstrap and migration above. For later
   normal runs, authenticate to AWS and run `terraform init`, then
   `terraform fmt -check`.
3. Identify the listener without assuming its port or position, then set the
   verified ARN for this shell before running a plan:

   ```powershell
   aws elbv2 describe-listeners --load-balancer-arn arn:aws:elasticloadbalancing:us-east-1:011582457592:loadbalancer/app/securedataops-alb/a1b68a761929383a --region us-east-1 --query "Listeners[].{Arn:ListenerArn,Port:Port,Protocol:Protocol,DefaultActions:DefaultActions}" --output table
   $ListenerArn = "<verified listener ARN from the output>"
   ```

4. Run `terraform validate` and `terraform plan -var "backend_listener_arn=$ListenerArn"`.
   Before importing, the plan will propose creates; it is a review only and
   must never be applied.
5. Do **not** run `terraform apply`. The resource blocks describe objects that
   already exist and are protected with `prevent_destroy`.

## Manual import order

After confirming live AWS values with read-only credentials, import these
existing objects into the chosen state in this exact order. Run a normal
`terraform plan` after each command and proceed only when it shows no proposed
infrastructure changes.

```powershell
# 1. ECR repositories (repository name is the import ID)
terraform import aws_ecr_repository.backend securedataops-backend
terraform plan -var "backend_listener_arn=$ListenerArn"
terraform import aws_ecr_repository.frontend securedatops-frontend
terraform plan -var "backend_listener_arn=$ListenerArn"

# 2. Backend target group (its ARN is the import ID)
terraform import aws_lb_target_group.backend arn:aws:elasticloadbalancing:us-east-1:011582457592:targetgroup/securedataops-backend-tg/781ee1c7b999a392
terraform plan -var "backend_listener_arn=$ListenerArn"

# 3. Backend ALB (its ARN is the import ID)
terraform import aws_lb.backend arn:aws:elasticloadbalancing:us-east-1:011582457592:loadbalancer/app/securedataops-alb/a1b68a761929383a
terraform plan -var "backend_listener_arn=$ListenerArn"

# 4. Backend listener (use the verified $ListenerArn from the preceding inventory command)
terraform import aws_lb_listener.backend $ListenerArn
terraform plan -var "backend_listener_arn=$ListenerArn"

# 5. ECS cluster (cluster name is the import ID)
terraform import aws_ecs_cluster.securedataops securedataops-cluster1
terraform plan -var "backend_listener_arn=$ListenerArn"

# 6. ECS execution role (role name is the import ID)
terraform import aws_iam_role.ecs_execution ecsTaskExecutionRole
terraform plan -var "backend_listener_arn=$ListenerArn"
```

Do not automatically import any of these resources. The listener command is a
read-only lookup but must be reviewed for a single, intended listener before
the import. Do not import or manage ECS task definitions, ECS services, RDS,
VPC/networking, secrets, or CI/CD until their separate reconciliation is
complete.

## Inputs and state safety

The defaults identify known existing resources. Override non-secret inventory
values only through local `*.tfvars` files, which are ignored by Git. Never put
database passwords, API keys, secrets, or connection strings in Terraform
variables, source files, plans, or state. The S3 backend configuration contains
no credentials; obtain backend and provider credentials through an approved AWS
identity mechanism. State access, including the lockfile, must be restricted to
trusted Terraform operators. CI/CD integration remains a deliberate later
migration step.
