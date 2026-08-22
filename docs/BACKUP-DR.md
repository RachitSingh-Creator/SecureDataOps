# SecureDataOps backup and disaster recovery

## Targets

| Recovery objective | Target | Basis |
| --- | --- | --- |
| RPO | 24 hours | RDS automated backups must retain at least seven days and support point-in-time recovery. |
| RTO | 4 hours | Includes restoring to an isolated RDS instance, validating the application, and performing an approved cutover. |
| Terraform state RPO | Last successful state write | The S3 backend uses server-side encryption, versioning, and native lockfiles. |

These are operating targets, not proof that a restore has succeeded. A restore
test is required before declaring the targets achieved.

## What is protected

- **PostgreSQL/RDS:** automated backups, point-in-time recovery, encrypted
  storage, and Multi-AZ are checked read-only by Terraform. RDS remains outside
  Terraform resource management in this migration.
- **Terraform state:** the S3 backend is encrypted, versioned, and locked. The
  bootstrap procedure retains noncurrent production state versions for 365
  days; see `infra/terraform/README.md`.
- **Container artifacts:** ECR repository encryption and tag immutability are
  preserved by the existing Terraform inventory. Retention/lifecycle policy is
  not assumed and must be reviewed before introducing one.
- **Runtime configuration:** ECS task-definition revisions and deployment
  history remain recoverable through ECS/CI-CD; task definitions and services
  are not backup-managed by this migration.

## Read-only verification

Use a least-privilege AWS identity. These commands do not expose database
credentials or alter infrastructure.

```powershell
$Region = "us-east-1"
$Database = "securedataops-db"
$StateBucket = "securedataops-tfstate-011582457592-us-east-1"

aws rds describe-db-instances --db-instance-identifier $Database --region $Region --query "DBInstances[0].{RetentionDays:BackupRetentionPeriod,BackupWindow:PreferredBackupWindow,LatestRestorableTime:LatestRestorableTime,MultiAZ:MultiAZ,StorageEncrypted:StorageEncrypted,DeletionProtection:DeletionProtection,CopyTagsToSnapshot:CopyTagsToSnapshot}" --output table
aws rds describe-db-snapshots --db-instance-identifier $Database --snapshot-type automated --region $Region --query "reverse(sort_by(DBSnapshots,&SnapshotCreateTime))[:5].{Id:DBSnapshotIdentifier,Created:SnapshotCreateTime,Status:Status}" --output table
aws s3api get-bucket-versioning --bucket $StateBucket --output json
aws s3api get-bucket-lifecycle-configuration --bucket $StateBucket --output json
aws ecr get-lifecycle-policy --repository-name securedataops-backend --region $Region --output json
aws ecr get-lifecycle-policy --repository-name securedatops-frontend --region $Region --output json
```

Treat a missing ECR lifecycle policy as a review finding, not permission to
create one during an incident. Confirm that any future policy retains the image
digests needed for the current and rollback ECS revisions.

The Terraform validation role also needs the read-only
`rds:DescribeDBInstances` action before the new backup-baseline check can run
in CI. Add it to the externally managed least-privilege validation policy; do
not grant RDS write, restore, snapshot, or delete permissions to CI.

## Database restore procedure

1. Declare an incident and preserve the source instance, CloudWatch logs, and
   current RDS metadata. Do not restore over the production instance.
2. Select a restore point at or before the incident using
   `LatestRestorableTime` or an automated snapshot. Record the intended RPO.
3. Restore to a **new, isolated** DB instance using the AWS console or the RDS
   point-in-time restore API. Reapply the source's VPC security groups, subnet
   group, parameter group, encryption, and Multi-AZ settings after verifying
   them from the source; do not guess these values.
4. Wait for `available`, run schema and application smoke tests with a
   non-production secret, and validate data completeness. Do not expose the
   restored endpoint publicly.
5. Obtain incident-owner approval for the application cutover. Update the
   production secret through the approved secret-management workflow, deploy a
   controlled revision, then verify `/health`, ALB target health, and database
   reads/writes.
6. Preserve the original instance until the incident is resolved and the
   rollback decision window has closed. Document actual RPO/RTO and clean up
   the isolated restore only with approval.

## Terraform state recovery

1. Stop concurrent Terraform runs; allow or resolve the S3 `.tflock` through
   the normal Terraform lock workflow rather than deleting it manually.
2. Identify the known-good S3 object version for
   `securedataops/production/terraform.tfstate` and have a second operator
   review the version and timestamp.
3. Copy that version to the current state key using an approved, audited AWS
   procedure. Do not overwrite a newer state without preserving its version.
4. Run `terraform init`, `terraform state list`, and a read-only plan. Do not
   apply until the plan is reviewed and approved.

## Required restore test

At least annually, and after material database or backup-policy changes,
perform a non-production point-in-time restore. Record the restore timestamp,
selected recovery point, validation evidence, actual RPO/RTO, and cleanup
approval. This test is still required because this repository has no AWS
credentials with which to confirm the live backup configuration or exercise a
restore.
