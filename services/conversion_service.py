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




def batch_convert_folder(folder_path, output_format, output_dir=None):
    import logging
    logging.basicConfig(level=logging.DEBUG)

    results = []

    if output_dir is None:
        output_dir = os.path.join(folder_path, "converted_output")

    os.makedirs(output_dir, exist_ok=True)
    output_ext = f".{output_format.lower()}"

    logging.debug(f"Scanning folder: {folder_path}")
    logging.debug(f"Saving output to: {output_dir}")

    for filename in os.listdir(folder_path):
        full_path = os.path.join(folder_path, filename)

        if os.path.isdir(full_path):
            logging.debug(f"[SKIP] {filename} is a directory.")
            continue

        name, ext = os.path.splitext(filename)
        ext = ext.lower()

        logging.debug(f"Found file: {filename} (ext: {ext})")

        if ext not in SUPPORTED_IMAGE_FORMATS + SUPPORTED_VIDEO_FORMATS:
            logging.debug(f"[SKIP] {filename} is not a supported format.")
            continue

        if name.endswith("_converted"):
            logging.debug(f"[SKIP] {filename} already converted.")
            continue

        if ext in SUPPORTED_IMAGE_FORMATS:
            result = convert_image(full_path, output_format, output_dir=output_dir)
        else:
            result = convert_video(full_path, output_format, output_dir=output_dir)

        if isinstance(result, str) and result.endswith(output_ext):
            results.append({"result": result})
        else:
            results.append({"error": result})

    return results
