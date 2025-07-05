from PIL import Image, ExifTags
import os

def read_image_metadata(file_path):
    metadata = {}

    try:
        img = Image.open(file_path)
        exif_data = img._getexif()

        if exif_data:
            for tag, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag, tag)

                if tag_name == "GPSInfo" and isinstance(value, dict):
                    gps_data = {}
                    for t in value:
                        sub_tag = ExifTags.GPSTAGS.get(t, t)
                        gps_data[sub_tag] = value[t]
                    metadata["GPSInfo"] = gps_data
                else:
                    metadata[tag_name] = value

        # Add basic image info
        metadata["File Name"] = os.path.basename(file_path)
        metadata["Format"] = img.format
        metadata["Mode"] = img.mode
        metadata["Image Size"] = f"{img.width} x {img.height}"
        metadata["File Size (KB)"] = round(os.path.getsize(file_path) / 1024, 2)

    except Exception as e:
        metadata["Error"] = str(e)

    return metadata

def write_image_metadata(input_path, metadata_updates, output_path):
    try:
        img = Image.open(input_path)
        exif_data = img.getexif()

        # Get original format (e.g., JPEG)
        image_format = img.format or 'JPEG'
        ext = os.path.splitext(output_path)[1].lower()

        # If no extension, add default
        if not ext:
            output_path += ".jpg"
            ext = ".jpg"

        # Map tag names to tag IDs
        reverse_tags = {v: k for k, v in ExifTags.TAGS.items()}

        for field, value in metadata_updates.items():
            tag_id = reverse_tags.get(field)
            if tag_id:
                exif_data[tag_id] = value

        img.save(output_path, format=image_format, exif=exif_data)
        return True

    except Exception as e:
        print(f"❌ Error saving metadata: {e}")
        return False
