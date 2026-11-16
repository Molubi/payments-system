# Incident Runbook

## Service

Service Name:

Owner:

Repository:

SLO:

---

## Alert

Alert Name:

Severity:

Dashboard:

---

## Symptoms

- What operators see
- Error messages
- Metrics affected

---

## Customer Impact

- Who is impacted
- What functionality is degraded

---

## Diagnosis

### Check Application

```bash
docker compose logs app
```

### Check Provider

```bash
docker compose logs provider
```

### Check Database

```bash
docker compose logs db
```

### Check Metrics

Prometheus:

http://localhost:9090

Grafana:

http://localhost:3000
```

---

## Mitigation

Immediate actions:

- Restart service
- Refresh credentials
- Failover to backup provider

---

## Root Cause

Describe cause.

---

## Permanent Fix

Describe the corrective action.

---

## Validation

How to verify service recovery.

---

## Escalation

Primary Team:

Secondary Team:

Contact: