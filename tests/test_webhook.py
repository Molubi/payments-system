import hmac
import hashlib
from app.webhook import verify_signature, WEBHOOK_SECRET


def test_verify_signature_valid():
    payload = b'{"paymentId":"pay_123","status":"SUCCEEDED"}'
    valid_sig = hmac.new(WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    assert verify_signature(payload, valid_sig) is True


def test_verify_signature_invalid():
    payload = b'{"paymentId":"pay_123","status":"SUCCEEDED"}'
    assert verify_signature(payload, "wrong-signature") is False
