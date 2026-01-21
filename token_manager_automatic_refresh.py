import time
import requests
from requests.auth import HTTPBasicAuth
from configuration import AUTH_URL, VERIFY_SSL


class TokenManager:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.expiry_time = 0
        self.authenticate()

    def authenticate(self):
        response = requests.post(
            AUTH_URL,
            auth=HTTPBasicAuth(self.username, self.password),
            json={"grant_type": "client_credentials"},
            headers={"Content-Type": "application/json"},
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        self._update_tokens(response.json())

    def refresh(self):
        if not self.refresh_token:
            self.authenticate()
            return

        response = requests.post(
            AUTH_URL,
            auth=HTTPBasicAuth(self.username, self.password),
            json={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token
            },
            headers={"Content-Type": "application/json"},
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        self._update_tokens(response.json())

    def _update_tokens(self, data):
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token")
        self.expiry_time = time.time() + data.get("expires_in", 3600) - 300

    def get_access_token(self):
        if time.time() >= self.expiry_time:
            self.refresh()
        return self.access_token
