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
