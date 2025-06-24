
import os

def is_valid_file(file_path):
    return os.path.exists(file_path) and os.path.isfile(file_path)
