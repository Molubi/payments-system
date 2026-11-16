def test_invalid_signature():

    response = client.post(
        "/webhooks/payment-status",
        json={}
    )

    assert response.status_code == 401