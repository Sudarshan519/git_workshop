from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
import os

SERVICE_ACCOUNT_FILE = "slides/service-account-data.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]

def get_drive_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES, subject='nabin@industryrockstar.ai'
    )
    return build("drive", "v3", credentials=credentials)

def create_folder_if_not_exists(service, name, parent_id):
    query = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
    results = service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
    folders = results.get("files", [])
    if folders:
        return folders[0]["id"]

    file_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": ["1IfLkxDzlHoPvV5wZkie2qpvNAO9td0yN"],
    }
    folder_id = "1IfLkxDzlHoPvV5wZkie2qpvNAO9td0yN"
    folder = service.files().get(fileId=folder_id, fields="id, name").execute()
    print("✅ Folder accessible:", folder["name"])
    file = service.files().create(body=file_metadata, fields="id").execute()
    return file.get("id")

def upload_and_get_public_url(local_file_path, person_folder_name, main_images_folder_id):
    service = get_drive_service()

    # 1. Create/find personal folder inside main folder
    person_folder_id = create_folder_if_not_exists(service, person_folder_name, main_images_folder_id)

    # 2. Upload image file
    file_metadata = {
        "name": os.path.basename(local_file_path),
        "parents": [person_folder_id],
    }
    media = MediaFileUpload(local_file_path, resumable=True)
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    file_id = uploaded_file.get("id")

    # 3. Make file publicly viewable
    permission = {
        "type": "anyone",
        "role": "reader",
    }
    service.permissions().create(fileId=file_id, body=permission).execute()

    # 4. Return public image URL
    return f"https://drive.google.com/uc?id={file_id}&export=download"
