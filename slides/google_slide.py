import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle
from urllib.parse import urlparse
from google.oauth2 import service_account
import google.auth.transport.requests
from googleapiclient.errors import HttpError
import requests
import mimetypes

from slides.image_blur import blur_and_save_image_from_url

from slides.google_drive_utils import upload_and_get_public_url, get_drive_service

from PIL import Image, ImageFilter
import io
import tempfile

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
GAP_AFTER_ITALIC_RATIO = 0.06
GAP_AFTER_CTA_RATIO = 0.08 # New constant, adjust as needed

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
gap_after_cta = int(GAP_AFTER_CTA_RATIO * SLIDE_HEIGHT) # New constant

headshot_y = top_margin
name_y = headshot_y + headshot_size + gap_after_headshot
tagline_y = name_y + NAME_BOX_HEIGHT + gap_after_name
italic_y = tagline_y + TAGLINE_BOX_HEIGHT + gap_after_tagline
button_y = italic_y + ITALIC_BOX_HEIGHT + gap_after_italic
button_x = (SLIDE_WIDTH - button_width) // 2

GOOGLE_DRIVE_MAIN_IMAGES_FOLDER_ID = "1IfLkxDzlHoPvV5wZkie2qpvNAO9td0yN"

def handle_background_image(background_url: str, person_name: str) -> str:
    folder_safe_person_name = person_name.replace(" ", "_")
    local_blur_path = f"static/blurred_backgrounds/{folder_safe_person_name}_blurred.png"

    # Blur and save locally
    blur_and_save_image_from_url(background_url, local_blur_path)

    # Upload to Drive
    drive_url = upload_and_get_public_url(
        local_file_path=local_blur_path,
        person_folder_name=folder_safe_person_name,
        main_images_folder_id=GOOGLE_DRIVE_MAIN_IMAGES_FOLDER_ID
    )

    return drive_url

def process_speaker_kit_images(kit_data: dict) -> dict:
    person_name = kit_data.get("name", "Unknown_Speaker")
    folder_safe_person_name = person_name.replace(" ", "_")

    image_fields = [
        "headshots",
        "heashot1",
        "booking_contact.qr_code"
    ]

    for field in image_fields:
        url = get_nested_field(kit_data, field)
        if url and is_local_image_url(url):
            local_path = extract_local_path(url)
            if os.path.exists(local_path):
                uploaded_url = upload_and_get_public_url(
                    local_file_path=local_path,
                    person_folder_name=folder_safe_person_name,
                    main_images_folder_id=GOOGLE_DRIVE_MAIN_IMAGES_FOLDER_ID
                )
                set_nested_field(kit_data, field, uploaded_url)

    # topics[].image
    for topic in kit_data.get("topics", []):
        image_url = topic.get("image")
        if image_url and is_local_image_url(image_url):
            local_path = extract_local_path(image_url)
            if os.path.exists(local_path):
                uploaded_url = upload_and_get_public_url(
                    local_file_path=local_path,
                    person_folder_name=folder_safe_person_name,
                    main_images_folder_id=GOOGLE_DRIVE_MAIN_IMAGES_FOLDER_ID
                )
                topic["image"] = uploaded_url

    print(f"Checking field: {field} = {url}")
    print(f"Extracted path: {local_path}")
    print("File exists?" , os.path.exists(local_path))

    return kit_data

def get_nested_field(data: dict, dotted_key: str):
    keys = dotted_key.split(".")
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data

def set_nested_field(data: dict, dotted_key: str, value):
    keys = dotted_key.split(".")
    for key in keys[:-1]:
        data = data.setdefault(key, {})
    data[keys[-1]] = value

def is_local_image_url(url: str) -> bool:
    return (
        "localhost" in url
        or "/statics/uploads/" in url
        or "/speaker-kit/statics/uploads/" in url
    )

def extract_local_path(url: str) -> str:
    """
    Converts a URL like http://localhost:8003/speaker-kit/statics/uploads/image.png
    into a filesystem path like static/uploads/image.png
    """
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")

    # Replace '/speaker-kit/statics/' with 'static/'
    if path.startswith("speaker-kit/statics/"):
        path = path.replace("speaker-kit/statics", "static")
    elif path.startswith("statics/"):
        path = path.replace("statics", "static")

    return path


# --- MAIN FUNCTION ---
def create_speaker_kit_slides(kit_data, bg_image_path=None):
    
    print(kit_data)
    # Use only the provided bg_image_path (should be a URL)
    if not bg_image_path:
        bg_image_path = "https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D"

    person_name = kit_data.get("name", "Unknown Speaker")

    try:
        bg_image_url = handle_background_image(bg_image_path, person_name)
    except Exception as e:
        print(f"[❌] Failed to process background image: {e}")
        bg_image_url = bg_image_path  # Fallback to original if error

    name = kit_data.get("name", "")
    email = kit_data.get("email", "")
    website = kit_data.get("website", "")
    tagline = kit_data.get("tagline", "")
    subtagline = kit_data.get("subtagline", "")
    bio = kit_data.get("bio", "")
    career_highlights = kit_data.get("career_highlights", [])
    topics = kit_data.get("topics", [])
    why_book = kit_data.get("why_book", [])
    audience_takeaways = kit_data.get("audience_takeaways", [])
    career_milestones = kit_data.get("career_milestones", [])
    clients_partners = kit_data.get("clients_partners", [])
    featured_in = kit_data.get("featured_in", [])
    testimonials = kit_data.get("testimonials", [])
    formats_offered = kit_data.get("formats_offered", [])
    booking_contact = kit_data.get("booking_contact", {})
    
    # Then use these variables to create your slides
    try:
        print("Starting slide creation process...")
        
        SCOPES = ['https://www.googleapis.com/auth/presentations', 'https://www.googleapis.com/auth/drive']
        SERVICE_ACCOUNT_FILE = 'slides/service-account-data.json'
        
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
        
        if response.status_code != 200:
            print(f"Error creating presentation: {response.status_code} {response.text}")
            raise Exception(f"Failed to create presentation: {response.status_code}")

        data = response.json()
        presentation_id = data.get("presentationId")
        print(f"Presentation created with ID: {presentation_id}")

        # Initialize services and prepare images
        drive_service = get_drive_service()
        
        default_headshot = "https://plus.unsplash.com/premium_photo-1664474619075-644dd191935f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8aW1hZ2V8ZW58MHx8MHx8fDA%3D"
        headshot_path = kit_data.get('headshots') or kit_data.get('headshot_path')

        headshot1_path = kit_data.get('heashot1') or kit_data.get('headshot1_path')
        headshot1_url = headshot1_path if headshot1_path else default_headshot

        # Prepare image URLs using Drive helpers
        # headshot_url = ensure_image_on_drive_and_get_url(headshot_path, drive_service, 'headshot', default_url=default_headshot)

        headshot_url = headshot_path if headshot_path else default_headshot


        # Build slide creation requests
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
            {"insertText": {"objectId": "cover_name", "insertionIndex": 0, "text": name}},
            {"updateTextStyle": {"objectId": "cover_name", "textRange": {"type": "ALL"}, "style": {"fontFamily": "Arial", "fontSize": {"magnitude": NAME_FONT_SIZE, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontFamily,fontSize,bold,foregroundColor"}},
            {"updateParagraphStyle": {"objectId": "cover_name", "textRange": {"type": "ALL"}, "style": {"alignment": "CENTER"}, "fields": "alignment"}},
            {"createShape": {"objectId": "cover_tagline", "shapeType": "TEXT_BOX", "elementProperties": {
                "pageObjectId": "slide1",
                "size": {"height": {"magnitude": TAGLINE_BOX_HEIGHT, "unit": "EMU"}, "width": {"magnitude": CONTENT_WIDTH, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": CONTENT_X, "translateY": tagline_y, "unit": "EMU"}}}},
            {"insertText": {"objectId": "cover_tagline", "insertionIndex": 0, "text": subtagline}},
            {"updateTextStyle": {"objectId": "cover_tagline", "textRange": {"type": "ALL"}, "style": {"fontFamily": "Arial", "fontSize": {"magnitude": TAGLINE_FONT_SIZE, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontFamily,fontSize,foregroundColor"}},
            {"updateParagraphStyle": {"objectId": "cover_tagline", "textRange": {"type": "ALL"}, "style": {"alignment": "CENTER"}, "fields": "alignment"}},
            {"createShape": {"objectId": "cover_subtitle", "shapeType": "TEXT_BOX", "elementProperties": {
                "pageObjectId": "slide1",
                "size": {"height": {"magnitude": ITALIC_BOX_HEIGHT, "unit": "EMU"}, "width": {"magnitude": CONTENT_WIDTH, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": CONTENT_X, "translateY": italic_y, "unit": "EMU"}}}},
            {"insertText": {"objectId": "cover_subtitle", "insertionIndex": 0, "text": tagline}},
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
            {"createImage": {"objectId": "about_headshot", "url": headshot1_url, "elementProperties": {
                "pageObjectId": "slide2",
                "size": {"height": {"magnitude": 1800000, "unit": "EMU"}, "width": {"magnitude": 1800000, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 6500000, "translateY": 500000, "unit": "EMU"}
            }}},
            {"createShape": {"objectId": "about_title", "shapeType": "TEXT_BOX", "elementProperties": {
                "pageObjectId": "slide2",
                "size": {"height": {"magnitude": 120000, "unit": "EMU"}, "width": {"magnitude": 5000000, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 400000, "unit": "EMU"}
            }}},
            {"insertText": {"objectId": "about_title", "insertionIndex": 0, "text": f"About {name}"}},
            {"updateTextStyle": {"objectId": "about_title", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 25, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,bold,foregroundColor"}},
            {"createShape": {"objectId": "about_text", "shapeType": "TEXT_BOX", "elementProperties": {
                "pageObjectId": "slide2",
                "size": {"height": {"magnitude": 300000, "unit": "EMU"}, "width": {"magnitude": 5000000, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 800000, "unit": "EMU"}
            }}},
            {"insertText": {"objectId": "about_text", "insertionIndex": 0, "text": bio}},
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
            {"insertText": {"objectId": "career_left", "insertionIndex": 0, "text": "• " + career_highlights[0] + "\n\n• " + career_highlights[1] + "\n\n• " + career_highlights[2]}},
            {"updateTextStyle": {"objectId": "career_left", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 12, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,foregroundColor"}},
            {"createShape": {"objectId": "career_right", "shapeType": "TEXT_BOX", "elementProperties": {
                "pageObjectId": "slide2",
                "size": {"height": {"magnitude": 250000, "unit": "EMU"}, "width": {"magnitude": 3500000, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": 4800000, "translateY": 2800000, "unit": "EMU"}
            }}},
            {"insertText": {"objectId": "career_right", "insertionIndex": 0, "text": "• " + career_highlights[3] + "\n\n• " + career_highlights[4] + "\n\n• " + career_highlights[5]}},
            {"updateTextStyle": {"objectId": "career_right", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 12, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,foregroundColor"}},
        ]

        # --- TOPIC SLIDES ---
        topics = kit_data.get('topics', [])
        if isinstance(topics, list):
            for idx, topic in enumerate(topics):
                slide_num = 3 + idx
                slide_id = f"topic_slide_{idx+1}"
                bg_id = f"topic_bg_{idx+1}"
                overlay_id = f"topic_overlay_{idx+1}"
                headshot_id = f"topic_headshot_{idx+1}"
                title_id = f"topic_title_{idx+1}"
                desc_id = f"topic_desc_{idx+1}"
                topic_img_id = f"topic_img_{idx+1}"
                # Add slide
                requests_data.append({"createSlide": {"objectId": slide_id, "insertionIndex": slide_num-1, "slideLayoutReference": {"predefinedLayout": "BLANK"}}})
                
                # For each topic, use a specific image (or a default if not present)
                default_topic_image = "https://static.toiimg.com/thumb/msid-121340289,width-1280,height-720,resizemode-4/121340289.jpg"
                raw_topic_image = topic.get('image')
                topic_image_final_url = raw_topic_image if raw_topic_image else default_topic_image

                # Add background image (covers the whole slide)
                requests_data.append({
                    "createImage": {
                        "objectId": bg_id,
                        "url": bg_image_url,
                        "elementProperties": {
                            "pageObjectId": slide_id,
                            "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
                        }
                    }
                })
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
                # Add topic image (smaller, on top)
                requests_data.append({
                    "createImage": {
                        "objectId": topic_img_id,
                        "url": topic_image_final_url,
                        "elementProperties": {
                            "pageObjectId": slide_id,
                            "size": {"height": {"magnitude": 1800000, "unit": "EMU"}, "width": {"magnitude": 1800000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 6500000, "translateY": 500000, "unit": "EMU"}
                        }
                    }
                })
                # Title
                requests_data.append({"createShape": {"objectId": title_id, "shapeType": "TEXT_BOX", "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"height": {"magnitude": 120000, "unit": "EMU"}, "width": {"magnitude": 5000000, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 300000, "unit": "EMU"}
                }}})
                requests_data.append({"insertText": {"objectId": title_id, "insertionIndex": 0, "text": topic.get('title', f'Topic {idx+1}')}})
                requests_data.append({"updateTextStyle": {"objectId": title_id, "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 25, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,bold,foregroundColor"}})
                # Description
                requests_data.append({"createShape": {"objectId": desc_id, "shapeType": "TEXT_BOX", "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"height": {"magnitude": 300000, "unit": "EMU"}, "width": {"magnitude": 5000000, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 1200000, "unit": "EMU"}
                }}})
                requests_data.append({"insertText": {"objectId": desc_id, "insertionIndex": 0, "text": topic.get('description', '')}})
                requests_data.append({"updateTextStyle": {"objectId": desc_id, "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 12, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,foregroundColor"}})

        # WHAT MAKES YOU DIFFERENT SLIDE (Top/Bottom layout)
        # Condition: Only add if there's content for why_book or audience_takeaways
        if why_book or audience_takeaways:
            requests_data += [
                {"createSlide": {"objectId": "different_slide", "slideLayoutReference": {"predefinedLayout": "BLANK"}}},

                # Background Image
                {"createImage": {"objectId": "different_bg", "url": bg_image_url, "elementProperties": {
                    "pageObjectId": "different_slide",
                    "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
                }}},

                # Overlay
                {"createShape": {"objectId": "different_overlay", "shapeType": "RECTANGLE", "elementProperties": {
                    "pageObjectId": "different_slide",
                    "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
                }}},
                {"updateShapeProperties": {
                    "objectId": "different_overlay",
                    "shapeProperties": {
                        "shapeBackgroundFill": {
                            "solidFill": {
                                "color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}},
                                "alpha": 0.55
                            }
                        }
                    },
                    "fields": "shapeBackgroundFill.solidFill.color,shapeBackgroundFill.solidFill.alpha"
                }},

                # Title
                {"createShape": {"objectId": "different_title", "shapeType": "TEXT_BOX", "elementProperties": {
                    "pageObjectId": "different_slide",
                    "size": {"height": {"magnitude": 120000, "unit": "EMU"}, "width": {"magnitude": 6000000, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 300000, "unit": "EMU"}
                }}},
                {"insertText": {"objectId": "different_title", "insertionIndex": 0, "text": "What Makes You Different"}},
                {"updateTextStyle": {"objectId": "different_title", "textRange": {"type": "ALL"}, "style": {
                    "fontSize": {"magnitude": 25, "unit": "PT"},
                    "bold": True,
                    "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}
                }, "fields": "fontSize,bold,foregroundColor"}},

                # Section 1 Heading: Why Book Me (Conditional)
                *(
                    [
                        {"createShape": {"objectId": "why_book_heading", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "different_slide",
                            "size": {"height": {"magnitude": 100000, "unit": "EMU"}, "width": {"magnitude": 7000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 900000, "unit": "EMU"}
                        }}},
                        {"insertText": {
                            "objectId": "why_book_heading",
                            "insertionIndex": 0,
                            "text": f"Why Book {name}?"
                        }},
                        {"updateTextStyle": {"objectId": "why_book_heading", "textRange": {"type": "ALL"}, "style": {
                            "fontSize": {"magnitude": 18, "unit": "PT"},
                            "bold": True,
                            "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}
                        }, "fields": "fontSize,bold,foregroundColor"}}
                    ] if why_book else []
                ),

                # Section 1 Content: Why Book Me bullet points (Conditional)
                *(
                    [
                        {"createShape": {"objectId": "why_book_content", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "different_slide",
                            "size": {"height": {"magnitude": 600000, "unit": "EMU"}, "width": {"magnitude": 7000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 1300000, "unit": "EMU"}
                        }}},
                        {"insertText": {
                            "objectId": "why_book_content",
                            "insertionIndex": 0,
                            "text": ("• " + "\n• ".join(why_book))
                        }},
                        {"updateTextStyle": {"objectId": "why_book_content", "textRange": {"type": "ALL"}, "style": {
                            "fontSize": {"magnitude": 14, "unit": "PT"},
                            "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}
                        }, "fields": "fontSize,foregroundColor"}}
                    ] if why_book else []
                ),

                # Section 2 Heading: Audience Takeaways (Conditional)
                *(
                    [
                        {"createShape": {"objectId": "takeaways_heading", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "different_slide",
                            "size": {"height": {"magnitude": 100000, "unit": "EMU"}, "width": {"magnitude": 7000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 2700000, "unit": "EMU"}
                        }}},
                        {"insertText": {
                            "objectId": "takeaways_heading",
                            "insertionIndex": 0,
                            "text": "Audience Takeaways:"
                        }},
                        {"updateTextStyle": {"objectId": "takeaways_heading", "textRange": {"type": "ALL"}, "style": {
                            "fontSize": {"magnitude": 18, "unit": "PT"},
                            "bold": True,
                            "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}
                        }, "fields": "fontSize,bold,foregroundColor"}}
                    ] if audience_takeaways else []
                ),

                # Section 2 Content: Audience Takeaways bullet points (Conditional)
                *(
                    [
                        {"createShape": {"objectId": "takeaways_content", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "different_slide",
                            "size": {"height": {"magnitude": 600000, "unit": "EMU"}, "width": {"magnitude": 7000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 3100000, "unit": "EMU"}
                        }}},
                        {"insertText": {
                            "objectId": "takeaways_content",
                            "insertionIndex": 0,
                            "text": ("• " + "\n• ".join(audience_takeaways))
                        }},
                        {"updateTextStyle": {"objectId": "takeaways_content", "textRange": {"type": "ALL"}, "style": {
                            "fontSize": {"magnitude": 14, "unit": "PT"},
                            "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}
                        }, "fields": "fontSize,foregroundColor"}}
                    ] if audience_takeaways else []
                )
            ]

        # --- PROOF & RECOGNITION SLIDE (Conditional) ---
        if career_milestones or clients_partners or featured_in:
            requests_data += [
                {"createSlide": {"objectId": "proof_slide", "slideLayoutReference": {"predefinedLayout": "BLANK"}}},
                {"createImage": {"objectId": "proof_bg", "url": bg_image_url, "elementProperties": {
                    "pageObjectId": "proof_slide",
                    "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
                }}},
                {"createShape": {"objectId": "proof_overlay", "shapeType": "RECTANGLE", "elementProperties": {
                    "pageObjectId": "proof_slide",
                    "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
                }}},
                {"updateShapeProperties": {
                    "objectId": "proof_overlay",
                    "shapeProperties": {
                        "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}}, "alpha": 0.55}}
                    },
                    "fields": "shapeBackgroundFill.solidFill.color,shapeBackgroundFill.solidFill.alpha"
                }},
                # Career Milestones Section (Conditional)
                *(
                    [
                        {"createShape": {"objectId": "career_milestones_title", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "proof_slide",
                            "size": {"height": {"magnitude": 120000, "unit": "EMU"}, "width": {"magnitude": 8000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 300000, "unit": "EMU"}
                        }}},
                        {"insertText": {"objectId": "career_milestones_title", "insertionIndex": 0, "text": "Career Milestones:"}},
                        {"updateTextStyle": {"objectId": "career_milestones_title", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 20, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,bold,foregroundColor"}},
                        {"createShape": {"objectId": "career_milestones_text", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "proof_slide",
                            "size": {"height": {"magnitude": 300000, "unit": "EMU"}, "width": {"magnitude": 8000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 900000, "unit": "EMU"}
                        }}},
                        {"insertText": {"objectId": "career_milestones_text", "insertionIndex": 0, "text": "• " + "\n\n• ".join(career_milestones)}},
                        {"updateTextStyle": {
                            "objectId": "career_milestones_text",
                            "textRange": {"type": "ALL"},
                            "style": {
                                "fontSize": {"magnitude": 16, "unit": "PT"},
                                "foregroundColor": {
                                    "opaqueColor": {
                                        "rgbColor": {"red": 1, "green": 1, "blue": 1}
                                    }
                                }
                            },
                            "fields": "fontSize,foregroundColor"
                        }},
                    ] if career_milestones else []
                ),
                # Clients & Partners Section (Conditional)
                *(
                    [
                        {"createShape": {"objectId": "clients_partners_title", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "proof_slide",
                            "size": {"height": {"magnitude": 120000, "unit": "EMU"}, "width": {"magnitude": 8000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 2500000, "unit": "EMU"}
                        }}},
                        {"insertText": {"objectId": "clients_partners_title", "insertionIndex": 0, "text": "Clients & Partners:"}},
                        {"updateTextStyle": {"objectId": "clients_partners_title", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 20, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,bold,foregroundColor"}},
                        {"createShape": {"objectId": "clients_partners_text", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "proof_slide",
                            "size": {"height": {"magnitude": 100000, "unit": "EMU"}, "width": {"magnitude": 8000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 2900000, "unit": "EMU"}
                        }}},
                        {"insertText": {
                            "objectId": "clients_partners_text",
                            "insertionIndex": 0,
                            "text": " • ".join(clients_partners)
                        }},
                        {"updateTextStyle": {"objectId": "clients_partners_text", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 14, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,foregroundColor"}}
                    ] if clients_partners else []
                ),
                # Featured In Section (Conditional)
                *(
                    [
                        {"createShape": {"objectId": "featured_in_title", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "proof_slide",
                            "size": {"height": {"magnitude": 120000, "unit": "EMU"}, "width": {"magnitude": 8000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 3500000, "unit": "EMU"}
                        }}},
                        {"insertText": {"objectId": "featured_in_title", "insertionIndex": 0, "text": "Featured In:"}},
                        {"updateTextStyle": {"objectId": "featured_in_title", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 20, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,bold,foregroundColor"}},
                        {"createShape": {"objectId": "featured_in_text", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "proof_slide",
                            "size": {"height": {"magnitude": 100000, "unit": "EMU"}, "width": {"magnitude": 8000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 3900000, "unit": "EMU"}
                        }}},
                        {"insertText": {
                            "objectId": "featured_in_text",
                            "insertionIndex": 0,
                            "text": " • ".join(featured_in)
                        }},
                        {"updateTextStyle": {"objectId": "featured_in_text", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 14, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,foregroundColor"}}
                    ] if featured_in else []
                ),
            ]

        # --- TESTIMONIALS SLIDE (Conditional) ---
        if testimonials:
            requests_data += [
                {"createSlide": {"objectId": "testimonials_slide", "slideLayoutReference": {"predefinedLayout": "BLANK"}}},
                {"createImage": {"objectId": "testimonials_bg", "url": bg_image_url, "elementProperties": {
                    "pageObjectId": "testimonials_slide",
                    "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
                }}},
                {"createShape": {"objectId": "testimonials_overlay", "shapeType": "RECTANGLE", "elementProperties": {
                    "pageObjectId": "testimonials_slide",
                    "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
                }}},
                {"updateShapeProperties": {
                    "objectId": "testimonials_overlay",
                    "shapeProperties": {
                        "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}}, "alpha": 0.55}}
                    },
                    "fields": "shapeBackgroundFill.solidFill.color,shapeBackgroundFill.solidFill.alpha"
                }},
                {"createShape": {"objectId": "testimonials_title", "shapeType": "TEXT_BOX", "elementProperties": {
                    "pageObjectId": "testimonials_slide",
                    "size": {"height": {"magnitude": 120000, "unit": "EMU"}, "width": {"magnitude": 8000000, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 300000, "unit": "EMU"}
                }}},
                {"insertText": {"objectId": "testimonials_title", "insertionIndex": 0, "text": "Testimonials:"}},
                {"updateTextStyle": {"objectId": "testimonials_title", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 25, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,bold,foregroundColor"}},
                {"createShape": {"objectId": "testimonials_text", "shapeType": "TEXT_BOX", "elementProperties": {
                    "pageObjectId": "testimonials_slide",
                    "size": {"height": {"magnitude": 600000, "unit": "EMU"}, "width": {"magnitude": 8000000, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 900000, "unit": "EMU"}
                }}},
                {"insertText": {
                    "objectId": "testimonials_text",
                    "insertionIndex": 0,
                    "text": "\n\n".join([f"“{t.get('quote', '')}”\n — {t.get('author', '')}, {t.get('title', '')}" for t in testimonials])
                }},
                {"updateTextStyle": {"objectId": "testimonials_text", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 14, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,foregroundColor"}},
            ]

        # --- FORMAT & CONTACT SLIDE (Conditional) ---
        qr_code_path = booking_contact.get('qr_code_path')
        qr_code_url = ""
        if qr_code_path:
            qr_code_url = qr_code_path if qr_code_path else None

        if formats_offered or email or website or qr_code_url: # Condition for the entire slide
            requests_data += [
                {"createSlide": {"objectId": "contact_slide", "slideLayoutReference": {"predefinedLayout": "BLANK"}}},
                {"createImage": {"objectId": "contact_bg", "url": bg_image_url, "elementProperties": {
                    "pageObjectId": "contact_slide",
                    "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
                }}},
                {"createShape": {"objectId": "contact_overlay", "shapeType": "RECTANGLE", "elementProperties": {
                    "pageObjectId": "contact_slide",
                    "size": {"height": {"magnitude": SLIDE_HEIGHT, "unit": "EMU"}, "width": {"magnitude": SLIDE_WIDTH, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"}
                }}},
                {"updateShapeProperties": {
                    "objectId": "contact_overlay",
                    "shapeProperties": {
                        "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": {"red": 0, "green": 0, "blue": 0}}, "alpha": 0.55}}
                    },
                    "fields": "shapeBackgroundFill.solidFill.color,shapeBackgroundFill.solidFill.alpha"
                }},
                # Formats Offered Section (Conditional)
                *(
                    [
                        {"createShape": {"objectId": "formats_title", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "contact_slide",
                            "size": {"height": {"magnitude": 120000, "unit": "EMU"}, "width": {"magnitude": 8000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 300000, "unit": "EMU"}
                        }}},
                        {"insertText": {"objectId": "formats_title", "insertionIndex": 0, "text": "Formats Offered:"}},
                        {"updateTextStyle": {"objectId": "formats_title", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 25, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,bold,foregroundColor"}},
                        {"createShape": {"objectId": "formats_text", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "contact_slide",
                            "size": {"height": {"magnitude": 300000, "unit": "EMU"}, "width": {"magnitude": 8000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 900000, "unit": "EMU"}
                        }}},
                        {"insertText": {
                            "objectId": "formats_text",
                            "insertionIndex": 0,
                            "text": "• " + "\n• ".join(formats_offered)
                        }},
                        {"updateTextStyle": {"objectId": "formats_text", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 14, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,foregroundColor"}}
                    ] if formats_offered else []
                ),
                # Contact Info Title (Conditional)
                *(
                    [
                        {"createShape": {"objectId": "contact_info_title", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "contact_slide",
                            "size": {"height": {"magnitude": 120000, "unit": "EMU"}, "width": {"magnitude": 8000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 2700000, "unit": "EMU"}
                        }}},
                        {"insertText": {"objectId": "contact_info_title", "insertionIndex": 0, "text": "Booking Contact:"}},
                        {"updateTextStyle": {"objectId": "contact_info_title", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 25, "unit": "PT"}, "bold": True, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,bold,foregroundColor"}},
                    ] if email or website else []
                ),
                # Contact Email (Conditional)
                *(
                    [
                        {"createShape": {"objectId": "contact_email_text", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "contact_slide",
                            "size": {"height": {"magnitude": 50000, "unit": "EMU"}, "width": {"magnitude": 4000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 3100000, "unit": "EMU"}
                        }}},
                        {"insertText": {
                            "objectId": "contact_email_text",
                            "insertionIndex": 0,
                            "text": f"Email: {email}"
                        }},
                        {"updateTextStyle": {"objectId": "contact_email_text", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 14, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,foregroundColor"}},
                    ] if email else []
                ),
                # Contact Website (Conditional)
                *(
                    [
                        {"createShape": {"objectId": "contact_website_text", "shapeType": "TEXT_BOX", "elementProperties": {
                            "pageObjectId": "contact_slide",
                            "size": {"height": {"magnitude": 50000, "unit": "EMU"}, "width": {"magnitude": 4000000, "unit": "EMU"}},
                            "transform": {"scaleX": 1, "scaleY": 1, "translateX": 400000, "translateY": 3500000, "unit": "EMU"}
                        }}},
                        {"insertText": {
                            "objectId": "contact_website_text",
                            "insertionIndex": 0,
                            "text": f"Website: {website}"
                        }},
                        {"updateTextStyle": {"objectId": "contact_website_text", "textRange": {"type": "ALL"}, "style": {"fontSize": {"magnitude": 14, "unit": "PT"}, "foregroundColor": {"opaqueColor": {"rgbColor": {"red": 1, "green": 1, "blue": 1}}}}, "fields": "fontSize,foregroundColor"}},
                    ] if website else []
                )
            ]
            if qr_code_url: # QR code is conditional too
                requests_data.append({"createImage": {"objectId": "qr_code_image", "url": qr_code_url, "elementProperties": {
                    "pageObjectId": "contact_slide",
                    "size": {"height": {"magnitude": 1000000, "unit": "EMU"}, "width": {"magnitude": 1000000, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 6500000, "translateY": 3900000, "unit": "EMU"}
                }}})

        print("Executing slide creation...")
        batch_update_url = f"https://slides.googleapis.com/v1/presentations/{presentation_id}:batchUpdate"
        batch_body = {"requests": requests_data}
        response = requests.post(batch_update_url, headers=headers, json=batch_body)
        
        if response.status_code not in (200, 201):
            raise Exception(f"Failed to create slides: {response.status_code} - {response.text}")

        # Set public access permissions
        drive_url = f"https://www.googleapis.com/drive/v3/files/{presentation_id}/permissions"
        permission_body = {
            "role": "writer",
            "type": "anyone"
        }
        perm_response = requests.post(drive_url, headers=headers, json=permission_body)
        
        if perm_response.status_code not in (200, 201):
            raise Exception(f"Failed to set permissions: {perm_response.status_code} - {perm_response.text}")
        
        slides_url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
        return presentation_id, slides_url
        
    except Exception as e:
        print(f"Error in create_speaker_kit_slides: {e}")
        import traceback
        traceback.print_exc()
        raise e