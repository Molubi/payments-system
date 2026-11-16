from fastapi import FastAPI, HTTPException
import requests
import json
import time
import hmac
import hashlib

app = FastAPI(title="Fake Payment Provider")

# --------------------------------------------------
# Provider State
# --------------------------------------------------

provider_state = {
    "token_valid": True,
    "slow_mode": False,
    "error_mode": False,
}

WEBHOOK_SECRET = "super-secret"
WEBHOOK_URL = "http://app:8000/webhooks/payment-status"

# --------------------------------------------------
# Authentication
# --------------------------------------------------


def validate_token(token: str):

    if not provider_state["token_valid"]:
        raise HTTPException(
            status_code=401,
            detail="Token expired"
        )

    if token != "valid-token":
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


# --------------------------------------------------
# Provider API
# --------------------------------------------------


@app.get("/")
def health():
    return {
        "service": "fake-provider",
        "status": "healthy"
    }


@app.get("/provider/payments/{payment_id}")
def get_payment(payment_id: str, token: str):

    validate_token(token)

    if provider_state["slow_mode"]:
        time.sleep(5)

    if provider_state["error_mode"]:
        raise HTTPException(
            status_code=500,
            detail="Provider error"
        )

    return {
        "paymentId": payment_id,
        "status": "SUCCESS"
    }


# --------------------------------------------------
# Token Endpoint
# --------------------------------------------------


@app.post("/provider/token")
def issue_token():

    provider_state["token_valid"] = True

    return {
        "token": "valid-token",
        "expiresIn": 3600
    }


# --------------------------------------------------
# Webhook Sender
# --------------------------------------------------


@app.post("/provider/send-webhook")
def send_webhook():

    payload = {
        "paymentId": "PAY123",
        "status": "SUCCESS"
    }

    body = json.dumps(payload).encode()

    signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    try:

        response = requests.post(
            WEBHOOK_URL,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Signature": signature
            },
            timeout=10
        )

        return {
            "message": "Webhook sent",
            "statusCode": response.status_code
        }

    except Exception as ex:

        raise HTTPException(
            status_code=500,
            detail=f"Webhook delivery failed: {str(ex)}"
        )


# --------------------------------------------------
# Admin Controls
# --------------------------------------------------


@app.post("/admin/expire-token")
def expire_token():

    provider_state["token_valid"] = False

    return {
        "message": "Token expired"
    }


@app.post("/admin/restore-token")
def restore_token():

    provider_state["token_valid"] = True

    return {
        "message": "Token restored"
    }


@app.post("/admin/slow")
def enable_slow_mode():

    provider_state["slow_mode"] = True

    return {
        "message": "Slow mode enabled"
    }


@app.post("/admin/normal")
def disable_slow_mode():

    provider_state["slow_mode"] = False

    return {
        "message": "Slow mode disabled"
    }


@app.post("/admin/error")
def enable_error_mode():

    provider_state["error_mode"] = True

    return {
        "message": "Error mode enabled"
    }


@app.post("/admin/recover")
def disable_error_mode():

    provider_state["error_mode"] = False

    return {
        "message": "Provider recovered"
    }


# --------------------------------------------------
# View Current State
# --------------------------------------------------


@app.get("/admin/state")
def get_state():

    return provider_state