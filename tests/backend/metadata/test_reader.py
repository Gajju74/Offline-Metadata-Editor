# tests/backend/metadata/test_reader.py

import os
from backend.app.metadata.reader import get_metadata

def test_image_metadata():
    sample_image = "samples/sample.jpg"  # Provide a path to a sample image
    if not os.path.exists(sample_image):
        print("Sample image not found:", sample_image)
        return

    result = get_metadata(sample_image)
    print("Image metadata:", result)

def test_video_metadata():
    sample_video = "samples/sample.mp4"  # Provide a path to a sample video
    if not os.path.exists(sample_video):
        print("Sample video not found:", sample_video)
        return

    result = get_metadata(sample_video)
    print("Video metadata:", result)

if __name__ == "__main__":
    test_image_metadata()
    test_video_metadata()
