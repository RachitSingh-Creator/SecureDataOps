# SecureDataOps incident management

This process covers the backend running on ECS/Fargate behind
`securedataops-alb`, with PostgreSQL as its dependency. Detection uses the
existing CloudWatch dashboard, ECS/ALB state, backend CloudWatch logs, and
customer reports. This repository does not define alert-routing or incident
notification automation; responders declare and coordinate incidents through
the team's established communication channel.

Use [the SLOs and error budgets](slo.md) to assess impact and
[the runbooks](runbooks.md) for commands and remediation. This document
coordinates the response; it does not replace the runbooks.

## Severity

| Severity | SecureDataOps definition | Examples |
| --- | --- | --- |
| SEV-1 | Broad production unavailability or a serious, ongoing availability breach with no prompt recovery path. | No healthy backend target/task; sustained ALB 5xx; a PostgreSQL outage causing most user API requests to return the generic 503; an ECS/ALB failure that prevents normal service. |
| SEV-2 | Material but partial customer impact, or a sustained condition likely to consume the availability or latency SLO budget if not corrected. | Sustained backend 5xx/503 for a subset of requests; unhealthy target while service remains available; p95 target response time above the 1-second SLO target across active periods; target-tracking capacity does not meet load. |
| SEV-3 | Limited, intermittent, or short-lived impact with a known workaround or stable service. | A single recovered task restart, a brief latency spike, or an isolated database timeout that does not produce sustained customer impact. |

Raise severity when scope, duration, repeated failures, or error-budget
consumption grows. Lower it only after recovery is verified.

## Live incident checklist

1. Record detection time, symptom, reporter, and initial severity.
2. Declare the incident and assign an Incident Commander (IC); one person may
   hold all roles for a small incident.
3. Check the CloudWatch dashboard, ECS service state, ALB target health, and
   backend logs. Preserve an affected `X-Request-ID` when available.
4. Select the matching [runbook](runbooks.md) and perform its first checks.
5. State the current impact, owner, and next update time in the team channel.
6. Apply only a runbook-supported, reversible remediation; record the action
   and result.
7. Verify customer recovery, ALB/ECS health, and the relevant SLI before
   resolving.
8. Capture follow-ups and schedule a postmortem for SEV-1 and material SEV-2
   incidents.

## Incident roles

| Role | Responsibility |
| --- | --- |
| Incident Commander | Sets severity and response cadence, keeps scope and customer impact current, approves mitigation decisions, and declares recovery. |
| Technical Lead/Responder | Runs the selected runbook, gathers evidence, performs approved remediation, and reports verification results to the IC. |
| Communications/Recorder | Maintains the timeline, records owners and decisions, publishes agreed updates through the team's established channel, and captures follow-ups. |

For a small incident, one person may hold multiple roles. The IC still names
the active role holder and records material decisions.

## Lifecycle and responsibilities

| Stage | Required action |
| --- | --- |
| Detect | Observe a customer report or an existing signal: ALB request/5xx count, `TargetResponseTime`, `UnHealthyHostCount`, ECS CPU/memory, task state, or backend logs. |
| Declare | Choose provisional severity, open the incident record, name the IC, and state customer impact. |
| Triage | Identify whether the symptom is task, ALB target, 5xx, database, latency, or scaling related; choose the matching runbook. |
| Assign roles | IC owns scope, decisions, and cadence; Technical Lead/Responder performs investigation and approved remediation; Communications/Recorder maintains the timeline and updates. One person can hold multiple roles when necessary. |
| Investigate | Use read-only checks first. Correlate backend logs with `X-Request-ID`; do not place credentials or connection strings in updates. |
| Mitigate | Use the safe remediation in the selected runbook. Avoid repeated force deployments, client write retries, and unreviewed configuration changes. |
| Recover | Restore healthy tasks/targets and normal request behavior. |
| Verify | Confirm the runbook's verification criteria and check the relevant SLO signal over subsequent periods. |
| Resolve | Record resolution time, final impact, and remaining risk; communicate recovery. |
| Postmortem | Complete the template below for SEV-1 and material SEV-2 incidents. Track corrective actions to completion. |

## Response procedure and runbook routing

Use the exact AWS CLI checks and remediation guardrails in
[docs/runbooks.md](runbooks.md).

| Symptom | Primary runbook | Key response notes |
| --- | --- | --- |
| ECS desired/running counts differ, tasks stop, or restarts repeat | [1. ECS task unhealthy or repeatedly restarting](runbooks.md#1-ecs-task-unhealthy-or-repeatedly-restarting) | Preserve task stopped reasons before one replacement deployment. |
| `UnHealthyHostCount` rises or a running task cannot receive traffic | [2. ALB target unhealthy](runbooks.md#2-alb-target-unhealthy) | Inspect target-health reason and ECS events; do not change health-check settings during the incident. |
| ALB target or ELB 5xx rises | [3. Backend 5xx spike](runbooks.md#3-backend-5xx-spike) | Separate target 5xx from ALB-side 5xx and correlate request IDs. |
| Generic `503 {"detail":"Database temporarily unavailable."}` occurs | [4. PostgreSQL/database unavailable](runbooks.md#4-postgresqldatabase-unavailable) | Database reads have bounded retries; writes are not retried. Do not retry client writes. |
| p95 `TargetResponseTime` exceeds 1 second | [5. High backend request latency](runbooks.md#5-high-backend-request-latency) | Compare load, ECS CPU/memory, target health, 503s, and request-log durations. |
| Desired capacity does not follow backend load | [6. ECS service not scaling as expected](runbooks.md#6-ecs-service-not-scaling-as-expected) | Verify `ALBRequestCountPerTarget`, cooldowns, min/max, and task placement before changing desired count. |

For every route, the IC records the decision, operator, timestamp, and
verification result. Do not duplicate the runbook commands here; use the
runbook as the source of truth.

## Timeline template

```text
Incident ID/title:
Severity:
IC / Technical Lead / Communications-Recorder:

Detected (UTC):
Declared (UTC):
Customer impact and scope:
Affected request IDs (if available):

UTC time | Observation or signal | Action and owner | Result / next decision
---------|-----------------------|------------------|-----------------------
         |                       |                  |

Mitigation applied (UTC):
Recovery observed (UTC):
Verification completed (UTC):
Resolved (UTC):
SLO/error-budget impact:
Follow-up owner and due date:
```

## Escalation

Escalate immediately to the responsible engineering/dependency owner for any
SEV-1, including no healthy backend target/task, broad 5xx/503, or a confirmed
database outage. Escalate a SEV-2 when customer impact persists, mitigation
does not recover service promptly, failures repeat after remediation, or SLO
availability/latency budget is being materially consumed. Escalate a SEV-3 if
it becomes sustained, affects more customers, or repeats.

Escalate beyond the application responder when the evidence points to an
infrastructure or dependency boundary: ALB-side 5xx, ECS placement/task
replacement failure, target health/networking issue, or PostgreSQL/RDS
availability/connectivity issue. This repository does not name a database ARN
or endpoint, so use the approved database operational channel rather than
guessing or changing infrastructure. Preserve evidence and avoid risky
changes while awaiting assistance.

## SLO and error-budget connection

Availability is measured over the rolling 30-day window from ALB request and
5xx metrics; backend 503 responses count as availability failures. The 0.5%
availability error budget is approximately 3 hours 36 minutes only as a time
analogy; failed-request percentage is authoritative. Healthy budget permits
normal releases, reduced budget requires caution and closer monitoring, and
exhausted budget prioritizes reliability work over unnecessary risky changes.

Latency is separate: its 5% compliance budget is evaluated from active
five-minute periods whose p95 target response time exceeds one second. Do not
convert latency budget consumption into downtime. See [docs/slo.md](slo.md)
for the complete definitions.

## Post-incident review template

```text
Title / incident ID / severity:
Date and duration:
Authors and reviewers:

Summary:
Customer impact (requests, functions, duration):
Timeline (link or copy final incident timeline):

Root cause:
Contributing factors:
Detection: how detected, which signal was missing or delayed, if any:

What went well:
What went poorly:
Mitigation and recovery actions:

Corrective actions
Priority | Action | Owner | Due date | Status | Prevention expected
---------|--------|-------|----------|--------|--------------------
         |        |       |          |        |

SLO/error-budget impact:
Lessons and follow-up review date:
```

The review is blameless and focused on improving detection, recovery, and
prevention. It does not create alerting, notification automation, or
infrastructure changes by itself; approved follow-up work is tracked
separately.
