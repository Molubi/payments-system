# Expired Provider Credential

## Service

payment-webhook-service

---

## Alert

ProviderAuthenticationFailure

Severity: Warning

---

## Symptoms

- Provider API returns HTTP 401
- Payment status updates stop
- Failed provider requests increase

---

## Customer Impact

Webhook processing may fail.

Payment status data may become stale.

---

## Diagnosis

Verify:

```bash
POST /admin/expire-token
```

Check provider logs.

Check Prometheus metric:

```promql
http_requests_total
```

---

## Mitigation

Refresh credential:

```http
POST /provider/token
```

Verify webhook processing resumes.

---

## Root Cause

Expired API credential.

---

## Permanent Fix

Enable proactive refresh before expiry.

Increase monitoring on authentication failures.

---

## Validation

Webhooks process successfully.

No further 401 responses.