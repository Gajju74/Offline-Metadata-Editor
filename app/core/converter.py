
import ffmpeg
from PIL import Image

def convert_image(input_path, output_path, format="JPEG"):
    img = Image.open(input_path)
    img.save(output_path, format=format)

def convert_video(input_path, output_path, codec="libx264"):
    ffmpeg.input(input_path).output(output_path, vcodec=codec).run()
