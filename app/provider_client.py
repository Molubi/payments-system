import requests

BASE_URL = "http://provider:8001"

token = "valid-token"


def refresh_token():
    global token

    response = requests.post(
        f"{BASE_URL}/provider/token"
    )

    token = response.json()["token"]

    return token


def get_provider_payment(payment_id):

    global token

    response = requests.get(
        f"{BASE_URL}/provider/payments/{payment_id}",
        params={"token": token}
    )

    if response.status_code == 401:

        refresh_token()

        response = requests.get(
            f"{BASE_URL}/provider/payments/{payment_id}",
            params={"token": token}
        )

    response.raise_for_status()

    return response.json()