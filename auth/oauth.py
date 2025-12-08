import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

class OAuth:
    def __init__(self, client_secret_file):
        self.client_secret_file = client_secret_file
        self.creds = None

    def authorize(self):
        flow = InstalledAppFlow.from_client_secrets_file(
            self.client_secret_file,
            ['https://www.googleapis.com/auth/calendar']
        )
        self.creds = flow.run_local_server(port=0)
        return self.creds.token
