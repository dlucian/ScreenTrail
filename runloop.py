import objc
from Foundation import NSObject, NSTimer, NSRunLoop, NSDefaultRunLoopMode
from AppKit import NSScreen, NSApplication, NSEvent, NSKeyDownMask

class TimerHandler(NSObject):
    def timer_callback_(self, timer):
        screens = NSScreen.screens()
        print("Screens:", screens)

    timer_callback_ = objc.selector(timer_callback_, signature=b'v@:@')

def main():
    # Set up the timer to call the timer_callback function every second
    handler = TimerHandler.alloc().init()
    timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(1.0, handler, handler.timer_callback_, None, True)

    # Add timer to the main run loop
    NSRunLoop.mainRunLoop().addTimer_forMode_(timer, NSDefaultRunLoopMode)

    # Set up an instance of NSApplication and activate it
    NSApp = NSApplication.sharedApplication()
    NSApp.setActivationPolicy_(0)  # NSApplicationActivationPolicyRegular

    print("Press 'q' to stop the script")

    # Add an event monitor to catch the key down event when 'q' is pressed
    def key_down_handler(event):
        if event.characters() == 'q':
            print("Exiting...")
            NSApp.stop_(None)

    monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(NSKeyDownMask, key_down_handler)

    # Run the main event loop
    NSApp.run()

if __name__ == "__main__":
    main()
