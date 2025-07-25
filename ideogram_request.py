import os




def get_background_image(section2:str):
    import requests

    # Generate with Ideogram 3.0 (POST /v1/ideogram-v3/generate)
    response = requests.post(
    "https://api.ideogram.ai/v1/ideogram-v3/generate",
    headers={
        "Api-Key": os.environ.get('IDEOGRAM_API_KEY')
    },
    json={
        "prompt":section2+"Create a background image for a speaker's kit that aligns with my brand’s tone and visual aesthetic. Do not include any human faces in the image. This is very important — no faces, no facial features, no depictions of people in any form. The artwork must contain text. Focus on abstract, thematic, or brand-aligned visual elements only — again, absolutely no human faces",
        "rendering_speed": "TURBO"
    }
    )
 
    print(response.json()) 
    return ( (response.json()['data'][0]['url']))

import os


def get_background_image(theme:str,style:str, aspect_ratio: str = "16x9"):
    import requests

    # Generate with Ideogram 3.0 (POST /v1/ideogram-v3/generate)
    response = requests.post(
    "https://api.ideogram.ai/v1/ideogram-v3/generate",
    headers={
        "Api-Key": os.environ.get('IDEOGRAM_API_KEY')
    },
    json={
        "prompt": f"""
            Create a high-resolution, professional background image. Theme: {theme}, Style: {style} Absolutely DO NOT include: any words, letters, numbers, symbols, or recognizable text; any logos, branding, or iconography; any humans, faces, body parts, or silhouettes. Focus on: abstract elements like soft geometric forms, circuits, holographic rings, flowing lines, or tech-like particle systems; a modern color palette fitting a futuristic design (e.g., soft purples, cyans, silvers); clear negative space for content overlays — balance and simplicity are key. Image must be text-free, logo-free, and people-free. The final result should look like a clean, versatile digital design background — not a poster or ad.
        """,
        "rendering_speed": "TURBO",
        "aspect_ratio": aspect_ratio
    }
    )
    
    print(response.json()) 
    return ( (response.json()['data'][0]['url']))
