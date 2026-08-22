# SecureDataOps service-level objectives

These objectives apply to the production backend behind
`securedataops-alb` in `us-east-1`. They use existing Amazon CloudWatch
metrics and require no application instrumentation or new monitoring service.
The `/health` endpoint remains the ECS container health check; the existing
`UnHealthyHostCount` dashboard widget is a supporting diagnostic signal, not
an SLI.

| SLI | CloudWatch measurement | Target and window | Failure definition |
| --- | --- | --- | --- |
| Availability | `AWS/ApplicationELB`: `RequestCount`, `HTTPCode_Target_5XX_Count`, and `HTTPCode_ELB_5XX_Count`, dimensioned by backend load balancer `app/securedataops-alb/a1b68a761929383a`. Calculate `1 - (target 5xx + ELB 5xx) / RequestCount`. | At least **99.5%** over a rolling 30 days. Periods with zero requests are excluded. | Any request counted by either 5xx metric. Client 4xx responses are excluded; backend 503 responses count as failures. |
| Request latency | `AWS/ApplicationELB`: `TargetResponseTime` extended statistic `p95`, with the same backend load-balancer dimension. Evaluate in 5-minute periods only when `RequestCount` is greater than zero. The SLI is compliant periods divided by evaluated periods. | At least **95%** of evaluated 5-minute periods have p95 latency at or below **1 second** over a rolling 30 days. | An evaluated 5-minute period whose p95 `TargetResponseTime` exceeds 1 second. |

The existing CloudWatch dashboard already shows backend request count, target
5xx count, average target response time, and unhealthy targets. For the SLO
calculation, query the same backend ALB metrics with the statistics above and
include `HTTPCode_ELB_5XX_Count` so load-balancer-generated 5xx responses are
not missed.

## Error budgets

The 99.5% availability SLO permits 0.5% failed requests in the rolling 30-day
window. Expressed as continuous time, that is approximately **3 hours 36
minutes** (`30 days x 0.5%`); the request-based SLI remains the source of
truth for actual budget consumption.

- **Healthy budget:** normal releases may proceed.
- **Reduced budget:** use increased caution and monitor changes closely.
- **Exhausted budget:** prioritize reliability work and avoid unnecessary
  risky changes until the rolling window recovers.

Latency has a separate compliance budget: up to 5% of evaluated five-minute
periods may exceed the p95 one-second target. This is a latency-compliance
allowance, not downtime, and must not be converted into an availability error
budget.

These are initial targets for a small single-task ECS service and should be
reviewed after at least one full 30-day production measurement window.
