@app.get("/payments/{payment_id}")
def get_payment(payment_id: str):

    db = SessionLocal()

    payment = db.get(
        PaymentStatus,
        payment_id
    )

    if not payment:
        raise HTTPException(
            status_code=404,
            detail="Not found"
        )

    return {
        "paymentId": payment.payment_id,
        "status": payment.status,
        "updatedAt": payment.updated_at
    }