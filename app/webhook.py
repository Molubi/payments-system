import hmac
import hashlib

WEBHOOK_SECRET = "super-secret"


def verify_signature(payload: bytes, signature: str):

    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)