import os
import time
import pytesseract
import mss
from datetime import datetime, timedelta
from math import floor
import numpy as np
from PIL import Image, ImageChops
from common import save_image, get_screen_scale_factors, get_foreground_window, capture_desktop, get_foreground_display_num

DIFF_THRESHOLD = 1000
OCR_INTERVAL = 5

def process_ocr(image, foreground_window, scale_factor, target_screen):
    screen_x, screen_y = target_screen['left'], target_screen['top']
    x, y, width, height = int(foreground_window['x']), int(foreground_window['y']), int(foreground_window['width']), int(foreground_window['height'])
    x, y, width, height = int((x - screen_x) * scale_factor), int((y - screen_y) * scale_factor), int(width * scale_factor), int(height * scale_factor)
    cropped_image = image.crop((x, y, x + width, y + height))
    custom_config = r'--psm 3'
    print(f"Processing OCR for {foreground_window['name']}...", target_screen, scale_factor, (x, y, width, height))
    text = pytesseract.image_to_string(cropped_image, config=custom_config)
    return text

def image_difference(img1, img2):
    diff = ImageChops.difference(img1, img2)
    diff_array = np.array(diff)
    return np.sum(diff_array)

written_lines = set()

def write_ocr_output(ocr_text):
    global written_lines
    timestamp = datetime.now()
    rounded_minute = floor(timestamp.minute / 10) * 10
    timestamp_str = timestamp.strftime('%Y-%m-%d_%H-') + f"{rounded_minute:02}" + "-00"
    filename = f"output/{timestamp_str}.txt"
    filepath = os.path.join(os.getcwd(), filename)

    with open(filepath, 'a') as f:
        lines = ocr_text.splitlines()
        for line in lines:
            if line not in written_lines:
                f.write(line + '\n')
                written_lines.add(line)

def get_monitors():
    with mss.mss() as sct:
        return sct.monitors[1:]  # Skip the first item which represents all monitors combined

def ocr_loop():
    screens = get_monitors()
    previous_images = [None] * len(screens)
    scale_factors = get_screen_scale_factors()

    while True:
        time.sleep(OCR_INTERVAL)
        screens = get_monitors()
        captured_images = capture_desktop()
        foreground_window = get_foreground_window()

        if foreground_window:
            # Get the display number of the active screen where the foreground window is located
            target_monitor = get_foreground_display_num(foreground_window, screens)

            if target_monitor is not None:
                img = captured_images[target_monitor][1]
                display_num = captured_images[target_monitor][0]

                prev_image = previous_images[display_num]
                if prev_image is not None and image_difference(prev_image, img) < DIFF_THRESHOLD:
                    continue

                previous_images[display_num] = img
                ocr_text = process_ocr(img, foreground_window, scale_factors[target_monitor], screens[target_monitor])
                if ocr_text:
                    write_ocr_output(ocr_text, foreground_window)
