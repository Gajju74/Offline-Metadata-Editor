# services/image_metadata.py
import subprocess
import json
import os
from PIL import Image, ExifTags

def read_image_metadata(file_path):
    metadata = {}

    try:
        # Try exiftool first
        result = subprocess.run(
            ["exiftool", "-json", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        output = result.stdout.decode()
        data = json.loads(output)[0]

        metadata.update(data)
        metadata["File Size (MB)"] = round(os.path.getsize(file_path) / (1024 * 1024), 2)

    except Exception as e:
        # Fallback to Pillow
        metadata["Warning"] = f"ExifTool failed: {e}. Using basic EXIF data."

        try:
            img = Image.open(file_path)
            exif_data = img.getexif()

            if exif_data:
                for tag, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag, tag)
                    metadata[tag_name] = value

            metadata["Format"] = img.format
            metadata["Mode"] = img.mode
            metadata["Size"] = f"{img.width} x {img.height}"
            metadata["File Size (MB)"] = round(os.path.getsize(file_path) / (1024 * 1024), 2)

        except Exception as fallback_err:
            metadata["Error"] = str(fallback_err)

    return metadata
