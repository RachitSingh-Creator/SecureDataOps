# SecureDataOps

> A production-oriented DevOps, SRE, and DevSecOps platform demonstrating how a containerized full-stack application can be deployed, secured, monitored, scaled, and recovered on AWS.

<!--
MAIN PROJECT SCREENSHOT

Place your clean application screenshot here.

Recommended:
docs/images/application-dashboard.png

Use dummy users/data in the public screenshot.
Do not expose real emails, phone numbers, UUIDs, credentials, tokens, or other personal information.
-->

---

## Overview

SecureDataOps is a full-stack cloud application built to demonstrate the complete lifecycle of operating a production-oriented workload on AWS.

The project is intentionally designed beyond the basic:

```text
Docker → AWS → Application Running
````

Instead, it covers:

```text
Application Development
        ↓
GitHub
        ↓
CI/CD
        ↓
Security Validation
        ↓
Docker
        ↓
Amazon ECR
        ↓
Amazon ECS Fargate
        ↓
Application Load Balancer
        ↓
PostgreSQL / Amazon RDS
        ↓
Monitoring
        ↓
Alerting
        ↓
Auto Scaling
        ↓
Backup & Disaster Recovery
        ↓
Incident Management
        ↓
Privacy / DPDP Controls
```

The project demonstrates practical concepts from:

* DevOps
* SRE
* DevSecOps
* AWS Cloud
* Infrastructure as Code
* CI/CD
* Containerization
* Observability
* Auto Scaling
* Backup & Disaster Recovery
* Application Security
* IAM
* Privacy engineering
* Incident management

---

# Why SecureDataOps?

A production application is not complete simply because it can be deployed.

Once an application is running, engineers must answer questions such as:

* How is the infrastructure managed?
* How does code reach production?
* How are AWS credentials protected?
* How are containers deployed?
* How does traffic reach the application?
* How are frontend and backend services separated?
* How does the backend reach the database?
* What happens when a task becomes unhealthy?
* What happens when traffic increases?
* How are failures detected?
* How are engineers notified?
* How is personal data protected?
* How is database recovery handled?
* How is Terraform state protected?
* How are dependency vulnerabilities detected?
* How are incidents handled?

SecureDataOps was built to answer these questions through an actual deployed system.

---

# Project Goals

The primary goals of the project are:

1. Deploy a real full-stack application on AWS.
2. Use Docker for reproducible application environments.
3. Use ECS Fargate instead of manually managed servers.
4. Use Application Load Balancers for traffic routing.
5. Use Amazon RDS PostgreSQL for persistent storage.
6. Manage infrastructure using Terraform.
7. Implement CI/CD using GitHub Actions.
8. Use GitHub OIDC instead of relying on long-lived AWS credentials.
9. Implement dependency security scanning.
10. Implement application authentication and authorization.
11. Implement CloudWatch monitoring and SNS notifications.
12. Implement ECS request-based auto scaling.
13. Establish backup and disaster-recovery controls.
14. Implement DPDP-oriented privacy controls.
15. Document incident response and operational procedures.

---

# High-Level Architecture

<!--
ARCHITECTURE DIAGRAM

Place:
docs/images/architecture-overview.png
-->

```text
                              INTERNET
                                  |
                 +----------------+----------------+
                 |                                 |
                 v                                 v
       +---------------------+           +---------------------+
       |    Frontend ALB     |           |     Backend ALB     |
       |   Internet-facing   |           |   Internet-facing   |
       +----------+----------+           +----------+----------+
                  |                                 |
                  |                                 |
                  v                                 v
       +---------------------+           +---------------------+
       |   Frontend ECS      |           |    Backend ECS      |
       |     Fargate        |           |      Fargate        |
       |      Service       |           |       Service       |
       +---------------------+           +----------+----------+
                                                    |
                                                    |
                                                    v
                                          +---------------------+
                                          |    PostgreSQL RDS   |
                                          +----------+----------+
                                                     |
                                                     v
                                          +---------------------+
                                          | Automated Backups   |
                                          | & Point-in-Time     |
                                          | Recovery            |
                                          +---------------------+


                AWS VPC / NETWORKING LAYER
                ============================

        Subnets
        Security Groups
        Routing
        Availability Zones


                OBSERVABILITY
                =============

        ECS / ALB / Application
                  |
                  v
             CloudWatch
                  |
             +----+----+
             |         |
           Logs      Alarms
                       |
                       v
                      SNS


                CI/CD
                =====

        Developer
             |
             v
          GitHub
             |
             v
       GitHub Actions
             |
       +-----+----------------+
       |                      |
       v                      v
    Security              Terraform
    Testing               Validation
       |                      |
       +----------+-----------+
                  |
                  v
              Docker Build
                  |
                  v
                 ECR
                  |
                  v
                ECS


                TERRAFORM STATE
                ===============

              Terraform
                  |
                  v
              S3 Bucket
                  |
       +----------+----------+
       |                     |
   Encryption            Versioning
                             |
                             v
                   Noncurrent versions
                       retained 365 days
```

---

# AWS Network Architecture

Networking is one of the most important parts of SecureDataOps.

The application runs within an AWS VPC environment.

The VPC provides the logical network boundary for the AWS workload.

The networking architecture consists of:

* VPC
* Subnets
* Availability Zones
* Route configuration
* Security Groups
* Internet-facing Application Load Balancers
* ECS services
* RDS PostgreSQL

The Terraform configuration references the existing production VPC and subnet environment rather than pretending that the VPC itself is recreated every time the application is deployed.

---

## VPC

The VPC provides the primary network boundary for the application.

```text
AWS Account
    |
    v
   VPC
    |
    +----------------------+
    |                      |
    v                      v
 Subnet Group          Subnet Group
    |                      |
    v                      v
   ALB                    ECS/RDS
```

The VPC allows the different application components to communicate through controlled private networking while exposing only the required public entry points.

---

## Subnets

The architecture separates infrastructure according to its role.

Conceptually:

```text
VPC
 |
 +-------------------------------+
 |                               |
 |        Public Layer            |
 |                               |
 |     Frontend ALB               |
 |     Backend ALB                |
 |                               |
 +-------------------------------+
 |
 +-------------------------------+
 |                               |
 |       Application Layer        |
 |                               |
 |     Frontend ECS               |
 |     Backend ECS                |
 |                               |
 +-------------------------------+
 |
 +-------------------------------+
 |                               |
 |        Data Layer              |
 |                               |
 |     PostgreSQL RDS             |
 |                               |
 +-------------------------------+
```

The exact subnet and network configuration is managed/referenced through the AWS environment and Terraform configuration.

---

# Security Groups and Network Access

Security Groups act as stateful network access controls.

The intended communication model is:

```text
Internet
   |
   v
Frontend ALB
   |
   v
Frontend ECS


Internet
   |
   v
Backend ALB
   |
   v
Backend ECS
   |
   v
PostgreSQL RDS
```

The database should not be treated as a public application endpoint.

The desired security relationship is:

```text
ALB
 |
 | allowed application traffic
 v
ECS
 |
 | allowed database traffic
 v
RDS
```

This creates a layered network model instead of allowing unrestricted communication between components.

---

# Availability Zones

AWS resources are designed around availability-zone-aware infrastructure.

The architecture separates the network into multiple subnets/AZs where applicable so that a single infrastructure location does not become the only point of failure.

RDS Multi-AZ is also enabled as part of the database availability configuration.

---

# Application Architecture

SecureDataOps consists of two main application services.

```text
                    SecureDataOps
                         |
              +----------+----------+
              |                     |
              v                     v
         Frontend Service      Backend Service
              |                     |
              v                     v
          React/Vite              FastAPI
                                    |
                                    v
                               PostgreSQL
```

---

# Frontend

The frontend is implemented using React/Vite.

Responsibilities include:

* application dashboard
* displaying users
* creating users
* editing users
* deleting users
* interacting with backend APIs

The frontend is packaged into a Docker image and deployed as an ECS Fargate service.

---

# Backend

The backend is implemented using FastAPI.

Responsibilities include:

* REST API
* user management
* database operations
* health checks
* authentication
* authorization
* privacy operations
* audit events
* request IDs
* application error handling

The backend runs inside an ECS Fargate service.

---

# Database

The application uses PostgreSQL hosted by Amazon RDS.

The application stores user-related data including:

* UUID
* name
* email
* optional phone
* creation timestamp
* update timestamp

The database is treated as a critical stateful component.

Therefore the architecture includes:

* encryption
* automated backups
* point-in-time recovery
* Multi-AZ
* recovery procedures

---

# Complete Request Flow

A normal backend request follows this path:

```text
User
 |
 v
Backend ALB
 |
 v
ALB Listener :80
 |
 v
Backend Target Group
 |
 v
Backend ECS Task
 |
 v
FastAPI
 |
 v
PostgreSQL RDS
 |
 v
FastAPI Response
 |
 v
Backend ALB
 |
 v
User
```

The frontend follows a separate path:

```text
User Browser
 |
 v
Frontend ALB
 |
 v
Frontend Target Group
 |
 v
Frontend ECS Task
 |
 v
React Application
```

When the frontend requires data:

```text
React
 |
 v
Backend API
 |
 v
Backend ALB
 |
 v
Backend ECS
 |
 v
RDS
```

---

# AWS Components

| Component       | Purpose                         |
| --------------- | ------------------------------- |
| VPC             | Network boundary                |
| Subnets         | Network segmentation            |
| Security Groups | Network access control          |
| Frontend ALB    | Frontend traffic entry point    |
| Backend ALB     | Backend API entry point         |
| ECS Fargate     | Container runtime               |
| ECR             | Container image registry        |
| RDS PostgreSQL  | Persistent application database |
| CloudWatch      | Monitoring and logging          |
| SNS             | Notifications                   |
| IAM             | AWS authorization               |
| S3              | Terraform remote state          |
| GitHub OIDC     | CI/CD AWS authentication        |

---

# Containerization

Both application services are containerized using Docker.

```text
Frontend Source
      |
      v
Docker Build
      |
      v
Frontend Image
      |
      v
ECR
      |
      v
ECS Fargate
```

The backend follows the same pattern:

```text
Backend Source
      |
      v
Docker Build
      |
      v
Backend Image
      |
      v
ECR
      |
      v
ECS Fargate
```

Containerization provides:

* reproducible environments
* dependency isolation
* consistent deployment artifacts
* easier rollback
* predictable runtime behavior

---

# Amazon ECR

Amazon ECR stores the Docker images used by ECS.

```text
GitHub Actions
      |
      v
Docker Build
      |
      v
Amazon ECR
      |
      v
ECS Task Definition
      |
      v
ECS Task
```

ECR therefore acts as the bridge between the CI/CD build process and ECS runtime.

---

# Amazon ECS Fargate

The ECS cluster contains separate services for:

```text
securedataops-frontend-service
securedataops-backend-service
```

Fargate manages the underlying compute infrastructure.

The application therefore does not require manually managed EC2 servers.

Verified deployment state:

```text
Backend:
Desired  = 1
Running  = 1
Pending  = 0

Frontend:
Desired  = 1
Running  = 1
Pending  = 0
```

Deployments were also verified as:

```text
Status  = PRIMARY
Rollout = COMPLETED
```

---

# Application Load Balancers

Two Application Load Balancers are used:

```text
Frontend ALB
    |
    v
Frontend Target Group
    |
    v
Frontend ECS


Backend ALB
    |
    v
Backend Target Group
    |
    v
Backend ECS
```

Both ALBs are internet-facing.

The backend ALB listener was verified as:

```text
Port     : 80
Protocol : HTTP
Action   : Forward
```

The listener forwards traffic to the backend target group.

The frontend ALB follows the corresponding frontend target-group path.

---

# ALB Health Checks

ALB target health is used to determine whether ECS tasks are healthy enough to receive traffic.

Verified state:

```text
Backend Target:
healthy

Frontend Target:
healthy
```

This provides an important layer of protection against routing traffic to unhealthy application tasks.

---

# Infrastructure as Code

Terraform manages and validates the infrastructure configuration.

Terraform is used for:

* ECS
* ECR
* ALB
* target groups
* IAM
* Application Auto Scaling
* Terraform state configuration
* infrastructure checks

Some existing infrastructure is referenced through Terraform data sources.

This is intentional where resources are externally managed or already exist.

---

# Terraform Lifecycle

The normal infrastructure workflow is:

```text
Terraform Code
      |
      v
terraform fmt
      |
      v
terraform validate
      |
      v
terraform plan
      |
      v
Review
      |
      v
terraform apply
      |
      v
AWS
```

Terraform state is stored remotely.

---

# Terraform State

Terraform state is stored in Amazon S3.

The state bucket was verified to have:

```text
Versioning: Enabled
Encryption: AES256
```

A lifecycle policy was configured for:

```text
Noncurrent Terraform state versions
Retention: 365 days
```

This provides protection against losing useful historical state versions.

---

# CI/CD Architecture

<!--
SCREENSHOT:
docs/images/github-actions-success.png

Show the successful GitHub Actions workflow.
-->

```text
Developer
    |
    v
GitHub Repository
    |
    v
GitHub Actions
    |
    +--------------------+
    |                    |
    v                    v
Application Tests    Security Checks
    |                    |
    +---------+----------+
              |
              v
       Terraform Validation
              |
              v
         Docker Build
              |
              v
             ECR
              |
              v
        ECS Deployment
              |
              v
       ALB Health Check
              |
              v
        Running Service
```

---

# GitHub OIDC → AWS

GitHub Actions uses OIDC-based AWS authentication.

The flow is:

```text
GitHub Actions
      |
      v
GitHub OIDC Token
      |
      v
AWS IAM Trust Policy
      |
      v
Terraform / Deployment IAM Role
      |
      v
Temporary AWS Credentials
      |
      v
AWS APIs
```

This avoids the need to rely on permanent AWS access keys stored directly in the repository workflow.

The IAM role is designed around least-privilege access required by the CI/CD workflow.

---

# CI/CD Security

The pipeline performs security-related validation before deployment.

One important example occurred when `pip-audit` detected known vulnerabilities in an older PyJWT version.

The dependency was upgraded.

Final validation:

```text
Backend tests:
26 passed

Dependency audit:
No known vulnerabilities found
```

This demonstrates that dependency security is part of the deployment process rather than a manual afterthought.

---

# DevSecOps

Security is implemented across multiple layers.

```text
                 DEVSECOPS
                     |
       +-------------+-------------+
       |             |             |
       v             v             v
     Code          CI/CD         Runtime
       |             |             |
       v             v             v
    Testing       pip-audit      JWT
                               Authorization
       |             |
       v             v
   Code Review    OIDC / IAM
                     |
                     v
                   AWS
```

Security controls include:

* IAM
* GitHub OIDC
* JWT
* authorization
* dependency scanning
* encrypted RDS
* encrypted S3
* privacy-safe logging
* secret management strategy
* Terraform validation

---

# Authentication and Authorization

Privacy-sensitive endpoints are protected by bearer JWT authorization.

Protected endpoints include:

```text
GET    /api/v1/users/{user_id}
GET    /api/v1/users/{user_id}/export
PUT    /api/v1/users/{user_id}
DELETE /api/v1/users/{user_id}
```

Tokens must contain:

```text
sub
iss
aud
exp
```

The token subject must correspond to the requested user's UUID.

Expected behavior:

```text
Missing token
    ↓
401 Unauthorized

Invalid token
    ↓
401 Unauthorized

Expired token
    ↓
401 Unauthorized

Token belongs to another user
    ↓
403 Forbidden

JWT configuration missing
    ↓
503 Service Unavailable
```

The application does not currently implement its own complete identity-provider/login system.

Token issuance is expected to be handled by a trusted identity system.

---

# Secrets Management

Production secrets are not committed to Git.

Configuration examples contain placeholders only.

Sensitive configuration includes:

```text
DATABASE_URL
AUTH_JWT_SECRET
AUTH_JWT_ISSUER
AUTH_JWT_AUDIENCE
```

Production values are intended to be provided through approved AWS secret/configuration management.

---

# Observability

Observability covers:

* application logs
* ECS metrics
* ALB metrics
* health checks
* request IDs
* CloudWatch alarms
* SNS notifications

The operational flow is:

```text
Application
     |
     +------ Logs
     |
     +------ Metrics
     |
     +------ Health
              |
              v
          CloudWatch
              |
       +------+------+
       |             |
       v             v
     Logs          Alarms
                     |
                     v
                    SNS
                     |
                     v
                Notification
```

---

# Request IDs

The backend generates/uses request identifiers to help correlate requests across application behavior and operational logs.

Request IDs are validated before being logged.

Privacy-sensitive data is intentionally not placed into request/audit logs unnecessarily.

---

# CloudWatch and SNS

CloudWatch is used for monitoring and alarm evaluation.

SNS is used for notifications.

```text
Metric
  |
  v
CloudWatch Alarm
  |
  +---- OK
  |
  +---- ALARM
          |
          v
         SNS
          |
          v
      Notification
```

A CloudWatch alarm notification was successfully tested.

Example alarm:

```text
SecureDataOps-Backend-High-CPU
```

---

# Auto Scaling

The backend ECS service uses Application Auto Scaling.

Current verified configuration:

| Configuration      |                    Value |
| ------------------ | -----------------------: |
| Minimum capacity   |                        1 |
| Maximum capacity   |                        3 |
| Metric             | ALBRequestCountPerTarget |
| Target             |                      100 |
| Scale-out cooldown |               60 seconds |
| Scale-in cooldown  |              300 seconds |

Flow:

```text
Incoming Requests
       |
       v
Backend ALB
       |
       v
Requests / Target
       |
       v
Application Auto Scaling
       |
       +----------+
       |          |
       v          v
   Scale Out   Scale In
       |          |
       v          v
   ECS Tasks   ECS Tasks
```

The scaling target is:

```text
Minimum: 1
Maximum: 3
```

Dynamic scale-in and scale-out are enabled.

---

# Health Checks

The backend exposes:

```text
GET /health
```

Production verification returned:

```text
HTTP/1.1 200 OK
```

with:

```json
{
  "status": "healthy"
}
```

The backend ALB target was also verified as healthy.

---

# Database and Recovery

RDS PostgreSQL is a critical stateful component.

Verified configuration:

```text
Engine:
PostgreSQL

Automated backup retention:
7 days

Encryption:
Enabled

Multi-AZ:
Enabled

Backup window:
Configured

Latest restorable time:
Available
```

Automated RDS snapshots were also verified.

---

# Backup and Disaster Recovery

The recovery architecture is:

```text
                    PRODUCTION
                        |
              +---------+---------+
              |                   |
              v                   v
             RDS              Terraform
              |                  State
              v                   |
        Automated Backup          v
              |                  S3
              v                   |
       Point-in-Time             Versioning
          Recovery                 |
              |                    v
              v              365-day retention
      Isolated Restore
              |
              v
         Validation
              |
              v
       Approved Cutover
```

The database is restored into an isolated environment rather than immediately overwriting the production database.

Detailed recovery procedures are documented in:

`docs/BACKUP-DR.md`

---

# RDS Backup Verification

The deployed database was verified with AWS CLI.

Verified:

```text
Backup retention:     7 days
Storage encryption:   True
Multi-AZ:             True
Backup window:        Configured
Latest restorable:    Available
```

Automated snapshots were also available.

---

# DPDP-Oriented Data Protection

The application stores personal data including:

* name
* email
* optional phone
* UUID
* timestamps

The project implements engineering controls around the personal data actually processed by the application.

---

## Privacy Operations

The backend supports:

```text
Data access
Data export
Data correction
Data erasure
```

The protected export endpoint is:

```text
GET /api/v1/users/{user_id}/export
```

Correction:

```text
PUT /api/v1/users/{user_id}
```

Erasure:

```text
DELETE /api/v1/users/{user_id}
```

These operations are protected by authorization.

---

# Privacy Audit Logging

Privacy-related operations generate minimal audit events.

Examples include:

```text
User created
User accessed
User list accessed
User exported
User corrected
User erased
```

The audit events are designed to avoid logging unnecessary personal information.

They do not intentionally record:

* passwords
* JWT tokens
* request bodies
* email addresses
* phone numbers
* credentials
* unnecessary personal data

---

# DPDP Scope

The project documents:

* data inventory
* purpose mapping
* privacy controls
* authorization
* export
* correction
* erasure
* audit logging
* operational/legal gaps

Detailed documentation:

`docs/DPDP.md`

### Important

This project implements **DPDP-oriented engineering controls**.

It is not a legal certification or a claim of complete legal compliance.

Formal decisions around:

* lawful basis
* notice
* consent
* retention
* grievance handling
* identity verification
* rights-request procedures
* organizational responsibilities

require appropriate legal and organizational review.

---

# Incident Management

Monitoring is only useful if there is a response process.

The incident lifecycle is:

```text
Detect
  ↓
Triage
  ↓
Mitigate
  ↓
Recover
  ↓
Validate
  ↓
Communicate
  ↓
Postmortem
  ↓
Prevent Recurrence
```

Documentation:

```text
docs/incident-management.md
docs/runbooks.md
```

---

# Example Failure Handling

## Unhealthy ECS Task

```text
ECS Task
   |
   v
ALB Health Check
   |
   v
Unhealthy
   |
   v
ALB stops routing traffic
   |
   v
ECS replaces task
```

---

## Increased Traffic

```text
Traffic Increase
       |
       v
ALB
       |
       v
Request Count / Target
       |
       v
Auto Scaling
       |
       v
Additional ECS Task
```

---

## Vulnerable Dependency

```text
Dependency
    |
    v
pip-audit
    |
    v
Vulnerability
    |
    v
CI Failure
    |
    v
Upgrade Dependency
    |
    v
Run Tests
    |
    v
Run Security Audit
    |
    v
Successful Pipeline
```

---

## Database Failure

```text
Database Incident
       |
       v
Identify Recovery Point
       |
       v
Isolated RDS Restore
       |
       v
Application Validation
       |
       v
Approved Cutover
       |
       v
Monitoring
```

---

# SLOs

Service Level Objectives are documented separately.

The SLO documentation covers the operational targets used to reason about service reliability.

See:

`docs/slo.md`

---

# Testing

The backend contains automated tests covering:

* application behavior
* user operations
* authorization
* privacy operations
* database failure behavior
* observability behavior

Final local validation:

```text
26 passed
```

---

# Security Validation

Dependency security is continuously checked using:

```text
pip-audit
```

Current result:

```text
No known vulnerabilities found
```

This check is integrated into the CI/CD process.

---

# Operational Verification

The deployed AWS environment was manually verified.

## ECS Services

```text
Backend:
ACTIVE
Desired: 1
Running: 1
Pending: 0

Frontend:
ACTIVE
Desired: 1
Running: 1
Pending: 0
```

## Deployments

```text
Status: PRIMARY
Rollout: COMPLETED
```

## ALB Target Health

```text
Backend:  healthy
Frontend: healthy
```

## Backend Health

```text
HTTP 200 OK

{"status":"healthy"}
```

## Auto Scaling

```text
Minimum: 1
Maximum: 3
Target: 100 ALB requests/target
```

## RDS

```text
PostgreSQL
Backup retention: 7 days
Encryption: enabled
Multi-AZ: enabled
```

## Terraform State

```text
S3 versioning: enabled
S3 encryption: enabled
Noncurrent state retention: 365 days
```

---

# CI/CD Evidence

<!--
SCREENSHOT

docs/images/github-actions-success.png

Show the successful GitHub Actions workflow.
-->

The final CI/CD pipeline successfully completed after resolving a vulnerable PyJWT dependency.

The pipeline therefore demonstrates:

```text
Source
  ↓
Test
  ↓
Security Audit
  ↓
Terraform Validation
  ↓
Build
  ↓
Deploy
```

---

# Screenshots

The README should include selected screenshots as evidence rather than filling the repository with screenshots of every AWS page.

## Application Dashboard

<!--
docs/images/application-dashboard.png
-->

Show the running application using dummy/non-sensitive user data.

---

## AWS VPC / Networking

<!--
docs/images/vpc-networking.png
-->

Show:

* VPC
* subnets
* availability zones
* relevant network structure

---

## ECS Services

<!--
docs/images/ecs-services.png
-->

Show:

* cluster
* frontend service
* backend service
* running tasks

---

## ECS Deployment

<!--
docs/images/ecs-deployment.png
-->

Show:

* PRIMARY
* COMPLETED
* running/desired tasks

---

## ALB Target Health

<!--
docs/images/alb-target-health.png
-->

Show:

* frontend target
* backend target
* healthy state

---

## GitHub Actions

<!--
docs/images/github-actions-success.png
-->

Show the successful CI/CD workflow.

---

## CloudWatch Alarm

<!--
docs/images/cloudwatch-alarm.png
-->

Show the configured alarm.

---

## SNS Notification

<!--
docs/images/sns-notification.png
-->

Show the successful alarm notification.

Do not expose private email information.

---

## Auto Scaling

<!--
docs/images/ecs-autoscaling.png
-->

Show:

* minimum capacity
* maximum capacity
* target tracking
* ALBRequestCountPerTarget

---

## RDS

<!--
docs/images/rds-backup.png
-->

Show:

* PostgreSQL
* Multi-AZ
* encryption
* backup retention

---

## Terraform State

<!--
docs/images/terraform-state.png
-->

Show:

* S3 versioning
* encryption
* lifecycle policy

---

## Health Check

<!--
docs/images/health-check.png
-->

Show:

```text
HTTP 200 OK
{"status":"healthy"}
```

---

# Architecture Diagrams

The repository should contain four primary architecture diagrams.

## 1. Overall AWS Architecture

```text
Internet
   |
   +--------------------+
   |                    |
   v                    v
Frontend ALB          Backend ALB
   |                    |
   v                    v
Frontend ECS          Backend ECS
                          |
                          v
                       RDS
```

Add the VPC, subnets, security groups, and availability zones around these components in the final visual diagram.

Recommended:

`docs/images/architecture-overview.png`

---

## 2. CI/CD Architecture

```text
Developer
    |
    v
GitHub
    |
    v
GitHub Actions
    |
    +---- Tests
    |
    +---- Security
    |
    +---- Terraform
    |
    +---- Docker
            |
            v
           ECR
            |
            v
           ECS
            |
            v
           ALB
```

Recommended:

`docs/images/cicd-pipeline.png`

---

## 3. Security Architecture

```text
User
 |
 v
ALB
 |
 v
Backend
 |
 v
JWT Authorization
 |
 v
Application
 |
 v
RDS


GitHub
 |
 v
OIDC
 |
 v
IAM
 |
 v
AWS
```

Recommended:

`docs/images/security-architecture.png`

---

## 4. Backup / DR Architecture

```text
RDS
 |
 +---- Automated Backups
 |
 +---- PITR
 |
 +---- Multi-AZ
 |
 v
Isolated Restore
 |
 v
Validation
 |
 v
Approved Cutover


Terraform
 |
 v
S3
 |
 +---- Encryption
 |
 +---- Versioning
 |
 v
365-Day Noncurrent Retention
```

Recommended:

`docs/images/backup-dr.png`

---

# Repository Structure

```text
secure-data-platform/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   └── ...
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── Dockerfile
│   └── ...
│
├── infra/
│   └── terraform/
│       ├── resources.tf
│       ├── variables.tf
│       ├── data-sources.tf
│       ├── backup-dr.tf
│       └── README.md
│
├── docs/
│   ├── BACKUP-DR.md
│   ├── DPDP.md
│   ├── incident-management.md
│   ├── runbooks.md
│   ├── slo.md
│   └── images/
│
├── .github/
│   └── workflows/
│
├── README.md
└── ...
```

---

# Documentation

Detailed operational documentation is maintained separately.

| Document                      | Purpose                        |
| ----------------------------- | ------------------------------ |
| `docs/BACKUP-DR.md`           | Backup and disaster recovery   |
| `docs/DPDP.md`                | DPDP-oriented privacy controls |
| `docs/incident-management.md` | Incident lifecycle             |
| `docs/runbooks.md`            | Operational troubleshooting    |
| `docs/slo.md`                 | Service Level Objectives       |
| `infra/terraform/README.md`   | Terraform infrastructure       |

---

# Deployment Lifecycle

The complete lifecycle is:

```text
Developer
    |
    v
GitHub
    |
    v
GitHub Actions
    |
    +----------------+
    |                |
    v                v
Testing          Security
    |                |
    +-------+--------+
            |
            v
     Terraform Validation
            |
            v
       Docker Build
            |
            v
           ECR
            |
            v
       ECS Fargate
            |
            v
           ALB
            |
            v
       Health Checks
            |
            v
        CloudWatch
            |
            v
          Operate
            |
       +----+----+
       |         |
       v         v
   Scaling     Alerts
       |         |
       +----+----+
            |
            v
       Recovery
```

---

# Production Readiness Considerations

The project intentionally demonstrates production-oriented engineering practices, but a real enterprise production environment would require additional controls depending on the organization's requirements.

Potential future improvements include:

* production identity provider integration
* asymmetric/JWKS-backed JWT validation
* formal secret rotation
* TLS/HTTPS everywhere
* AWS WAF
* CloudFront where appropriate
* stronger network isolation
* private database networking
* centralized security monitoring
* formal penetration testing
* formal disaster-recovery exercises
* multi-region recovery where required
* cost monitoring
* formal compliance/legal review
* formal retention policies
* production-grade incident escalation

These are documented as future considerations rather than being falsely presented as already implemented.

---

# What This Project Demonstrates

SecureDataOps demonstrates practical understanding of the following areas:

### Cloud

* AWS VPC
* subnets
* security groups
* ALB
* ECS
* Fargate
* ECR
* RDS
* S3
* CloudWatch
* SNS
* IAM

### DevOps

* Git
* GitHub
* Docker
* Terraform
* CI/CD
* Infrastructure as Code
* automated deployment

### DevSecOps

* OIDC
* IAM
* JWT
* authorization
* dependency scanning
* secure configuration
* privacy-safe logging

### SRE

* monitoring
* alerting
* health checks
* SLOs
* auto scaling
* incident management
* runbooks
* backup and recovery

### Data Protection

* personal-data inventory
* privacy operations
* data export
* correction
* erasure
* audit events
* DPDP-oriented controls

---

# Lessons Learned

## Deployment is only the beginning

A working deployment is not the same as a production-ready system.

---

## Networking matters

The application depends on controlled communication between:

```text
Internet
   ↓
ALB
   ↓
ECS
   ↓
RDS
```

VPCs, subnets, routing, and security groups determine how these components communicate.

---

## CI/CD should fail safely

The dependency vulnerability discovered by `pip-audit` demonstrated why security checks belong inside the deployment pipeline.

---

## Observability must lead to action

Metrics become useful when they result in:

```text
Metric
 ↓
Alarm
 ↓
Notification
 ↓
Investigation
 ↓
Runbook
 ↓
Recovery
```

---

## Scaling requires a measurable signal

The backend uses ALB request count per target instead of arbitrarily scaling based on guesswork.

---

## Backups are not enough

A backup strategy is incomplete without a documented restoration procedure and periodic restore testing.

---

## Privacy requires engineering controls

DPDP-oriented protection requires more than documentation.

The application also needs:

* authorization
* controlled access
* export
* correction
* erasure
* auditability
* safe logging

---

# Project Status

## Application

* [x] React frontend
* [x] FastAPI backend
* [x] PostgreSQL
* [x] CRUD operations
* [x] Docker
* [x] Health endpoint

## AWS

* [x] VPC/network integration
* [x] Subnets
* [x] Security/network controls
* [x] Frontend ALB
* [x] Backend ALB
* [x] Target groups
* [x] ECS Fargate
* [x] ECR
* [x] RDS PostgreSQL
* [x] CloudWatch
* [x] SNS
* [x] IAM
* [x] S3 Terraform state

## DevOps

* [x] Terraform
* [x] GitHub Actions
* [x] Docker image build
* [x] ECR deployment
* [x] ECS deployment
* [x] GitHub OIDC
* [x] Infrastructure validation

## SRE

* [x] Health checks
* [x] Monitoring
* [x] CloudWatch alarms
* [x] SNS notifications
* [x] ECS Auto Scaling
* [x] SLO documentation
* [x] Incident management
* [x] Runbooks

## Security

* [x] IAM
* [x] GitHub OIDC
* [x] JWT authorization
* [x] Dependency vulnerability scanning
* [x] Secure configuration examples
* [x] Privacy-aware logging
* [x] RDS encryption
* [x] S3 encryption

## Backup / DR

* [x] RDS automated backups
* [x] 7-day retention
* [x] RDS encryption
* [x] Multi-AZ
* [x] Automated snapshots
* [x] Terraform state versioning
* [x] Terraform state encryption
* [x] 365-day noncurrent state retention
* [x] Recovery procedure documentation

## DPDP-Oriented Controls

* [x] Data inventory
* [x] Purpose mapping
* [x] Data export
* [x] Data correction
* [x] Data erasure
* [x] Authorization
* [x] Privacy audit events
* [x] Sensitive-data logging reduction
* [x] DPDP documentation

## Validation

* [x] Backend tests
* [x] 26 tests passing
* [x] Dependency audit
* [x] No known dependency vulnerabilities
* [x] Terraform validation
* [x] ECS deployment verified
* [x] ALB target health verified
* [x] Production `/health` verified
* [x] Auto Scaling verified
* [x] RDS backup configuration verified
* [x] S3 versioning verified
* [x] S3 encryption verified
* [x] S3 lifecycle policy verified

---

# Final Architecture Philosophy

SecureDataOps follows a simple principle:

```text
Build
  ↓
Automate
  ↓
Secure
  ↓
Deploy
  ↓
Observe
  ↓
Scale
  ↓
Recover
  ↓
Improve
```

The project demonstrates that DevOps is not simply about deploying an application.

A production-oriented system must be:

**automated, observable, secure, scalable, recoverable, and maintainable.**

---

# Author

## Rachit Singh Chauhan

B.Tech — Computer Science (AI & ML)

Areas of interest:

* DevOps
* SRE
* DevSecOps
* AWS
* Cloud Infrastructure
* Infrastructure as Code
* CI/CD
* AI/ML Systems
* Backend Engineering
* Production Engineering
