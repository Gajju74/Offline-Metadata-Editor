import os
from PIL import Image
from PIL.ExifTags import TAGS
import pyheif
import subprocess
import json

def is_image(file_path):
    return file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.heic'))

def is_video(file_path):
    return file_path.lower().endswith(('.mp4', '.mov', '.avi'))

def read_image_metadata(file_path):
    if file_path.lower().endswith('.heic'):
        heif_file = pyheif.read(file_path)
        metadata = {}
        for item in heif_file.metadata or []:
            metadata[item['type']] = item['data']
        return metadata

    image = Image.open(file_path)
    exif_data = image.getexif()
    metadata = {}

    for tag_id, value in exif_data.items():
        tag = TAGS.get(tag_id, tag_id)
        metadata[tag] = value

    return metadata

def read_video_metadata(file_path):
    try:
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration:format_tags",
            "-of", "json",
            file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return json.loads(result.stdout)
    except Exception as e:
        return {"error": str(e)}


def get_metadata(file_path):
    if not os.path.exists(file_path):
        return {"error": "File does not exist"}

    if is_image(file_path):
        return {"type": "image", "metadata": read_image_metadata(file_path)}

    if is_video(file_path):
        return {"type": "video", "metadata": read_video_metadata(file_path)}

    return {"error": "Unsupported file type"}