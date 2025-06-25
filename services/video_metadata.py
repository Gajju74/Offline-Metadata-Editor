# services/video_metadata.py
import subprocess
import json
import os
import shutil

# Auto-detect exiftool path or use fallback
EXIFTOOL_PATH = shutil.which("exiftool") or "C:/ExifTool/exiftool.exe"

def read_video_metadata(file_path):
    metadata = {}

    try:
        # Run exiftool and get all metadata
        result = subprocess.run(
            [EXIFTOOL_PATH, "-json", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        output = result.stdout.decode()
        data = json.loads(output)[0]  # exiftool returns a list of dicts

        # Use all metadata fields
        metadata.update(data)

        # Add file size in MB (not included in exiftool reliably)
        metadata["File Size (MB)"] = round(os.path.getsize(file_path) / (1024 * 1024), 2)

    except Exception as e:
        metadata["Error"] = f"ExifTool failed: {e}"

    return metadata
