import os
import hmac
import hashlib
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ci.db")

from fastapi.testclient import TestClient
from app.main import app
from app.webhook import WEBHOOK_SECRET

client = TestClient(app)


def _sign(body: bytes) -> str:
    return hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()


def test_health_and_metrics():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "http_request_duration_seconds" in metrics.text


def test_webhook_rejects_missing_or_invalid_signature():
    body = b'{"paymentId":"pay_001","status":"SUCCEEDED"}'

    res_missing = client.post("/webhooks/payment-status", content=body)
    assert res_missing.status_code == 401

    res_invalid = client.post(
        "/webhooks/payment-status",
        content=body,
        headers={"X-Signature": "bad-sig"}
    )
    assert res_invalid.status_code == 401


@patch("app.main.get_provider_payment")
def test_webhook_records_and_fetches_payment(mock_provider):
    mock_provider.return_value = {"paymentId": "pay_100", "status": "SUCCEEDED"}
    body = b'{"paymentId":"pay_100","status":"SUCCEEDED"}'

    post_res = client.post(
        "/webhooks/payment-status",
        content=body,
        headers={"X-Signature": _sign(body)}
    )
    assert post_res.status_code == 200
    assert post_res.json()["status"] == "recorded"

    get_res = client.get("/payments/pay_100")
    assert get_res.status_code == 200
    assert get_res.json()["paymentId"] == "pay_100"
    assert get_res.json()["status"] == "SUCCEEDED"


@patch("app.main.get_provider_payment", side_effect=RuntimeError("401 Expired Token"))
def test_webhook_returns_503_when_provider_rejects_expired_token(mock_provider):
    body = b'{"paymentId":"pay_999","status":"FAILED"}'

    res = client.post(
        "/webhooks/payment-status",
        content=body,
        headers={"X-Signature": _sign(body)}
    )
    assert res.status_code == 503
    assert "Provider unavailable" in res.json()["detail"]
