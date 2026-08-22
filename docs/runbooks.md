# SecureDataOps SRE runbooks

Use these runbooks for the Fargate services in `us-east-1`. Commands are
PowerShell-compatible and read state unless explicitly labelled as a
remediation. The backend is `securedataops-backend-service` in ECS cluster
`securedataops-cluster1`, behind ALB `securedataops-alb` and target group
`securedataops-backend-tg`. Backend logs are in
`/ecs/securedataops-backend`.

```powershell
$Region = "us-east-1"
$Cluster = "securedataops-cluster1"
$BackendService = "securedataops-backend-service"
$AlbName = "securedataops-alb"
$TargetGroupName = "securedataops-backend-tg"
$TargetGroupArn = aws elbv2 describe-target-groups --names $TargetGroupName --region $Region --query "TargetGroups[0].TargetGroupArn" --output text
```

The backend logs a request ID for every request and returns it as
`X-Request-ID`. Keep that value when correlating an ALB response with
`/ecs/securedataops-backend` logs. The database failure response is the safe
`503 {"detail":"Database temporarily unavailable."}` and does not expose
database connection details to the client.

## 1. ECS task unhealthy or repeatedly restarting

**Symptoms and impact:** ECS desired and running task counts differ, service
events show repeated starts/stops, or users receive intermittent 5xx. A
single-task backend can be unavailable while a replacement starts.

**First checks and signals:** ECS service events, task `lastStatus` and
`stoppedReason`, container exit details, CPU/memory utilization, and backend
logs.

```powershell
aws ecs describe-services --cluster $Cluster --services $BackendService --region $Region
aws ecs list-tasks --cluster $Cluster --service-name $BackendService --desired-status RUNNING --region $Region
aws ecs list-tasks --cluster $Cluster --service-name $BackendService --desired-status STOPPED --region $Region
aws logs tail /ecs/securedataops-backend --since 30m --region $Region --format short
```

**Healthy result:** running count equals desired count, a task reports
`RUNNING`, no repeating deployment/task events appear, and logs show normal
request records rather than startup failures.

**Diagnosis and safe remediation:** inspect the stopped task before acting:

```powershell
$StoppedTasks = aws ecs list-tasks --cluster $Cluster --service-name $BackendService --desired-status STOPPED --region $Region --query "taskArns" --output text
aws ecs describe-tasks --cluster $Cluster --tasks $StoppedTasks --region $Region
```

Use the stopped reason and logs to distinguish image/startup, resource, and
dependency failures. If the failure is transient and the task definition has
not changed, a safe recovery action is a replacement deployment:

```powershell
aws ecs update-service --cluster $Cluster --service $BackendService --force-new-deployment --region $Region
aws ecs wait services-stable --cluster $Cluster --services $BackendService --region $Region
```

Do not repeatedly force deployments when the same task stops; preserve the
first stopped-task evidence. Verify desired equals running and the target is
healthy. Escalate when replacements continue failing, a new deployment
introduced the failures, or the backend has no healthy running task.

## 2. ALB target unhealthy

**Symptoms and impact:** `UnHealthyHostCount` rises, ALB requests receive 5xx,
or ECS has a running task that cannot receive traffic. `/health` is the
backend container health endpoint.

**First checks and signals:** target health state/reason, ECS service events,
`UnHealthyHostCount`, and backend `/health` logs.

```powershell
aws elbv2 describe-target-health --target-group-arn $TargetGroupArn --region $Region
aws ecs describe-services --cluster $Cluster --services $BackendService --region $Region
aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name UnHealthyHostCount --dimensions Name=TargetGroup,Value=targetgroup/securedataops-backend-tg/781ee1c7b999a392 Name=LoadBalancer,Value=app/securedataops-alb/a1b68a761929383a --statistics Maximum --period 60 --start-time (Get-Date).ToUniversalTime().AddMinutes(-30).ToString("o") --end-time (Get-Date).ToUniversalTime().ToString("o") --region $Region
```

**Healthy result:** every registered backend target is `healthy`,
`UnHealthyHostCount` is zero, and the service has matching desired/running
counts.

**Diagnosis and safe remediation:** use the target-health reason together
with task events and logs. The configured container health check calls
`http://127.0.0.1:8000/health`; it has a 3-second client timeout, 5-second
health-check timeout, 30-second interval, three retries, and a 20-second
start period. If the task is otherwise healthy but target registration has
not recovered after that window, replace it once using the ECS deployment
command in runbook 1. Do not change target-group health-check settings during
the incident.

Verify `describe-target-health` returns `healthy` and request/5xx metrics
return to baseline. Escalate when all targets remain unhealthy after a stable
replacement, or the target-health reason indicates a networking/load-balancer
configuration issue.

## 3. Backend 5xx spike

**Symptoms and impact:** `HTTPCode_Target_5XX_Count` or
`HTTPCode_ELB_5XX_Count` rises, availability SLO consumption increases, and
clients receive failed requests.

**First checks and signals:** ALB request and 5xx counts, target health,
backend logs, and the affected request ID.

```powershell
aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name RequestCount --dimensions Name=LoadBalancer,Value=app/securedataops-alb/a1b68a761929383a --statistics Sum --period 300 --start-time (Get-Date).ToUniversalTime().AddMinutes(-30).ToString("o") --end-time (Get-Date).ToUniversalTime().ToString("o") --region $Region
aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name HTTPCode_Target_5XX_Count --dimensions Name=LoadBalancer,Value=app/securedataops-alb/a1b68a761929383a --statistics Sum --period 300 --start-time (Get-Date).ToUniversalTime().AddMinutes(-30).ToString("o") --end-time (Get-Date).ToUniversalTime().ToString("o") --region $Region
aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name HTTPCode_ELB_5XX_Count --dimensions Name=LoadBalancer,Value=app/securedataops-alb/a1b68a761929383a --statistics Sum --period 300 --start-time (Get-Date).ToUniversalTime().AddMinutes(-30).ToString("o") --end-time (Get-Date).ToUniversalTime().ToString("o") --region $Region
aws logs tail /ecs/securedataops-backend --since 30m --region $Region --format short
```

**Healthy result:** 5xx counts are zero or return to their normal baseline,
targets are healthy, and logs contain successful request records. Filter a
known request ID without placing credentials in the filter:

```powershell
aws logs filter-log-events --log-group-name /ecs/securedataops-backend --filter-pattern '"request_id=<request-id>"' --region $Region
```

**Diagnosis and safe remediation:** separate target 5xx (application/backend
response) from ELB 5xx (load-balancer-side failure). Check runbooks 1, 2, and
4 before replacing tasks. For a known-bad recent deployment, use the existing
deployment process to return to the last known-good task definition; do not
manually edit a task definition during an incident. For a transient task
failure, use one replacement deployment as in runbook 1.

Verify both 5xx metrics and target health after recovery. Escalate for a
sustained spike, ELB-side 5xx, or a spike that persists after reverting or
replacing the backend task.

## 4. PostgreSQL/database unavailable

**Symptoms and impact:** user API requests return the generic database `503`
response, backend logs contain `Database temporarily unavailable`, and target
5xx may rise. Health can remain successful because `/health` does not query
PostgreSQL.

**First checks and signals:** safe 503 body, request ID, backend database
unavailable log records, request/target-5xx metrics, and backend task health.

```powershell
aws logs filter-log-events --log-group-name /ecs/securedataops-backend --filter-pattern '"Database temporarily unavailable"' --region $Region
aws ecs describe-services --cluster $Cluster --services $BackendService --region $Region
aws elbv2 describe-target-health --target-group-arn $TargetGroupArn --region $Region
```

**Healthy result:** user API requests no longer return 503, no new database
unavailable log records appear, and reads/writes complete normally. The
application uses a 10-second database connect timeout and a 5-second
PostgreSQL statement timeout. It retries only bounded idempotent reads;
writes are intentionally not retried.

**Diagnosis and safe remediation:** correlate the client `X-Request-ID` with
the request log, confirm whether failures are isolated or widespread, and
check the database service through its approved operational channel. Do not
retry writes from a client or repeatedly force ECS deployments for a database
outage: neither restores an unavailable database and duplicate writes are
unsafe. After the database service is confirmed available, allow pooled
connections to be re-established; a single backend replacement can be used
only if stale tasks do not recover.

Verify successful user reads and writes, the absence of new generic 503s, and
falling target-5xx counts. Escalate immediately when the database service is
unavailable, credentials/connectivity must be changed, or 503s persist after
the database is healthy; this repository does not identify a database ARN or
endpoint to operate directly.

## 5. High backend request latency

**Symptoms and impact:** `TargetResponseTime` p95 exceeds the one-second SLO
target, users experience slow responses, and the latency compliance budget is
consumed. This is not automatically an availability failure.

**First checks and signals:** ALB p95 target response time, request count,
backend CPU/memory utilization, target health, and request logs with duration
in milliseconds.

```powershell
aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name TargetResponseTime --dimensions Name=LoadBalancer,Value=app/securedataops-alb/a1b68a761929383a --extended-statistics p95 --period 300 --start-time (Get-Date).ToUniversalTime().AddMinutes(-30).ToString("o") --end-time (Get-Date).ToUniversalTime().ToString("o") --region $Region
aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name CPUUtilization --dimensions Name=ClusterName,Value=$Cluster Name=ServiceName,Value=$BackendService --statistics Average --period 300 --start-time (Get-Date).ToUniversalTime().AddMinutes(-30).ToString("o") --end-time (Get-Date).ToUniversalTime().ToString("o") --region $Region
aws cloudwatch get-metric-statistics --namespace AWS/ECS --metric-name MemoryUtilization --dimensions Name=ClusterName,Value=$Cluster Name=ServiceName,Value=$BackendService --statistics Average --period 300 --start-time (Get-Date).ToUniversalTime().AddMinutes(-30).ToString("o") --end-time (Get-Date).ToUniversalTime().ToString("o") --region $Region
aws logs tail /ecs/securedataops-backend --since 30m --region $Region --format short
```

**Healthy result:** p95 is at or below one second in active five-minute
periods, CPU/memory are not persistently saturated, targets are healthy, and
request log durations return to baseline.

**Diagnosis and safe remediation:** compare latency with request volume,
CPU/memory, 503s, and database-unavailable logs. If database timeouts or 503s
coincide, use runbook 4. If load is high and the target-tracking policy is
not adding capacity, use runbook 6. Do not add application-wide request
timeouts or increase database timeouts during an incident; those are design
changes, not safe immediate remediation.

Verify the next active five-minute periods meet the p95 target and request
logs show lower durations. Escalate for sustained latency with normal load,
or sustained saturation after verified scaling.

## 6. ECS service not scaling as expected

**Symptoms and impact:** request volume rises but desired/running task counts
do not change, or capacity does not return after load falls. This can increase
latency and 5xx risk.

**First checks and signals:** desired/running/pending counts, deployment
state, scalable target min/max, target-tracking policy, and
`RequestCountPerTarget`. The configured policy uses
`ALBRequestCountPerTarget` with target value 100, 60-second scale-out cooldown,
and 300-second scale-in cooldown.

```powershell
aws ecs describe-services --cluster $Cluster --services $BackendService --region $Region
aws application-autoscaling describe-scalable-targets --service-namespace ecs --resource-ids service/securedataops-cluster1/securedataops-backend-service --scalable-dimension ecs:service:DesiredCount --region $Region
aws application-autoscaling describe-scaling-policies --service-namespace ecs --resource-id service/securedataops-cluster1/securedataops-backend-service --scalable-dimension ecs:service:DesiredCount --region $Region
aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name RequestCountPerTarget --dimensions Name=TargetGroup,Value=targetgroup/securedataops-backend-tg/781ee1c7b999a392 Name=LoadBalancer,Value=app/securedataops-alb/a1b68a761929383a --statistics Sum --period 60 --start-time (Get-Date).ToUniversalTime().AddMinutes(-30).ToString("o") --end-time (Get-Date).ToUniversalTime().ToString("o") --region $Region
```

**Healthy result:** the scalable target is registered, a target-tracking
policy is present, desired count changes after sustained load outside the
cooldown windows, and ECS reaches that desired running count with healthy ALB
targets.

**Diagnosis and safe remediation:** confirm that the service is not in a
deployment failure, the scalable target min/max permits the needed count, and
the measured request count per target exceeds the configured target long
enough to pass cooldown. Do not alter the target-tracking policy during an
incident. If approved capacity is needed immediately and remains within the
registered maximum, increase desired count once and then monitor:

```powershell
$CurrentDesired = [int](aws ecs describe-services --cluster $Cluster --services $BackendService --region $Region --query "services[0].desiredCount" --output text)
aws ecs update-service --cluster $Cluster --service $BackendService --desired-count ($CurrentDesired + 1) --region $Region
aws ecs wait services-stable --cluster $Cluster --services $BackendService --region $Region
```

Verify healthy targets, matching desired/running counts, and improved
`RequestCountPerTarget` and latency. Escalate when min/max limits, placement,
or repeated task failures prevent the service from reaching desired capacity,
or when the target-tracking policy is absent or not evaluating.
