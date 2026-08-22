# SecureDataOps DPDP engineering controls

This is an engineering inventory and control map, not legal advice or a claim
of compliance. It covers the application as implemented, not future product
features or external systems.

## Data inventory and purpose

| Data element | Storage | Purpose evidenced by the application | Notes |
| --- | --- | --- | --- |
| Name | PostgreSQL `users.name` | Create and display a user record | Required field. |
| Email address | PostgreSQL `users.email` | Identify a user record; uniqueness check | Required, unique, indexed. |
| Phone number | PostgreSQL `users.phone` | Optional contact detail on a user record | Optional. |
| User UUID and timestamps | PostgreSQL `users.id`, `created_at`, `updated_at` | Record identity and lifecycle metadata | UUID is used in privacy audit events. |
| Request metadata | Application logs | Operational troubleshooting | Method, path, status, duration, and a UUID request ID; application logs no request bodies or personal-data values. |

The repository contains no implemented collection of passwords, government IDs,
payment data, location data, device identifiers, behavioural profiles, or
consent records. Database credentials are configuration only and must remain in
approved secret storage.

## Implemented controls

| Control | Implementation | DPDP relationship |
| --- | --- | --- |
| Authentication and self-only authorization | Access, export, correction, and erasure require an expiring HS256 bearer JWT whose `sub` is a UUID matching the requested record. Missing, malformed, expired, wrong-issuer/audience, or cross-user tokens are rejected. | Provides an application identity gate; token issuance and identity proofing are external responsibilities. |
| Access and export | `GET /api/v1/users/{user_id}` returns the authenticated subject's stored record; `GET /api/v1/users/{user_id}/export` returns the same portable JSON representation with an attachment header. | Supports the engineering side of access requests; legal procedure remains required. |
| Correction | Authenticated subject-only `PUT /api/v1/users/{user_id}` updates provided name, email, or phone fields and preserves the unique-email constraint. | Aligns with correction, completion, and updating concepts in Act section 12. |
| Erasure | Authenticated subject-only `DELETE /api/v1/users/{user_id}` physically removes the live row. | Supports erasure under section 12, subject to legal or purpose-based retention. Backup expiry is not immediate erasure. |
| Privacy audit events | Successful create, single-record access, list access, export, correction, and erasure actions emit action names and, where applicable, UUIDs only. | Supports accountability without logging field values. |
| Log safety | Request IDs are accepted only when UUID-formatted; unexpected exception messages are not logged. | Reduces user-controlled log injection and secret leakage. |
| Security baseline | Database URL comes from runtime configuration, CORS defaults to no cross-origin access, and response headers reduce browser exposure. | Supports reasonable security safeguards but does not replace assessment. |

The DPDP Act provides rights to access information, correction/erasure, and
grievance redressal. See the [DPDP Act, 2023](https://www.meity.gov.in/static/uploads/2024/02/Digital-Personal-Data-Protection-Act-2023.pdf)
(sections 11–13) and the [DPDP Rules, 2025](https://www.meity.gov.in/documents/act-and-policies/digital-personal-data-protection-rules-2025-gDOxUjMtQWa?pageTitle=Digital-Personal-Data-Protection-Rules-2025.pdf).

## Required manual and legal review

- **Token issuer and identity proofing:** configure a trusted issuer to create
  short-lived HS256 JWTs with `sub` equal to the verified user UUID, and inject
  `AUTH_JWT_SECRET`, `AUTH_JWT_ISSUER`, and `AUTH_JWT_AUDIENCE` from approved
  secret/configuration management. The API deliberately has no login, password,
  registration, or token-issuance flow.
- **Lawful basis, notice, and consent:** determine purpose, applicability,
  notice content, consent or other legal basis, and child-data obligations with
  counsel. This application does not implement consent.
- **Retention:** approve a schedule for live rows, RDS backups, audit logs, and
  export artifacts. Do not automate deletion until the schedule and legal holds
  are defined. RDS backups follow `docs/BACKUP-DR.md`.
- **Grievance and request handling:** provide a verified intake and response
  process, escalation/contact details, request tracking, and response timing.
  The API is not a verified self-service rights portal.
- **Audit operations:** protect log access, define audit-log retention, review
  events regularly, and decide whether an immutable external audit store is
  needed. The application deliberately does not log personal-data field values.
- **Security review:** restrict database network access, use TLS in production,
  inject secrets from an approved manager, set explicit production CORS origins,
  and conduct an application/security assessment.
