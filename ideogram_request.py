import os


def get_background_image(section2:str, aspect_ratio: str = "16x9"):
    import requests

    # Generate with Ideogram 3.0 (POST /v1/ideogram-v3/generate)
    response = requests.post(
    "https://api.ideogram.ai/v1/ideogram-v3/generate",
    headers={
        "Api-Key": "3OxovSLIcSdX6F3Pjk_uNcWXrTxmPDuzM8Xnu8TkiZY1xO4zqhq2vl2Im6O_aDSM6yRqHBCrXaRpt1l0biMVWQ"
    },
    json={
        "prompt":section2+"""
            Ideogram Setup:
            Model: 2.0 
            MP (Magic Prompt): ON
            Style: General
            Color: Auto

            Prompt:
            Create a high-resolution, professional background image.
            Theme: [user input from section 2 Question 7] 
            Style: [user input from section 2 Question 8] 

            Absolutely DO NOT include:
            - Any words, letters, numbers, symbols, or recognizable text  
            - Any logos, branding, or iconography  
            - Any humans, faces, body parts, or silhouettes  

            Focus on:
            - Abstract elements like soft geometric forms, circuits, holographic rings, flowing lines, or tech-like particle systems  
            - A modern color palette fitting a futuristic design (e.g., soft purples, cyans, silvers)  
            - Clear negative space for content overlays — balance and simplicity are key

            Create a blurred image with the blur_radius of 6–10

            Image must be **text-free**, **logo-free**, and **people-free**.  
            The final result should look like a clean, versatile digital design background — **not a poster or ad**.
        """,
        "rendering_speed": "TURBO",
        "aspect_ratio": aspect_ratio
    }
    )
    # print(response.json())
    # with open('output.png', 'wb') as f:
    # f.write(requests.get(response.json()['data'][0]['url']).content)

    # Generate with style reference images
    # response = requests.post(
    # "https://api.ideogram.ai/v1/ideogram-v3/generate",
    # headers={
    #     "Api-Key": "3OxovSLIcSdX6F3Pjk_uNcWXrTxmPDuzM8Xnu8TkiZY1xO4zqhq2vl2Im6O_aDSM6yRqHBCrXaRpt1l0biMVWQ"
    # },
    # data={
    #     "prompt":section2,
    #     "aspect_ratio": "3x1"
    # },
    # files=[
    #     # ("style_reference_images", open("style_reference_image_1.png", "rb")),
    #     # ("style_reference_images", open("style_reference_image_2.png", "rb")),
    # ]
    # )
    print(response.json()) 
    return ( (response.json()['data'][0]['url']))
