import subprocess
import os
from pathlib import Path

def list_fonts(font_dir):
    """List and yield paths of font files in the given directory."""
    for root, _, files in os.walk(font_dir):
        for file in files:
            if file.endswith(('.ttf', '.otf', '.ttc')):
                yield os.path.join(root, file)

def generate_preview_video(font_path, output_path):
    """Generate a preview video for a given font using FFmpeg."""
    font_name = os.path.basename(font_path).split('.')[0]
    command = (
        f"ffmpeg -f lavfi -i color=c=white:s=640x480:d=5 "
        f"-vf \"drawtext=fontfile={font_path}:text='Sample Text\n{font_name}':fontsize=48:fontcolor=black:x=(w-text_w)/2:y=(h-text_h)/2\" "
        f"-y {output_path}"
    )
    
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to create preview for {font_name}: {e}")

def main():
    # Font directory (adjust based on your system)
    font_dir = "/usr/share/fonts/truetype"
    output_dir = "font_previews"
    Path(output_dir).mkdir(exist_ok=True)

    for font in list_fonts(font_dir):
        output_file = os.path.join(output_dir, f"{os.path.basename(font).replace(' ', '_')}.mp4")
        generate_preview_video(font, output_file)
        print(f"Created preview for {os.path.basename(font)}")

if __name__ == "__main__":
    main()