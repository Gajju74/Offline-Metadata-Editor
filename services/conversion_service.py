import os
from ui.conversion import (
    convert_image,
    convert_video,
    SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_VIDEO_FORMATS,
)

def is_supported_format(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    return ext in SUPPORTED_IMAGE_FORMATS + SUPPORTED_VIDEO_FORMATS

def run_conversion(file_path, output_format, strip_metadata=False, custom_metadata=None):
    ext = os.path.splitext(file_path)[1].lower()

    if ext in SUPPORTED_IMAGE_FORMATS:
        result = convert_image(
            input_path=file_path,
            output_format=output_format,
            strip_metadata=strip_metadata
        )
        return {"type": "image", "result": result}

    elif ext in SUPPORTED_VIDEO_FORMATS:
        result = convert_video(
            input_path=file_path,
            output_format=output_format,
            strip_metadata=strip_metadata,
            custom_metadata=custom_metadata
        )
        return {"type": "video", "result": result}

    else:
        return {"error": f"Unsupported file format: {ext}"}

def batch_convert_folder(folder_path, output_format):
    results = []
    output_ext = f".{output_format.lower()}"

    for filename in os.listdir(folder_path):
        full_path = os.path.join(folder_path, filename)
        name, ext = os.path.splitext(filename)

        # Skip non-supported files
        if ext.lower() not in SUPPORTED_IMAGE_FORMATS + SUPPORTED_VIDEO_FORMATS:
            continue

        # ✅ Skip already-converted files
        if name.endswith("_converted"):
            continue

        if ext.lower() in SUPPORTED_IMAGE_FORMATS:
            result = convert_image(full_path, output_format)
        else:
            result = convert_video(full_path, output_format)

        if isinstance(result, str) and result.endswith(output_ext):
            results.append({"result": result})
        else:
            results.append({"error": result})

    return results