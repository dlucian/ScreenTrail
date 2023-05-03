import os
import mss
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID, kCGWindowListExcludeDesktopElements
from AppKit import NSScreen
from datetime import datetime
from PIL import Image

def get_monitors():
    with mss.mss() as sct:
        for i, monitor in enumerate(sct.monitors[1:], start=0):
            print(f"Got monitor {i} / {monitor}...")
        return sct.monitors[1:]  # Skip the first item which represents all monitors combined

# https://www.appsloveworld.com/cplus/100/619/nsscreen-not-updating-monitor-count-when-new-monitors-are-plugged-in?utm_content=cmp-true
def get_screen_scale_factors():
    return [screen.backingScaleFactor() for screen in NSScreen.screens()]

def get_foreground_window():
    window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly | kCGWindowListExcludeDesktopElements, kCGNullWindowID)
    for window in window_list:
        if window.get('kCGWindowLayer') == 0 and window.get('kCGWindowIsOnscreen', False):
            return {
                'name': window.get('kCGWindowName', 'Unknown'),
                'x': window['kCGWindowBounds']['X'],
                'y': window['kCGWindowBounds']['Y'],
                'width': window['kCGWindowBounds']['Width'],
                'height': window['kCGWindowBounds']['Height']
            }
    return None

def capture_desktop():
    images = []
    with mss.mss() as sct:
        for i, monitor in enumerate(sct.monitors[1:], start=0):
            monitor['left'], monitor['top'], monitor['width'], monitor['height']
            sct_img = sct.grab(monitor)
            image = Image.frombytes('RGB', sct_img.size, sct_img.rgb)
            images.append((i, image))
    return images

def save_image(image):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"output/{timestamp}.png"
    filepath = os.path.join(os.getcwd(), filename)
    image.save(filepath)

def get_relative_scale_factors():
    screens = NSScreen.screens()

    # cannot use NSScreen.mainScreen() as is not necessarily the screen with the menu bar
    # https://stackoverflow.com/a/864432/2472348
    main_screen = screens[0];
    main_screen_size = main_screen.frame().size

    relative_scale_factors = []

    for screen in screens:
        screen_size = screen.frame().size
        scale_width = screen_size.width / main_screen_size.width
        scale_height = screen_size.height / main_screen_size.height
        relative_scale_factors.append((scale_width, scale_height))

    return relative_scale_factors

def get_foreground_display_num(foreground_window, screens):
    relative_scale_factors = get_relative_scale_factors()

    print("Relative scale factors:", relative_scale_factors)
    print("Screens:", screens)

    for display_num, screen in enumerate(screens):
        print(f"Display {display_num}: {screen}")
        scale_width, scale_height = relative_scale_factors[display_num]
        x, y, width, height = screen['left'], screen['top'], screen['width'] * scale_width, screen['height'] * scale_height
        fx, fy, fw, fh = foreground_window['x'], foreground_window['y'], foreground_window['width'] * scale_width, foreground_window['height'] * scale_height
        if x <= fx < x + width and y <= fy < y + height:
            return display_num
    return None
