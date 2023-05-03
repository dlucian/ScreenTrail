import cv2
import numpy
import objc
import threading
import os

from AppKit import NSApplication, NSNotificationCenter, NSStatusBar, NSMenu, NSMenuItem, NSImage
from common import get_screen_scale_factors, get_monitors, get_foreground_window, capture_desktop, get_foreground_display_num
from datetime import datetime, timedelta
from Foundation import NSObject, NSTimer, NSRunLoop, NSDefaultRunLoopMode

SCREENSHOT_SAVE_INTERVAL = 60 * 10  # 10 minutes
OCR_INTERVAL = 5
DIFF_THRESHOLD = 1000
VIDEO_INTERVAL = 1

def create_video_writer(display_num, monitor):
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = f"output/{timestamp}_D{display_num}.mp4"
    filepath = os.path.join(os.getcwd(), filename)
    width, height = monitor['width'], monitor['height']
    print(f"VID {display_num}: Creating video writer for display in {filename}...")
    return cv2.VideoWriter(filepath, fourcc, VIDEO_INTERVAL, (width, height))

class AppDelegate(NSObject):
    def applicationDidFinishLaunching_(self, notification):
        status_bar = NSStatusBar.systemStatusBar()
        self.status_item = status_bar.statusItemWithLength_(-1)

        # Set the icon for the status bar item
        # https://hetima.github.io/fucking_nsimage_syntax/
        icon = NSImage.imageNamed_("NSStatusAway")
        self.status_item.button().setImage_(icon)

        # Create a simple menu with a quit option
        menu = NSMenu.alloc().init()

        # Quit menu item
        quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "terminate:", "")
        menu.addItem_(quit_item)

        # Pause menu item
        pause_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Pause 5 minutes", "pause:", "")
        menu.insertItem_atIndex_(pause_item, 0)  # Insert at index 0, right above the "Quit" option

        # Set the menu for the status bar item
        self.status_item.setMenu_(menu)

        # Register for screen configuration change event
        notification_center = NSNotificationCenter.defaultCenter()
        notification_center.addObserver_selector_name_object_(self, "screenConfigurationChanged:", "NSApplicationDidChangeScreenParametersNotification", None)

    def applicationWillTerminate_(self, notification):
        self.timer_handler.release_video_writers()

    applicationWillTerminate_ = objc.selector(applicationWillTerminate_, signature=b'v@:@')

    def pause_(self, sender):
        is_paused = self.timer_handler.toggle_pause()
        if is_paused:
            sender.setTitle_("Resume")
            pause_icon = NSImage.imageNamed_("NSPauseTemplate")  # Use an appropriate icon here
            self.status_item.button().setImage_(pause_icon)
            print("Paused...")
        else:
            sender.setTitle_("Pause 5 minutes")
            normal_icon = NSImage.imageNamed_("NSStatusAway")
            self.status_item.button().setImage_(normal_icon)
            print("Resumed...")

    pause_ = objc.selector(pause_, signature=b'v@:@')

    def screenConfigurationChanged_(self, notification):
        with self.timer_handler.lock:  # Acquire the lock
            print("Screen configuration changed")
            self.timer_handler.screen_configuration_changed = True

    screenConfigurationChanged_ = objc.selector(screenConfigurationChanged_, signature=b'v@:@')

class TimerHandler(NSObject):
    def init(self):
        self = super(TimerHandler, self).init()
        if self:
            self.pause_end_time = datetime.min
            self.screen_configuration_changed = False
            self.refresh_video_writers()
            self.lock = threading.Lock()
        return self

    def start_timer(self):
        # Wrap timer-related code inside a separate thread
        def timer_thread():
            self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(OCR_INTERVAL, self, self.timer_callback_, None, True)
            NSRunLoop.currentRunLoop().addTimer_forMode_(self.timer, NSDefaultRunLoopMode)
            NSRunLoop.currentRunLoop().run()

        self.timer_thread = threading.Thread(target=timer_thread)
        self.timer_thread.start()

    def timer_callback_(self, timer):
        with self.lock:
            if self.screen_configuration_changed:
                self.refresh_video_writers()
                self.screen_configuration_changed = False

        if getattr(self, 'paused', False):
            if datetime.now() >= self.pause_end_time:
                self.toggle_pause()
        else:
            self.scale_factors = get_screen_scale_factors()
            captured_images = capture_desktop()
            for display_num, img in captured_images:
                if (datetime.now() - self.video_writer_start_times[display_num]).seconds >= SCREENSHOT_SAVE_INTERVAL:
                    print(f"Display {display_num}: {self.frame_count[display_num]} frames written.")
                    self.video_writers[display_num].release()
                    self.screens = get_monitors()
                    self.video_writers[display_num] = create_video_writer(display_num, self.screens[display_num])
                    self.video_writer_start_times[display_num] = datetime.now()
                    self.frame_count[display_num] = 0

                frame = cv2.cvtColor(numpy.array(img), cv2.COLOR_RGB2BGR)
                target_width, target_height = self.video_writer_dimensions[display_num]
                resized_frame = cv2.resize(frame, (int(target_width), int(target_height)), interpolation=cv2.INTER_AREA)

                self.video_writers[display_num].write(resized_frame)
                self.frame_count[display_num] += 1

    timer_callback_ = objc.selector(timer_callback_, signature=b'v@:@')

    def toggle_pause(self):
        self.paused = not getattr(self, 'paused', False)
        if self.paused:
            self.release_video_writers()
            pause_end_time = datetime.now() + timedelta(minutes=5)
            self.pause_end_time = pause_end_time
            print("Pausing for 5 minutes...")
        else:
            self.refresh_video_writers()
            print("Resuming recording...")

        return self.paused

    def release_video_writers(self):
        if not hasattr(self, 'video_writers'):
            return
        print("Releasing video writers...")
        for display_num, vw in enumerate(self.video_writers):
            print(f"Display {display_num}: {self.frame_count[display_num]} frames written.")
            vw.release()

    def refresh_video_writers(self):
        print("Refreshing video writers...")
        self.release_video_writers()
        self.screens = get_monitors()
        self.video_writers = [create_video_writer(i, screen) for i, screen in enumerate(self.screens)]
        self.video_writer_start_times = [datetime.now()] * len(self.screens)
        self.video_writer_dimensions = [(int(screen['width']), int(screen['height'])) for screen in self.screens]
        self.frame_count = [0] * len(self.screens)
        self.previous_images = [None] * len(self.screens)
        self.frame_count = [0] * len(self.screens)
        self.previous_images = [None] * len(self.screens)

def main():
    if not os.path.exists("output"):
        os.makedirs("output")

    print("Running...")
    handler = TimerHandler.alloc().init()
    handler.start_timer()  # Start the timer thread
    NSApp = NSApplication.sharedApplication()
    NSApp.setActivationPolicy_(1)  # NSApplication.ActivationPolicy.accessory
    delegate = AppDelegate.alloc().init()
    delegate.timer_handler = handler
    NSApp.setDelegate_(delegate)
    NSApp.activateIgnoringOtherApps_(True)
    NSApp.run()

    # Release all VideoWriter instances after the app is stopped
    for vw in handler.video_writers:
        vw.release()

if __name__ == "__main__":
    main()
