from pydantic import BaseModel

class PaymentWebhook(BaseModel):
    paymentId: str
    status: str