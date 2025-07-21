import requests
from google.oauth2 import service_account
import google.auth.transport.requests
import json

# Path to your service account key file
SERVICE_ACCOUNT_FILE = 'service-account.json'
SCOPES = [
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive'
]

# Authenticate and get an access token
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
auth_req = google.auth.transport.requests.Request()
credentials.refresh(auth_req)
access_token = credentials.token
