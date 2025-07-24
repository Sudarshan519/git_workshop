# slides/image_blur.py

from PIL import Image, ImageFilter
from io import BytesIO
import requests
import os

def blur_and_save_image_from_url(image_url: str, output_path: str, blur_radius: int = 15):
    response = requests.get(image_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download image: {image_url}")

    img = Image.open(BytesIO(response.content)).convert("RGB")
    blurred = img.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    blurred.save(output_path)
    return output_path
