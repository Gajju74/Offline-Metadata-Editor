import ffmpeg


def read_video_metadata(file_path):
    """
    Reads metadata from a video file using ffmpeg.probe.
    Returns a dictionary of available metadata fields.
    """
    try:
        probe = ffmpeg.probe(file_path)
        format_info = probe.get("format", {})
        tags = format_info.get("tags", {})
        return tags
    except ffmpeg.Error as e:
        print("⚠️ FFmpeg Error:", e.stderr.decode() if hasattr(e, 'stderr') else str(e))
        return {}
    except Exception as e:
        print("⚠️ Unexpected Error:", str(e))
        return {}


def write_video_metadata(input_path, output_path, metadata_dict):
    """
    Writes metadata to a video file using ffmpeg.
    The video streams are copied without re-encoding.
    """
    try:
        args = []
        for key, value in metadata_dict.items():
            args.extend(["-metadata", f"{key}={value}"])

        (
            ffmpeg
            .input(input_path)
            .output(output_path, *args, c="copy")
            .overwrite_output()
            .run()
        )
        print(f"✅ Metadata written successfully to {output_path}")
    except ffmpeg.Error as e:
        print("⚠️ FFmpeg Write Error:", e.stderr.decode() if hasattr(e, 'stderr') else str(e))
    except Exception as e:
        print("⚠️ Unexpected Write Error:", str(e))
