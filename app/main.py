from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import Base, PaymentStatus
from app.schemas import PaymentWebhook
from app.webhook import verify_signature
from app.provider_client import get_provider_payment
from app.wait_for_db import wait_for_db
from prometheus_fastapi_instrumentator import Instrumentator


# Create database tables
wait_for_db()
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Payment Webhook Service"
)

Instrumentator().instrument(app).expose(app)

@app.get("/")
def root():
    return {
        "service": "payment-webhook-service",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/webhooks/payment-status")
async def receive_payment_status(request: Request):

    body = await request.body()

    signature = request.headers.get("X-Signature")

    if not signature:
        raise HTTPException(
            status_code=401,
            detail="Missing signature"
        )

    if not verify_signature(body, signature):
        raise HTTPException(
            status_code=401,
            detail="Invalid signature"
        )

    payload = PaymentWebhook.model_validate_json(body)

    try:
        provider_payment = get_provider_payment(
            payload.paymentId
        )

    except Exception as ex:
        raise HTTPException(
            status_code=503,
            detail=f"Provider unavailable: {str(ex)}"
        )

    db: Session = SessionLocal()

    try:

        payment = PaymentStatus(
            payment_id=payload.paymentId,
            status=provider_payment["status"],
            updated_at=datetime.utcnow()
        )

        db.merge(payment)

        db.commit()

    finally:
        db.close()

    return {
        "status": "recorded",
        "paymentId": payload.paymentId
    }


@app.get("/payments/{payment_id}")
def get_payment(payment_id: str):

    db: Session = SessionLocal()

    try:

        payment = db.get(
            PaymentStatus,
            payment_id
        )

        if not payment:
            raise HTTPException(
                status_code=404,
                detail="Payment not found"
            )

        return {
            "paymentId": payment.payment_id,
            "status": payment.status,
            "updatedAt": payment.updated_at
        }

    finally:
        db.close()