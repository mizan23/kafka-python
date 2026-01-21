import requests
from requests.auth import HTTPBasicAuth
from configuration import REVOKE_URL, VERIFY_SSL, USERNAME, PASSWORD


def revoke_token(access_token):
    """
    Revoke NSP access token (mandatory clean logout)
    """
    response = requests.post(
        REVOKE_URL,
        auth=HTTPBasicAuth(USERNAME, PASSWORD),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "token": access_token,
            "token_type_hint": "token",
        },
        verify=VERIFY_SSL
    )

    response.raise_for_status()
    print("🔒 Token revoked")
