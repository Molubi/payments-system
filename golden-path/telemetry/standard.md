# Telemetry Standard

## Purpose

Every service onboarded to the golden path must emit metrics, traces and logs using these standards.

---

# Metrics

## Naming

Pattern:

service_<metric_name>

Examples:

service_requests_total

service_request_duration_seconds

service_failures_total

provider_auth_failures_total

---

## Required Labels

service

environment

endpoint

status_code

---

## Forbidden Labels

payment_id

user_id

email

request_id

token

Reason:

High cardinality increases observability cost.

---

# Tracing

OpenTelemetry required.

Every incoming webhook request creates a trace.

Required attributes:

service.name

endpoint

http.method

http.status_code

---

# Sampling

Default trace sampling:

5%

Errors:

100%

Reason:

Reduce observability spend while retaining incident visibility.

---

# Logging

Format:

JSON structured logs

Example:

{
  "event": "provider_auth_failure",
  "status": 401
}

---

# Log Levels

Production:

INFO

Development:

DEBUG

Error conditions:

ERROR

---

# Retention

Metrics:
30 days

Traces:
3 days

Logs:
7 days

---

# Cost Controls

No high-cardinality labels.

Error sampling only.

Logs retained for 7 days by default.

DEBUG disabled in production.