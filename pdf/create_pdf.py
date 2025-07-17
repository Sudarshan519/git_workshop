import json
import requests
from google_cred import access_token

def add_text_slides_from_json(presentation_id, access_token, json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        pages = json.load(f)

    batch_update_url = f"https://slides.googleapis.com/v1/presentations/{presentation_id}:batchUpdate"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    # Step 1: Create all slides (no objectId)
    create_slide_requests = []
    for idx in range(len(pages)):
        create_slide_requests.append({
            "createSlide": {
                "insertionIndex": idx,
                "slideLayoutReference": {
                    "predefinedLayout": "BLANK"
                }
            }
        })
    batch_body = {"requests": create_slide_requests}
    response = requests.post(batch_update_url, headers=headers, json=batch_body)
    if response.status_code not in (200, 201):
        print("Failed to create slides:", response.status_code, response.text)
        return

    # Step 2: Fetch the presentation to get real slide IDs
    pres_url = f"https://slides.googleapis.com/v1/presentations/{presentation_id}"
    pres_resp = requests.get(pres_url, headers=headers)
    if pres_resp.status_code != 200:
        print("Failed to fetch presentation:", pres_resp.status_code, pres_resp.text)
        return
    slides = pres_resp.json().get('slides', [])
    slide_ids = [slide['objectId'] for slide in slides]

    # Step 3: Add text boxes to each slide using real IDs
    add_text_requests = []
    for idx, page in enumerate(pages):
        if idx >= len(slide_ids):
            break
        slide_id = slide_ids[idx]
        text_id = f"text_{idx+1}"
        add_text_requests.append({
            "createShape": {
                "objectId": text_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {
                        "height": {"magnitude": 400, "unit": "PT"},
                        "width": {"magnitude": 600, "unit": "PT"}
                    },
                    "transform": {
                        "scaleX": 1, "scaleY": 1, "translateX": 50, "translateY": 50, "unit": "PT"
                    }
                }
            }
        })
        add_text_requests.append({
            "insertText": {
                "objectId": text_id,
                "insertionIndex": 0,
                "text": page['text']
            }
        })
    if add_text_requests:
        batch_body = {"requests": add_text_requests}
        response = requests.post(batch_update_url, headers=headers, json=batch_body)
        if response.status_code in (200, 201):
            print("Slides created from PDF content!")
        else:
            print("Failed to add text to slides:", response.status_code, response.text)


def create_pdf_file():
    # API endpoint
    url = 'https://slides.googleapis.com/v1/presentations'
    # Example request body (customize as needed)
    headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json'
    }

    body = {
        "title": "Python API Demo Presentation",
        "pageSize": {
            "width": {
                "magnitude": 9144000,  # 10 inches in EMUs
                "unit": "EMU"
            },
            "height": {
                "magnitude": 6858000,  # 7.5 inches in EMUs
                "unit": "EMU"
            }
        },
        "locale": "en-US"
    }
    response = requests.post(url, headers=headers, json=body)
