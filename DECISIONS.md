# Architecture & Engineering Decisions (`DECISIONS.md`)

## 1. Key Decisions & Trade-Offs

* **SLO-as-Code Generator (`golden-path/slo/generator.py`):** Instead of hand-writing verbose PromQL alert rules per service, product teams define a compact YAML spec (`specs/payment-webhook.yaml`). A lightweight Python generator compiles it into multi-window, multi-burn-rate Prometheus alerts (Google SRE Workbook standard: `14.4x` burn over `1h/5m` for critical paging, `6x` burn over `6h/30m` for tickets).
* **Telemetry Cost Guardrails First:** Observability bills scale with custom metric cardinality and trace volume. We standardized low-cardinality route templates (`/payments/{id}` instead of `/payments/12345`), capped log verbosity at `INFO`, and enforced error-biased trace sampling.
* **Terraform Tag Enforcement via Input Validation:** Rather than relying on manual PR reviews to catch missing FinOps tags, `terraform/modules/payment-service/variables.tf` enforces non-empty `owner`, `service`, `environment`, and `cost_centre` inputs via Terraform `validation` blocks.
* **What Was Rejected:**
  * *Full Kubernetes (AKS) cluster for a single small service:* Rejected due to high baseline control-plane/node overhead and operational complexity compared to Azure Container Apps / managed PaaS.
  * *Distributed message broker (Kafka/Service Bus) in v1:* Rejected to keep the local stack self-contained and fast to run; PostgreSQL transactional persistence + provider webhook retries handle durability for `15–150 req/s`.

---

## 2. Approach to the Service Build

* **What We Kept Small:** Built a focused two-endpoint FastAPI service (`POST /webhooks/payment-status` and `GET /payments/{id}`) backed by PostgreSQL, paired with a lightweight `fake_provider` service capable of simulating expired credentials, latency spikes, and `5xx` failures on demand.
* **What We Chose Not to Build:** Full OAuth2/OIDC UI portals, multi-currency ledger reconciliation engines, or multi-region active-active failover. The service exists to prove real telemetry, SLO burn-rate math, and credential expiry handling under load.

---

## 3. Where AI Was Used & What Was Changed

* **Scaffolding & Boilerplate:** Used AI to draft initial FastAPI route structures, Pydantic schemas, k6 load script (`load.js`), and Markdown templates for `README.md` and `DECISIONS.md`.
* **Debugging & Refactoring:** Used AI assistance when structuring the Terraform module (`terraform/modules/payment-service`). Initially, provider blocks were duplicated across `variables.tf` and `versions.tf`, and root outputs referenced internal module resources directly.
* **What Was Changed / Rejected:**
  * Stripped `provider "azurerm"` out of the child module so the module remains reusable across subscriptions and environments.
  * Added explicit `validation` blocks on cost tags (`owner`, `service`, `environment`, `cost_centre`) so invalid configurations fail immediately at `terraform validate`.
  * Simplified Prometheus alert expressions to match exact metric names emitted by the FastAPI instrumentation.

---

## 4. Questions for Product & Assumptions Made

If collaborating with the Payments Product Manager, we would confirm:
1. *What is the exact SLA commitment to downstream Finance reporting when a webhook is delayed >1s?*
2. *Should webhook ingestion queue callbacks locally during an upstream provider outage, or return `503` so the provider retries?*
3. *What is the compliance retention requirement for raw webhook payloads (`30 days` vs `7 years`)?*

**Assumptions Documented:**
* **Error Budget Policy:** Exhausting the `0.1%` 30-day error budget triggers a release freeze on non-reliability changes.
* **Graceful Degradation:** When the provider API rejects an expired token (`401`), the service triggers token renewal, avoids tight retry loops, and relies on provider webhook retries while alerting on-call.
* **Traffic Profile:** `15 req/s` steady state (`~39M requests/month`), bursting `10x` to `150 req/s` during month-end billing (25th from 08:00).

---

## 5. Rough Monthly Cost Estimate (Azure + Telemetry)

Assumptions: South Africa North / West Europe pricing, `~42M` webhook requests/month (`15 req/s` average + month-end peaks), `99.9%` availability target.

| Component | Azure / Platform Service | Sizing & Assumptions | Est. Monthly Cost (USD) |
| :--- | :--- | :--- | :---: |
| **Compute** | Azure Container Apps (Consumption/Dedicated) | Min 2 replicas (0.5 vCPU, 1 GiB) steady; autoscales to 8 replicas on 25th | ~$55 |
| **Database** | Azure Database for PostgreSQL Flexible Server | Burstable B2s (2 vCPU, 4 GiB RAM), 32 GiB SSD, automated backups | ~$45 |
| **Networking / Edge** | Azure Front Door Standard + WAF | ~42M requests, ~25 GB outbound data transfer, managed WAF rules | ~$50 |
| **Metrics & Alerts** | Azure Monitor Managed Prometheus | ~15k active time series (low-cardinality labels enforced), 30s scrape | ~$20 |
| **Logs & Traces** | Log Analytics + Application Insights | ~15 GB/month (`INFO` logs + 10% trace sampling, 30-day retention) | ~$40 |
| **Secrets & Registry** | Azure Key Vault + ACR Basic | Secret rotation + container image storage | ~$10 |
| **Total Estimated Run Rate** | | | **~$220 / month** |

*Cost control impact:* Without label cardinality limits and trace sampling (`100%` ingestion), telemetry costs alone at `42M` requests/month would exceed **$350–$500/month**—more than double the compute and database footprint.

---

## 6. Golden Path Components Not Built (Design Proposals)

### A. Pipeline Template (CI/CD & Policy Gate)
To standardize safe delivery across product teams, I would provide a reusable **Azure Pipelines** template (`golden-path/pipelines/service-ci-cd.yaml`) referenced via `extends`:
1. **Build & Unit Test:** Run `pytest`, lint (`ruff`), and build an immutable, non-root container image tagged with Git SHA.
2. **Security & IaC Scanning:** Run **Trivy** on the container image (blocking on `CRITICAL`/`HIGH` CVEs) and **Checkov/tfsec** on Terraform modules.
3. **Policy Gate (OPA / Conftest):** Evaluate Terraform plan JSON and Kubernetes/Container App manifests against Open Policy Agent rules—blocking deployments missing mandatory cost tags (`owner`, `service`, `environment`, `cost_centre`), public database endpoints, or missing health probes.
4. **Progressive Delivery:** Deploy to `staging`, run automated smoke + synthetic webhook verification, then roll out to `prod` via canary traffic shifting (`10% -> 50% -> 100%`) with automatic rollback if the fast-burn SLO alert triggers during rollout.

### B. Edge & Security (TLS, WAF, Rate Limiting & Origin Lock-Down)
To safely expose the webhook receiver to external payment providers without exposing the origin directly:
1. **Edge Entrypoint:** Deploy **Azure Front Door** (or Cloudflare) in IaC with managed TLS 1.2+ certificates, automatic renewal, and an Azure Monitor alert firing **30 days** prior to certificate expiration.
2. **WAF & Rate Limiting:** Attach a Web Application Firewall policy in `Prevention` mode with OWASP core rule sets, plus custom rate-limiting rules on `POST /webhooks/payment-status` (`300 req/s` burst ceiling per source) and strict IP/ASN allowlisting for known payment provider CIDR blocks.
3. **Origin Lock-Down:** Configure the origin (Azure Container Apps / App Service) with Private Link or origin-access restrictions validating the `X-Azure-FDID` header, ensuring attackers cannot bypass the WAF by hitting the origin hostname directly.
4. **Local Equivalent:** Locally, this pattern is replicated using **Caddy** or **NGINX** as a reverse proxy terminating local TLS and enforcing `limit_req` rate limits in front of the FastAPI container.

---

## 7. Known Gaps & What I Would Do With One More Sprint

### Known Gaps / Shortcuts Taken for 3-Day Timebox
* **Local Observability Stack:** Focused on Prometheus metrics and SLO burn-rate alerts locally; a full OpenTelemetry Collector + Tempo/Jaeger + Grafana dashboard bundle was kept out of Docker Compose to keep local startup fast and lightweight.
* **Database Migrations:** Schema initialization runs at app startup rather than via versioned **Alembic** migrations.
* **Synthetic Continuous Probing:** Load testing uses on-demand `k6` runs rather than a continuously running synthetic canary container.

### Next Sprint Priorities
1. **Automated Secret Rotation:** Integrate Azure Key Vault event triggers so provider API credentials rotate automatically before expiration without human intervention.
2. **OpenTelemetry Collector Sidecar:** Add an OTel Collector container to `docker-compose.yml` demonstrating live tail-based sampling and trace-to-log correlation in Grafana.
3. **Alembic Migrations & Dead-Letter Queue:** Add versioned schema migrations and a PostgreSQL-backed dead-letter table for malformed or unverified webhook payloads requiring manual replay.

---

## 8. Post-Baseline Upgrade: CI & FinOps Policy Gate (`.github/workflows/golden-path-ci.yml`)

Added an automated GitHub Actions pipeline that enforces Golden Path standards on every commit:
* **Automated Test Gate:** Runs `pytest` across webhook verification and payment status endpoints.
* **SLO-as-Code Drift Detection:** Re-runs `golden-path/slo/generator.py` and fails if generated Prometheus recording/alert rules drift from `specs/payment-webhook.yaml`.
* **IaC & FinOps Policy Gate:** Runs `terraform fmt -check`, `terraform validate`, and a policy check verifying that `owner`, `service`, `environment`, and `cost_centre` tags are declared before any deployment can proceed.
