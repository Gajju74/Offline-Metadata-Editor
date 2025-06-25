# ui/conversion.py
import os
import subprocess
from PIL import Image


# Import HEIF support
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pillow_heif = None

SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png", ".heic"]
SUPPORTED_VIDEO_FORMATS = [".mp4", ".mov", ".avi", ".mkv"]

def convert_image(input_path, output_format="jpg", strip_metadata=False, output_dir=None):
    try:
        filename_wo_ext = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = output_dir or os.path.dirname(input_path)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{filename_wo_ext}_converted.{output_format}")

        with Image.open(input_path) as img:
            print(f"[DEBUG] Original mode: {img.mode}, Format: {img.format}")

            # Force RGB conversion for any format that doesn't support alpha
            if img.mode not in ["RGB", "L"]:
                img = img.convert("RGB")
                print(f"[DEBUG] Converted to RGB for format {output_format}")

            pil_format = "JPEG" if output_format.lower() in ["jpg", "jpeg"] else output_format.upper()

            # Special check for HEIC
            if pil_format == "HEIC" and not pillow_heif:
                raise Exception("HEIC output requires pillow-heif. Install it via `pip install pillow-heif`")

            if strip_metadata:
                data = list(img.getdata())
                img_no_meta = Image.new(img.mode, img.size)
                img_no_meta.putdata(data)
                img_no_meta.save(output_path, format=pil_format)
            else:
                img.save(output_path, format=pil_format)

            print(f"[SUCCESS] Saved converted image to {output_path}")
        return output_path if os.path.exists(output_path) else None

    except Exception as e:
        print(f"[ERROR] Image conversion failed for {input_path}: {e}")
        return f"Image conversion error: {e}"




def convert_video(input_path, output_format="mp4", strip_metadata=False, custom_metadata=None, output_dir=None):
    try:
        filename_wo_ext = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = output_dir or os.path.dirname(input_path)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{filename_wo_ext}_converted.{output_format}")

        cmd = ["ffmpeg", "-y", "-i", input_path]
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

