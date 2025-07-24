from googleapiclient.discovery import build
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = "slides/service-account-data.json" # 👈 replace with actual path
SCOPES = ["https://www.googleapis.com/auth/drive"]

credentials = service_account.Credentials.from_service_account_file(
SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

service = build("drive", "v3", credentials=credentials)

folder_id = "1IfLkxDzlHoPvV5wZkie2qpvNAO9td0yN"

try:
    folder = service.files().get(fileId=folder_id, fields="id, name").execute()
    print("✅ Folder is accessible by the service account:")
    print("📁 Folder name:", folder["name"])
except Exception as e:
    print("❌ Service account cannot access this folder.")
    print("Error:", e)
