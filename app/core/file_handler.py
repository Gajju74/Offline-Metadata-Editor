
import os

def is_supported_image(file_path):
    return file_path.lower().endswith(('.jpg', '.jpeg', '.png'))

def is_supported_video(file_path):
    return file_path.lower().endswith(('.mp4', '.avi', '.mov'))

def list_files(directory):
    return [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
