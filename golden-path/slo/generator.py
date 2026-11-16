from pathlib import Path

OUTPUT_DIR = Path(
    "golden-path/slo/output"
)

spec = {
    "service": "payment-webhook",
    "sli": {
        "good_metric": 'http_requests_total{status="2xx"}',
        "total_metric": "http_requests_total"
    },
    "slo": {
        "target": 99.9,
        "window": "30d"
    }
}


def generate_recording_rule(spec):

    service = spec["service"]

    good = spec["sli"]["good_metric"]

    total = spec["sli"]["total_metric"]

    return f"""
groups:
- name: {service}-slo

  rules:

  - record: slo:availability_ratio

    expr: |
      sum(rate({good}[5m]))
      /
      sum(rate({total}[5m]))
"""


def generate_alerts(spec):

    service = spec["service"]

    return f"""
groups:
- name: {service}-alerts

  rules:

  - alert: HighErrorBudgetBurn

    expr: slo:availability_ratio < 0.999

    for: 5m

    labels:
      severity: critical

    annotations:

      summary: "{service} error budget burn"

      description: |
        Service is burning error budget too fast.

  - alert: SlowErrorBudgetBurn

    expr: slo:availability_ratio < 0.9995

    for: 1h

    labels:
      severity: warning

    annotations:

      summary: "{service} slow burn"

      description: |
        Service is consuming error budget.
"""


def write_file(path, content):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(path, "w") as file:
        file.write(content)


def main():

    recording_rules = (
        generate_recording_rule(spec)
    )

    alerts = (
        generate_alerts(spec)
    )

    write_file(
        OUTPUT_DIR / "recording-rules.yaml",
        recording_rules
    )

    write_file(
        OUTPUT_DIR / "alert-rules.yaml",
        alerts
    )

    print(
        "Generated SLO rules successfully."
    )


if __name__ == "__main__":
    main()