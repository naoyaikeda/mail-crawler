import httpx
from dotenv import load_dotenv
import os

class ExchangeAuth:
    client_id: str
    client_secret: str
    redirect_uri: str
    auth_url: str
    token_url: str

    def __init__(self):
        load_dotenv()
        self.client_id = os.getenv("EXCHANGE_CLIENT_ID")
        self.client_secret = os.getenv("EXCHANGE_CLIENT_SECRET")
        self.redirect_uri = "https://login.microsoftonline.com/common/oauth2/nativeclient"
        self.auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        self.token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    
    def get_access_token(self, auth_code: str) -> dict:
        data = {
            "code": auth_code,
            "scope":  "https://outlook.office365.com/IMAP.AccessAsUser.All offline_access",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code"
        }
        response = httpx.post(self.token_url, data=data)
        response.raise_for_status()
        return response.json()
    
    def refresh_access_token(self, refresh_token: str) -> dict:
        data = {
            "client_id": self.client_id,
            "scope":  "https://outlook.office365.com/IMAP.AccessAsUser.All offline_access",
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        response = httpx.post(self.token_url, data=data)
        response.raise_for_status()
        return response.json()


    def get_auth_url(self) -> str:
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "response_mode": "query",
            "scope": "https://outlook.office365.com/IMAP.AccessAsUser.All offline_access",
            "state": "12345"
        }
        request = httpx.Request("GET", self.auth_url, params=params)
        return str(request.url)

    def extract_auth_code(self, redirect_response: str) -> str:
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(redirect_response)
        auth_code = parse_qs(parsed_url.query).get('code', [None])[0]
        return auth_code
