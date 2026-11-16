import requests

token = "valid-token"

BASE_URL = "http://provider:8001"


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

    return response.json()