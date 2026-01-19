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
        payload = {"grant_type": "client_credentials"}

        response = requests.post(
            AUTH_URL,
            auth=HTTPBasicAuth(self.username, self.password),
            json=payload,
            headers={"Content-Type": "application/json"},
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        self._update_tokens(response.json())

    def refresh(self):
        # If no refresh token, re-authenticate
        if not self.refresh_token:
            print("⚠️ No refresh token, re-authenticating")
            self.authenticate()
            return

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }

        response = requests.post(
            AUTH_URL,
            auth=HTTPBasicAuth(self.username, self.password),
            json=payload,
            headers={"Content-Type": "application/json"},
            verify=VERIFY_SSL
        )
        response.raise_for_status()
        self._update_tokens(response.json())

    def _update_tokens(self, data):
        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")  # may be None
        expires_in = data.get("expires_in", 3600)

        # refresh 5 minutes before expiry
        self.expiry_time = time.time() + expires_in - 300

    def get_access_token(self):
        if time.time() >= self.expiry_time:
            print("🔄 Token expiring – refreshing")
            try:
                self.refresh()
            except Exception as e:
                print("❌ Refresh failed, re-authenticating:", e)
                self.authenticate()

        return self.access_token
