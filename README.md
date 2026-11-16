# Payments Golden Path & Payment Status Webhook Receiver

This repository contains the **SRE Golden Path** reusable platform kit and the reference onboarding of the **Payment Status Webhook Receiver** (`payments-system`).

---

## 1. Quickstart: Run Everything Locally

All components (FastAPI service, PostgreSQL, Fake Payment Provider, and Prometheus) run locally via Docker Compose.

### Start the stack
```bash
docker compose up --build -d
```

### Verify endpoints
* **Webhook Receiver API & Swagger UI:** `http://localhost:8000/docs`
* **Fake Payment Provider:** `http://localhost:8001/docs` (check your `docker-compose.yml` port mapping)
* **Prometheus UI & Alerts:** `http://localhost:9090`

### Run automated tests & load traffic
```bash
# Run unit & integration tests
pytest

# Run k6 load simulation (steady 15 req/s baseline)
k6 run load.js
```

---

## 2. How a Product Team Adopts This Golden Path

Any product team can onboard a new service in four steps without building observability, alerting, or cloud governance from scratch:

### Step 1: Define Your SLO (`golden-path/slo/`)
1. Copy `golden-path/slo/specs/payment-webhook.yaml` to `golden-path/slo/specs/<your-service>.yaml`.
2. Set your service name, target availability/latency (`99.9%` within `1000ms`), and rolling window (`30d`).
3. Run the generator to produce Prometheus recording rules and multi-window burn-rate alerts:
   ```bash
   python golden-path/slo/generator.py
   ```
4. Mount or load the generated `recording-rules.yaml` and `alert-rules.yaml` into Prometheus.

### Step 2: Instrument Telemetry (`golden-path/telemetry/standard.md`)
Follow `golden-path/telemetry/standard.md` to emit OpenTelemetry/Prometheus signals with enforced cost controls:
* **Naming & Labels:** Use standard `http_request_duration_seconds` and `service`, `environment`, `status_code`, and `route` labels.
* **Cardinality Guardrails:** Never put unbounded IDs (`payment_id`, `user_id`, raw paths) in metric labels.
* **Trace Sampling & Log Levels:** Default to `INFO` logs in production and head-based tail/probabilistic trace sampling (`10%` steady-state, `100%` on `5xx`/errors) to control ingestion costs.

### Step 3: Provision Azure Infrastructure (`terraform/modules/payment-service/`)
Reference the reusable Terraform module in your service repository. The module enforces mandatory FinOps tags (`owner`, `service`, `environment`, `cost_centre`) at validation time:

```hcl
module "my_service" {
  source = "../../modules/payment-service"

  owner       = "payments-team"
  service     = "payment-webhook"
  environment = "prod"
  cost_centre = "CC-FIN-01"
}
```

### Step 4: Create Your Service Runbook (`runbooks/`)
Copy `runbooks/template.md` to `runbooks/<failure-mode>.md` and document symptoms, immediate mitigation steps, and root-cause remediation before going live.

---

## 3. Reproducing the Expired Credential Incident

To test end-to-end resilience, alerting, and incident response:

1. **Trigger credential expiry** on the fake payment provider (via its admin/control toggle in `fake_provider` or during load testing).
2. **Observe service mitigation:** The webhook receiver detects `401/403` responses from the provider API, stops hammering the upstream dependency with futile retries, and automatically attempts token renewal / degrades gracefully while preserving incoming webhook durability.
3. **Observe Prometheus alert:** Check `http://localhost:9090/alerts` to see the fast-burn SLO alert fire as error budget consumption spikes above the `14.4x` (1-hour) burn threshold.
4. **Follow the runbook:** Execute the mitigation and token rotation procedure documented in `runbooks/expired-provider-token.md`.

---

## 4. Product Team Assumptions & Error Budget Policy

Because the ticket left operational policy open, the following defaults apply unless overridden by Product leadership:
* **Error Budget Exhaustion (`0.1%` / ~43.2 mins over 30 days):** When the 30-day error budget is exhausted, non-critical feature releases freeze automatically. Engineering capacity shifts to reliability and backlog fixes until the rolling window recovers above `10%` remaining budget.
* **Webhook Replay & Idempotency:** Payment providers retry failed webhooks with exponential backoff. Duplicate `event_id` callbacks are safely deduplicated in PostgreSQL without corrupting ledger state.
* **Month-End Peak Sizing (`150 req/s` on the 25th from 08:00):** Infrastructure autoscaling and database connection pools are sized for a `10x` traffic surge (`15 req/s` baseline to `150 req/s` peak) with `2x` headroom (`300 req/s`).
