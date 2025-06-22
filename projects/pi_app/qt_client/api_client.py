# api_client.py

import requests
import jwt # PyJWT
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

class ApiClient(QObject):
    # Signals for communication with the main application
    login_success = pyqtSignal(str, str, str) # identity, role, message
    login_failure = pyqtSignal(str) # error_message
    logout_success = pyqtSignal()
    api_error = pyqtSignal(str) # general API error message
    token_refresh_needed = pyqtSignal() # Signal to trigger refresh

    def __init__(self, base_url, parent=None):
        super().__init__(parent)
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.current_user_identity = None
        self.current_user_role = None

        # Timer for proactive token refreshing
        self.token_refresh_timer = QTimer(self)
        self.token_refresh_timer.timeout.connect(self._refresh_access_token_internal)

    def _set_tokens(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token
        
        if access_token:
            # Decode access token to get identity and role
            # IMPORTANT: On client-side, only decode for claims, do NOT verify signature
            # Signature verification happens on the server.
            decoded_token = jwt.decode(self.access_token, options={"verify_signature": False})
            self.current_user_identity = decoded_token.get("sub")
            self.current_user_role = decoded_token.get("role")
            
            # Start refresh timer (e.g., 1 minute before access token expires)
            # This assumes access tokens expire in 15 minutes (900 seconds)
            # Adjust based on actual JWT_ACCESS_TOKEN_EXPIRES from backend config
            self.token_refresh_timer.start(14 * 60 * 1000) # 14 minutes
        else:
            self.current_user_identity = None
            self.current_user_role = None
            self.token_refresh_timer.stop()

    def _request(self, method, endpoint, json_data=None, headers=None, timeout=5, retry_on_refresh=True):
        """Internal helper for making authenticated requests."""
        full_url = f"{self.base_url}{endpoint}"
        
        if headers is None:
            headers = {}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"

        try:
            response = requests.request(method, full_url, json=json_data, headers=headers, timeout=timeout)
            response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
            return response
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401 and retry_on_refresh and self.refresh_token:
                # Access token expired, try to refresh
                self.token_refresh_needed.emit() # Signal to main app that refresh is happening
                if self._refresh_access_token_internal():
                    # Retry the original request with the new token
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    response = requests.request(method, full_url, json=json_data, headers=headers, timeout=timeout)
                    response.raise_for_status()
                    return response
                else:
                    self.api_error.emit("Failed to refresh token. Please log in again.")
                    self.logout()
                    raise e # Re-raise to propagate error
            self.api_error.emit(f"API Error ({e.response.status_code}): {e.response.text}")
            raise e # Re-raise other HTTP errors
        except requests.exceptions.RequestException as e:
            self.api_error.emit(f"Network Error: {e}")
            raise e # Re-raise network errors

    # Public API methods
    def get(self, endpoint, headers=None, timeout=5):
        return self._request("GET", endpoint, headers=headers, timeout=timeout)

    def post(self, endpoint, json_data=None, headers=None, timeout=5):
        return self._request("POST", endpoint, json_data=json_data, headers=headers, timeout=timeout)

    def put(self, endpoint, json_data=None, headers=None, timeout=5):
        return self._request("PUT", endpoint, json_data=json_data, headers=headers, timeout=timeout)

    def delete(self, endpoint, headers=None, timeout=5):
        return self._request("DELETE", endpoint, headers=headers, timeout=timeout)

    # Authentication methods
    def login(self, email, password):
        try:
            response = requests.post(f"{self.base_url}/api/auth/login", json={"email": email, "password": password}, timeout=5)
            response.raise_for_status()
            data = response.json()
            self._set_tokens(data.get("access_token"), data.get("refresh_token"))
            self.login_success.emit(self.current_user_identity, self.current_user_role, "Login successful.")
        except requests.exceptions.RequestException as e:
            self.login_failure.emit(f"Login failed: {e}")

    def register(self, email, password):
        try:
            response = requests.post(f"{self.base_url}/api/auth/register", json={"email": email, "password": password}, timeout=5)
            response.raise_for_status()
            self.login_success.emit(None, None, f"Registration successful for {email}. Please log in.") # No tokens on register
        except requests.exceptions.RequestException as e:
            self.login_failure.emit(f"Registration failed: {e}")

    def card_login(self, card_id):
        try:
            response = requests.post(f"{self.base_url}/api/auth/card_login", json={"card_id": card_id}, timeout=5)
            response.raise_for_status()
            data = response.json()
            self._set_tokens(data.get("access_token"), data.get("refresh_token"))
            self.login_success.emit(self.current_user_identity, self.current_user_role, "Card login successful.")
        except requests.exceptions.RequestException as e:
            self.login_failure.emit(f"Card login failed: {e}")

    def guest_login(self):
        """Logs in as a temporary guest user."""
        try:
            response = requests.post(f"{self.base_url}/api/auth/guest_login", timeout=5)
            response.raise_for_status()
            data = response.json()
            self._set_tokens(data.get("access_token"), data.get("refresh_token"))
            self.login_success.emit(self.current_user_identity, self.current_user_role, "Logged in as guest.")
        except requests.exceptions.RequestException as e:
            self.login_failure.emit(f"Guest login failed: {e}")
    def _refresh_access_token_internal(self):
        """Internal method to refresh access token. Returns True on success, False otherwise."""
        if not self.refresh_token:
            return False
        try:
            response = requests.post(f"{self.base_url}/api/auth/refresh", headers={"Authorization": f"Bearer {self.refresh_token}"}, timeout=5)
            response.raise_for_status()
            data = response.json()
            self._set_tokens(data.get("access_token"), self.refresh_token) # Refresh token remains the same
            return True
        except requests.exceptions.RequestException as e:
            self.api_error.emit(f"Failed to refresh token: {e}")
            self.logout()
            return False

    def logout(self):
        """Clears tokens and logs out the user."""
        self._set_tokens(None, None)
        self.logout_success.emit()