# ui/conversion.py
import os
import subprocess
from PIL import Image

SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".heic"]
SUPPORTED_VIDEO_FORMATS = [".mp4", ".mov", ".avi", ".mkv"]

def convert_image(input_path, output_format="jpg", strip_metadata=False):
    try:
        output_path = os.path.abspath(os.path.splitext(input_path)[0] + f"_converted.{output_format}")
        with Image.open(input_path) as img:
            if img.mode in ("RGBA", "LA"):
                img = img.convert("RGB")  # ✅ Remove alpha for JPEG

            if strip_metadata:
                data = list(img.getdata())
                img_no_meta = Image.new(img.mode, img.size)
                img_no_meta.putdata(data)
                img_no_meta.save(output_path)
            else:
                img.save(output_path)

        return output_path if os.path.exists(output_path) else None
    except Exception as e:
        return f"Image conversion error: {e}"


def convert_video(input_path, output_format="mp4", strip_metadata=False, custom_metadata=None):
    try:
        output_path = os.path.abspath(os.path.splitext(input_path)[0] + f"_converted.{output_format}")
        cmd = ["ffmpeg", "-y", "-i", input_path]  # -y to overwrite if exists

        if strip_metadata:
            cmd += ["-map_metadata", "-1"]
        elif custom_metadata:
            for k, v in custom_metadata.items():
                cmd += ["-metadata", f"{k}={v}"]

        cmd += ["-c", "copy", output_path]
        subprocess.run(cmd, check=True)
        return output_path if os.path.exists(output_path) else None
    except subprocess.CalledProcessError as e:
        return f"FFmpeg error: {e}"
    except Exception as e:
        return f"Video conversion error: {e}"
