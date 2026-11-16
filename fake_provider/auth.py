from fastapi import HTTPException
from .state import provider_state


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