# SecureDataOps Terraform migration scaffold

This directory starts an IaC migration for the existing `us-east-1`
SecureDataOps production environment. It contains import-ready resource blocks
for only the safest existing components: the backend and frontend ECR
repositories, backend ALB and target group, its listener, ECS cluster, and ECS
task execution role. It has no remote state backend, credentials, database
connection string, or task-definition image tag.

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
variables, source files, plans, or state. A remote encrypted state backend,
state locking, IAM permissions, and CI/CD integration are deliberate later
migration steps, not part of this scaffold.
