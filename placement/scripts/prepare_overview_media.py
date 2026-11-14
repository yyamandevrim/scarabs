"""Create native-sized Overview derivatives from the archived event clip.

Usage: python prepare_overview_media.py SOURCE_EVENT.webm OUTPUT_DIRECTORY
Requires ffmpeg and Pillow. The source is not copied into the public directory.
"""
from pathlib import Path
import subprocess
import sys
from io import BytesIO
from PIL import Image

source, output = map(Path, sys.argv[1:3])
output.mkdir(parents=True, exist_ok=True)
clip = output / 'event-clip.mp4'
subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
                '-vf', 'crop=640:280:0:80,fps=15', '-an', '-c:v', 'libx264',
                '-crf', '24', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(clip)], check=True)
# One second into the same record gives a legible smoke view; no pixels are repainted.
frame = subprocess.check_output(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-ss', '1',
                                 '-i', str(clip), '-frames:v', '1', '-f', 'image2pipe',
                                 '-vcodec', 'png', '-'])
Image.open(BytesIO(frame)).save(output / 'event-frame.webp', quality=85, method=6)
