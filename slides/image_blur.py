# slides/image_blur.py

from PIL import Image, ImageFilter
from io import BytesIO
import requests
import os

def blur_and_save_image_from_url(image_url: str, save_path: str, blur_radius: int = 10):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")
        blurred_image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        blurred_image.save(save_path)
    except Exception as e:
        raise RuntimeError(f"Failed to blur image from {image_url}: {e}")
