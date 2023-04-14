import cv2
import mss
import os
from datetime import datetime

VIDEO_INTERVAL = 1
SCREENSHOT_SAVE_INTERVAL = 60 * 10  # 10 minutes
OCR_INTERVAL = 5

def create_video_writer(display_num, monitor):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"output/{timestamp}_D{display_num}.mp4"
    filepath = os.path.join(os.getcwd(), filename)
    width, height = monitor['width'], monitor['height']
    print(f"VID {display_num}: Creating video writer for display in {filename}...")
    return cv2.VideoWriter(filepath, fourcc, VIDEO_INTERVAL, (width, height))

# Add this function to the script
def get_monitors():
    with mss.mss() as sct:
        return sct.monitors[1:]  # Skip the first item which represents all monitors combined

