import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
import urllib.parse
from google.oauth2 import service_account  # <-- Add this import
import google.auth.transport.requests
from googleapiclient.errors import HttpError
# import logging

from PIL import Image, ImageFilter
import io
import tempfile

# # Suppress INFO messages from googleapiclient
# logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.WARNING)

# --- SLIDE CONSTANTS (from test.py) ---
SLIDE_WIDTH = 9144000
SLIDE_HEIGHT = 5143500
CONTENT_WIDTH = int(SLIDE_WIDTH * 0.80)
CONTENT_X = (SLIDE_WIDTH - CONTENT_WIDTH) // 2

HEADSHOT_SIZE_RATIO = 0.18
TOP_MARGIN_RATIO = 0.20
GAP_AFTER_HEADSHOT_RATIO = 0.05
GAP_AFTER_NAME_RATIO = 0.06
GAP_AFTER_TAGLINE_RATIO = 0.06
GAP_AFTER_ITALIC_RATIO = 0.08

NAME_FONT_SIZE = 26
TAGLINE_FONT_SIZE = 16
ITALIC_FONT_SIZE = 11
BUTTON_FONT_SIZE = 16

NAME_BOX_HEIGHT = NAME_FONT_SIZE * 15000
TAGLINE_BOX_HEIGHT = 70000
ITALIC_BOX_HEIGHT = 60000
BUTTON_BOX_HEIGHT = 400000
BUTTON_WIDTH_RATIO = 0.50

headshot_size = int(HEADSHOT_SIZE_RATIO * SLIDE_HEIGHT)
headshot_x = SLIDE_WIDTH // 2 - headshot_size // 2
button_width = int(BUTTON_WIDTH_RATIO * SLIDE_WIDTH)

top_margin = int(TOP_MARGIN_RATIO * SLIDE_HEIGHT)
gap_after_headshot = int(GAP_AFTER_HEADSHOT_RATIO * SLIDE_HEIGHT)
gap_after_name = int(GAP_AFTER_NAME_RATIO * SLIDE_HEIGHT)
gap_after_tagline = int(GAP_AFTER_TAGLINE_RATIO * SLIDE_HEIGHT)
gap_after_italic = int(GAP_AFTER_ITALIC_RATIO * SLIDE_HEIGHT)

headshot_y = top_margin
name_y = headshot_y + headshot_size + gap_after_headshot
tagline_y = name_y + NAME_BOX_HEIGHT + gap_after_name
italic_y = tagline_y + TAGLINE_BOX_HEIGHT + gap_after_tagline
button_y = italic_y + ITALIC_BOX_HEIGHT + gap_after_italic
button_x = (SLIDE_WIDTH - button_width) // 2

# --- Service account ---
# def get_service_account_credentials(scopes, service_account_file='slides/speaker-kit-creator-agent.json'):
#     # Load credentials from service account file
#     creds = service_account.Credentials.from_service_account_file(
#         service_account_file, scopes=scopes)
    
#     # Refresh the credentials
#     auth_req = google.auth.transport.requests.Request()
#     creds.refresh(auth_req)
    
#     return creds

# def cleanup_old_speaker_kits(drive_service, max_files_to_keep=3):
#     """Clean up old speaker kit files to free up storage space"""
#     try:
#         # Find all speaker kit presentations
#         query = "name contains 'Speaker Kit' and mimeType='application/vnd.google-apps.presentation' and trashed=false"
#         results = drive_service.files().list(
#             q=query, 
#             fields="files(id, name, createdTime)",
#             orderBy="createdTime desc"
#         ).execute()
        
#         files = results.get('files', [])
        
#         # Keep only the most recent files
#         if len(files) > max_files_to_keep:
#             files_to_delete = files[max_files_to_keep:]
#             for file in files_to_delete:
#                 print(f"Deleting old file: {file['name']}")
#                 drive_service.files().delete(fileId=file['id']).execute()
            
#             print(f"Cleaned up {len(files_to_delete)} old speaker kit files")
#     except Exception as e:
#         print(f"Warning: Could not clean up old files: {e}")

# def cleanup_old_images(drive_service, max_images_to_keep=10):
#     """Clean up old uploaded images to free up storage space"""
#     try:
#         # Find all image files (jpeg, png, webp, etc.)
#         query = "(mimeType contains 'image/') and trashed=false"
#         results = drive_service.files().list(
#             q=query, 
#             fields="files(id, name, createdTime, size)",
#             orderBy="createdTime desc"
#         ).execute()
        
#         files = results.get('files', [])
        
#         # Keep only the most recent files
#         if len(files) > max_images_to_keep:
#             files_to_delete = files[max_images_to_keep:]
#             for file in files_to_delete:
#                 print(f"Deleting old image: {file['name']}")
#                 drive_service.files().delete(fileId=file['id']).execute()
            
#             print(f"Cleaned up {len(files_to_delete)} old image files")
#     except Exception as e:
#         print(f"Warning: Could not clean up old images: {e}")

# def emergency_cleanup(drive_service):
#     """Emergency cleanup - delete all files except the most recent ones"""
#     try:
#         print("Performing emergency cleanup...")
        
#         # Delete all speaker kits except the most recent 1
#         cleanup_old_speaker_kits(drive_service, max_files_to_keep=1)
        
#         # Delete all images except the most recent 2
#         cleanup_old_images(drive_service, max_images_to_keep=2)
        
#         # Also try to delete any other large files
#         query = "trashed=false and (mimeType contains 'application/' or mimeType contains 'video/')"
#         results = drive_service.files().list(
#             q=query, 
#             fields="files(id, name, createdTime, size)",
#             orderBy="createdTime desc"
#         ).execute()
        
#         files = results.get('files', [])
#         if len(files) > 3:  # Keep only 3 most recent files
#             files_to_delete = files[3:]
#             for file in files_to_delete:
#                 print(f"Emergency deleting: {file['name']}")
#                 drive_service.files().delete(fileId=file['id']).execute()
        
#         print("Emergency cleanup completed")
#     except Exception as e:
#         print(f"Emergency cleanup failed: {e}")

# --- IMAGE UPLOAD HELPERS ---
def find_file_in_drive(filename, drive_service):
    query = f"name='{filename}' and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    return None

def upload_image_to_drive(image_path, drive_service):
    filename = os.path.basename(image_path)
    existing_id = find_file_in_drive(filename, drive_service)
    if existing_id:
        return existing_id
    file_metadata = {
        'name': filename
    }
    media = MediaFileUpload(image_path, mimetype='image/jpeg')
    file = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    drive_service.permissions().create(
        fileId=file['id'],
        body={'role': 'reader', 'type': 'anyone'}
    ).execute()
    return file['id']

def get_drive_service(creds):
    return build('drive', 'v3', credentials=creds)

def get_slides_service(creds):
    return build('slides', 'v1', credentials=creds)

def get_or_create_drive_folder(drive_service, folder_name, parent_id=None):
    # Search for the folder
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    # Create the folder
    metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent_id:
        metadata['parents'] = [parent_id]
    folder = drive_service.files().create(body=metadata, fields='id').execute()
    return folder['id']


def find_file_in_folder(drive_service, filename, folder_id):
    query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get('files', [])
    if files:
        return files[0]['id']
    return None


def upload_file_to_folder(drive_service, file_path, folder_id):
    from googleapiclient.http import MediaFileUpload
    filename = os.path.basename(file_path)
    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaFileUpload(file_path, resumable=True)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file['id']


def set_file_public(drive_service, file_id):
    try:
        drive_service.permissions().create(
            fileId=file_id,
            body={'role': 'reader', 'type': 'anyone'},
            fields='id',
        ).execute()
    except HttpError as e:
        if e.resp.status == 403 and 'already exists' in str(e):
            pass  # Permission already set
        else:
            raise

def get_drive_public_url(file_id):
    return f"https://drive.google.com/uc?id={file_id}"


def ensure_image_on_drive_and_get_url(image_path, drive_service, folder_name):
    if image_path.startswith('http://') or image_path.startswith('https://'):
        return image_path  # Already a public URL
    # Otherwise, upload to Drive folder
    folder_id = get_or_create_drive_folder(drive_service, folder_name)
    filename = os.path.basename(image_path)
    file_id = find_file_in_folder(drive_service, filename, folder_id)
    if not file_id:
        file_id = upload_file_to_folder(drive_service, image_path, folder_id)
    set_file_public(drive_service, file_id)
    return get_drive_public_url(file_id)

def blur_and_resize_image(image_path, width, height, blur_radius=15):
    img = Image.open(image_path)
    # Convert EMU to pixels (assuming 914400 EMU = 1 inch, 96 dpi)
    emu_to_px = 96 / 914400
    px_width = int(width * emu_to_px)
    px_height = int(height * emu_to_px)
    img = img.resize((px_width, px_height), resample=Image.Resampling.LANCZOS)
    blurred_img = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    blurred_img.save(temp_file, format='PNG')
    temp_file.close()
    return temp_file.name

# --- MAIN FUNCTION ---
def create_speaker_kit_slides(kit_data):
    try:
        print("Starting slide creation process...")
        # print("Kit data received:", kit_data)
        
        import requests
        
        SCOPES = ['https://www.googleapis.com/auth/presentations', 'https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = 'service-account-data.json'
        
        # Check if service account file exists
        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            print(f"ERROR: Service account file not found: {SERVICE_ACCOUNT_FILE}")
            raise FileNotFoundError(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        
        print(f"Service account file found: {SERVICE_ACCOUNT_FILE}")
        
        # Authenticate and get an access token (exactly like your working example)
        IMPERSONATE_USER = 'nabin@industryrockstar.ai'  # Or pass as a function argument

        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        ).with_subject(IMPERSONATE_USER)
        auth_req = google.auth.transport.requests.Request()
        credentials.refresh(auth_req)
        access_token = credentials.token
        print("Authentication successful, got access token")

        # 1. Create a new presentation using REST API (exactly like your working example)
        url = 'https://slides.googleapis.com/v1/presentations'
        
        body = {
            "title": f"Speaker Kit - {kit_data.get('name', 'Speaker')}",
            "pageSize": {
                "width": {
                    "magnitude": SLIDE_WIDTH,
                    "unit": "EMU"
                },
                "height": {
                    "magnitude": SLIDE_HEIGHT,
                    "unit": "EMU"
                }
            },
            "locale": "en-US"
        }

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        print("Creating presentation...")
        response = requests.post(url, headers=headers, json=body)
        
        print(f"Presentation creation response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Error creating presentation: {response.status_code} {response.text}")
            raise Exception(f"Failed to create presentation: {response.status_code}")

        data = response.json()
        presentation_id = data.get("presentationId")
        print(f"Presentation created with ID: {presentation_id}")

        drive_service = get_drive_service(credentials)
        # Prepare image URLs using Drive helpers
        bg_image_path = kit_data.get('bg_image_path', 'publicspeakerhero.jpeg')
        headshot_path = kit_data.get('headshot_path', 'publicspeakerhero.jpeg')
        if not (bg_image_path.startswith('http://') or bg_image_path.startswith('https://')):
            # Only process local files
            blurred_bg_path = blur_and_resize_image(bg_image_path, SLIDE_WIDTH, SLIDE_HEIGHT, blur_radius=15)
            bg_image_url = ensure_image_on_drive_and_get_url(blurred_bg_path, drive_service, 'background')
        else:
            bg_image_url = bg_image_path
        headshot_url = ensure_image_on_drive_and_get_url(headshot_path, drive_service, 'headshot')

        # 2. Prepare dynamic content
        SPEAKER_NAME = kit_data.get('name', 'Speaker')
        TAGLINE = kit_data.get('title', '')
        TAGS = kit_data.get('title', '')
        ABOUT_TEXT = kit_data.get('bio', '')
        CAREER_HIGHLIGHTS = kit_data.get('career_highlights', [
            "Authored best-selling book 'The AI Alchemist'",
            "Keynote speaker at over 100 international conferences on AI and leadership",
            "Led a groundbreaking initiative that resulted in a 30% efficiency",
            "Recognized as 'Top Innovator in Tech' by TechForward Magazine (2023)",
            "Founded a highly successful startup focused on ethical AI solutions",
            "Delivered a highly-rated TEDx talk on 'The Future of Human-AI Collaboration'",
        ])

        print(f"Speaker name: {SPEAKER_NAME}")
        print(f"Tagline: {TAGLINE}")

        # 3. Build requests for slides using REST API
        print("Building slide requests...")
        batch_update_url = f"https://slides.googleapis.com/v1/presentations/{presentation_id}:batchUpdate"
        
        requests_data = [
            # Delete default slide
            {"deleteObject": {"objectId": 'p'}},
            # --- COVER SLIDE ---
            {"createSlide": {"objectId": "slide1", "insertionIndex": 0, "slideLayoutReference": {"predefinedLayout": "BLANK"}}},
            {"createImage": {"objectId": "bg_image", "url": bg_image_url, "elementProperties": {
                "pageObjectId": "slide1",
                "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
            }}},
            {"createShape": {"objectId": "overlay", "shapeType": "RECTANGLE", "elementProperties": {
                "pageObjectId": "slide1",
                "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
            }}},
            {"updateShapeProperties": {"objectId": "overlay", "shapeProperties": {
                "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}}, "alpha": 0.55}}
            }, "fields": "shapeBackgroundFill.solidFill.color,shapeBackgroundFill.solidFill.alpha"}},
            {"createImage": {"objectId": "headshot", "url": headshot_url, "elementProperties": {
                "pageObjectId": "slide1",
                "size": {"height": {"magnitude": headshot_size, "unit": "EMU"}, "width": {"magnitude": headshot_size, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": headshot_x, "translateY": headshot_y, "unit": "EMU"}
            }}},
            {"createShape": {"objectId": "cover_name", "shapeType": "TEXT_BOX", "elementProperties": {
                "pageObjectId": "slide1",
                "size": {"height": {"magnitude": NAME_BOX_HEIGHT, "unit": "EMU"}, "width": {"magnitude": CONTENT_WIDTH, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": CONTENT_X, "translateY": name_y, "unit": "EMU"}}}},
            {"insertText": {"objectId": "cover_name", "insertionIndex": 0, "text": SPEAKER_NAME}},
            {"updateTextStyle": {"objectId": "cover_name", "textRange": {"type": "ALL"}, "style": {"fontFamily": "Arial", "fontSize": {"magnitude": NAME_FONT_SIZE, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontFamily,fontSize,bold,foregroundColor"}},
            {"updateParagraphStyle": {"objectId": "cover_name", "textRange": {"type": "ALL"}, "style": {"alignment": "CENTER"}, "fields": "alignment"}},
            {"createShape": {"objectId": "cover_tagline", "shapeType": "TEXT_BOX", "elementProperties": {
                "pageObjectId": "slide1",
                "size": {"height": {"magnitude": TAGLINE_BOX_HEIGHT, "unit": "EMU"}, "width": {"magnitude": CONTENT_WIDTH, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": CONTENT_X, "translateY": tagline_y, "unit": "EMU"}}}},
            {"insertText": {"objectId": "cover_tagline", "insertionIndex": 0, "text": TAGLINE}},
            {"updateTextStyle": {"objectId": "cover_tagline", "textRange": {"type": "ALL"}, "style": {"fontFamily": "Arial", "fontSize": {"magnitude": TAGLINE_FONT_SIZE, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontFamily,fontSize,foregroundColor"}},
            {"updateParagraphStyle": {"objectId": "cover_tagline", "textRange": {"type": "ALL"}, "style": {"alignment": "CENTER"}, "fields": "alignment"}},
            {"createShape": {"objectId": "cover_subtitle", "shapeType": "TEXT_BOX", "elementProperties": {
                "pageObjectId": "slide1",
                "size": {"height": {"magnitude": ITALIC_BOX_HEIGHT, "unit": "EMU"}, "width": {"magnitude": CONTENT_WIDTH, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": CONTENT_X, "translateY": italic_y, "unit": "EMU"}}}},
            {"insertText": {"objectId": "cover_subtitle", "insertionIndex": 0, "text": TAGS}},
            {"updateTextStyle": {"objectId": "cover_subtitle", "textRange": {"type": "ALL"}, "style": {"fontFamily": "Arial", "fontSize": {"magnitude": ITALIC_FONT_SIZE, "unit": "PT"}, "italic": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 0.7, "green": 0.7, "blue": 0.7}}}}, "fields": "fontFamily,fontSize,italic,foregroundColor"}},
            {"updateParagraphStyle": {"objectId": "cover_subtitle", "textRange": {"type": "ALL"}, "style": {"alignment": "CENTER"}, "fields": "alignment"}},
            {"createShape": {"objectId": "cta_button", "shapeType": "ROUND_RECTANGLE", "elementProperties": {
                "pageObjectId": "slide1",
                "size": {"height": {"magnitude": BUTTON_BOX_HEIGHT, "unit": "EMU"}, "width": {"magnitude": button_width, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": button_x, "translateY": button_y, "unit": "EMU"}}}},
            {"insertText": {"objectId": "cta_button", "insertionIndex": 0, "text": "Discover Solutions"}},
            {"updateShapeProperties": {
                "objectId": "cta_button",
                "shapeProperties": {
                    "shapeBackgroundFill": {
                        "solidFill": {
                            "color": {"rgbColor": {"red": 0.09, "green": 0.32, "blue": 0.6}},
                            "alpha": 1
                        }
                    },
                    "outline": {
                        "outlineFill": {
                            "solidFill": {"color": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}
                        },
                        "weight": {"magnitude": 2, "unit": "PT"}
                    }
                },
                "fields": "shapeBackgroundFill.solidFill.color,shapeBackgroundFill.solidFill.alpha,outline.outlineFill.solidFill.color,outline.weight"
            }},
            {"updateTextStyle": {"objectId": "cta_button", "textRange": {"type": "ALL"}, "style": {"fontFamily": "Arial", "fontSize": {"magnitude": BUTTON_FONT_SIZE, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontFamily,fontSize,bold,foregroundColor"}},
            {"updateParagraphStyle": {"objectId": "cta_button", "textRange": {"type": "ALL"}, "style": {"alignment": "CENTER"}, "fields": "alignment"}},
            # --- ABOUT SLIDE ---
            {"createSlide": {"objectId": "slide2", "insertionIndex": 1, "slideLayoutReference": {"predefinedLayout": "BLANK"}}},
            {"createImage": {"objectId": "bg_image2", "url": bg_image_url, "elementProperties": {
                "pageObjectId": "slide2",
                "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
            }}},
            {"createShape": {"objectId": "overlay2", "shapeType": "RECTANGLE", "elementProperties": {
                "pageObjectId": "slide2",
                "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
            }}},
            {"updateShapeProperties": {
                "objectId": "overlay2",
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}}, "alpha": 0.55}}
                },
                "fields": "shapeBackgroundFill.solidFill.color,shapeBackgroundFill.solidFill.alpha"
            }},
            {"createImage": {"objectId": "about_headshot", "url": headshot_url, "elementProperties": {
                "pageObjectId": "slide2",
                "size": {"height": {"magnitude": 1800000, "unit": "EMU"}, "width": {"magnitude": 1800000, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 6500000, "translateY": 500000, "unit": "EMU"}
            }}},
            {"createShape": {"objectId": "about_title", "shapeType": "TEXT_BOX", "elementProperties": {
                "pageObjectId": "slide2",
                "size": {"height": {"magnitude": 120000, "unit": "EMU"}, "width": {"magnitude": 5000000, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 400000, "unit": "EMU"}
            }}},
            {"insertText": {"objectId": "about_title", "insertionIndex": 0, "text": f"About {SPEAKER_NAME}"}},
            {"updateTextStyle": {"objectId": "about_title", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 25, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,bold,foregroundColor"}},
            {"createShape": {"objectId": "about_text", "shapeType": "TEXT_BOX", "elementProperties": {
                "pageObjectId": "slide2",
                "size": {"height": {"magnitude": 300000, "unit": "EMU"}, "width": {"magnitude": 5000000, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 800000, "unit": "EMU"}
            }}},
            {"insertText": {"objectId": "about_text", "insertionIndex": 0, "text": ABOUT_TEXT}},
            {"updateTextStyle": {"objectId": "about_text", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 12, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,foregroundColor"}},
            {"createShape": {"objectId": "career_title2", "shapeType": "TEXT_BOX", "elementProperties": {
                "pageObjectId": "slide2",
                "size": {"height": {"magnitude": 90000, "unit": "EMU"}, "width": {"magnitude": 5000000, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 2300000, "unit": "EMU"}
            }}},
            {"insertText": {"objectId": "career_title2", "insertionIndex": 0, "text": "Career Highlights"}},
            {"updateTextStyle": {"objectId": "career_title2", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 20, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,bold,foregroundColor"}},
            {"createShape": {"objectId": "career_left", "shapeType": "TEXT_BOX", "elementProperties": {
                "pageObjectId": "slide2",
                "size": {"height": {"magnitude": 250000, "unit": "EMU"}, "width": {"magnitude": 3500000, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 2800000, "unit": "EMU"}
            }}},
            {"insertText": {"objectId": "career_left", "insertionIndex": 0, "text": "• " + CAREER_HIGHLIGHTS[0] + "\n\n• " + CAREER_HIGHLIGHTS[1] + "\n\n• " + CAREER_HIGHLIGHTS[2]}},
            {"updateTextStyle": {"objectId": "career_left", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 12, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,foregroundColor"}},
            {"createShape": {"objectId": "career_right", "shapeType": "TEXT_BOX", "elementProperties": {
                "pageObjectId": "slide2",
                "size": {"height": {"magnitude": 250000, "unit": "EMU"}, "width": {"magnitude": 3500000, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 4800000, "translateY": 2800000, "unit": "EMU"}
            }}},
            {"insertText": {"objectId": "career_right", "insertionIndex": 0, "text": "• " + CAREER_HIGHLIGHTS[3] + "\n\n• " + CAREER_HIGHLIGHTS[4] + "\n\n• " + CAREER_HIGHLIGHTS[5]}},
            {"updateTextStyle": {"objectId": "career_right", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 12, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,foregroundColor"}},
        ]  # <-- Properly close the requests_data list for the initial slides

        # --- TOPIC SLIDES ---
        topics = kit_data.get('topics', [])
        if isinstance(topics, list):
            for idx, topic in enumerate(topics):
                slide_num = 3 + idx  # slide1, slide2, then topics
                slide_id = f"topic_slide_{idx+1}"
                bg_id = f"topic_bg_{idx+1}"
                overlay_id = f"topic_overlay_{idx+1}"
                headshot_id = f"topic_headshot_{idx+1}"
                title_id = f"topic_title_{idx+1}"
                desc_id = f"topic_desc_{idx+1}"
                # Add slide
                requests_data.append({"createSlide": {"objectId": slide_id, "insertionIndex": slide_num-1, "slideLayoutReference": {"predefinedLayout": "BLANK"}}})
                # Background image
                requests_data.append({"createImage": {"objectId": bg_id, "url": bg_image_url, "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
                }}})
                # Overlay
                requests_data.append({"createShape": {"objectId": overlay_id, "shapeType": "RECTANGLE", "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
                }}})
                requests_data.append({"updateShapeProperties": {
                    "objectId": overlay_id,
                    "shapeProperties": {
                        "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}}, "alpha": 0.55}}
                    },
                    "fields": "shapeBackgroundFill.solidFill.color,shapeBackgroundFill.solidFill.alpha"
                }})
                # Headshot image (use headshot_url)
                requests_data.append({"createImage": {"objectId": headshot_id, "url": headshot_url, "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"height": {"magnitude": 1800000, "unit": "EMU"}, "width": {"magnitude": 1800000, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 6500000, "translateY": 500000, "unit": "EMU"}
                }}})
                # Title
                requests_data.append({"createShape": {"objectId": title_id, "shapeType": "TEXT_BOX", "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"height": {"magnitude": 120000, "unit": "EMU"}, "width": {"magnitude": 5000000, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 400000, "unit": "EMU"}
                }}})
                requests_data.append({"insertText": {"objectId": title_id, "insertionIndex": 0, "text": topic.get('title', f'Topic {idx+1}')}})
                requests_data.append({"updateTextStyle": {"objectId": title_id, "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 25, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,bold,foregroundColor"}})
                # Description
                requests_data.append({"createShape": {"objectId": desc_id, "shapeType": "TEXT_BOX", "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"height": {"magnitude": 300000, "unit": "EMU"}, "width": {"magnitude": 5000000, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 800000, "unit": "EMU"}
                }}})
                requests_data.append({"insertText": {"objectId": desc_id, "insertionIndex": 0, "text": topic.get('description', '')}})
                requests_data.append({"updateTextStyle": {"objectId": desc_id, "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 12, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,foregroundColor"}})

        print("Executing slide creation...")
        batch_body = {"requests": requests_data}
        response = requests.post(batch_update_url, headers=headers, json=batch_body)
        
        print(f"Slide creation response status: {response.status_code}")
        
        if response.status_code not in (200, 201):
            print(f"Error creating slides: {response.status_code} {response.text}")
            raise Exception(f"Failed to create slides: {response.status_code}")

        print("Slides created successfully!")

        # 5. Make presentation publicly accessible (exactly like your working example)
        print("Making presentation publicly accessible...")
        drive_url = f"https://www.googleapis.com/drive/v3/files/{presentation_id}/permissions"
        permission_body = {
            "role": "writer",
            "type": "anyone"
        }
        perm_response = requests.post(drive_url, headers=headers, json=permission_body)
        print(f"Permission response status: {perm_response.status_code}")
        
        if perm_response.status_code in (200, 201):
            print("Shared with anyone who has the link!")
        else:
            print(f"Failed to share: {perm_response.status_code} {perm_response.text}")
        
        slides_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
        print(f"Slides created successfully: {slides_url}")
        print("RETURNING SLIDES URL:", slides_url)

        # Return the presentation link
        return slides_url
        
    except Exception as e:
        print(f"Error in create_speaker_kit_slides: {e}")
        import traceback
        traceback.print_exc()
        raise e
    