import json
import hmac
import hashlib
import requests

WEBHOOK_SECRET = "super-secret"


def send_webhook():

    payload = {
        "paymentId": "123",
        "status": "SUCCESS"
    }

    body = json.dumps(payload).encode()

    signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    response = requests.post(
        "http://app:8000/webhooks/payment-status",
        data=body,
        headers={
            "X-Signature": signature
        }
    )

    return response.status_code