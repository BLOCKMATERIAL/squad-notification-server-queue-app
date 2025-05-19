import time
from language import get_text

# Try to import winsound for sound notifications
try:
    import winsound
    winsound_available = True
except ImportError:
    print(get_text("sound_warning"))
    winsound_available = False

# Try to import win10toast for Windows notifications
try:
    from win10toast import ToastNotifier
    toaster = ToastNotifier()
    toast_available = True
except ImportError:
    print("WARNING: win10toast module not available. Toast notifications disabled.")
    toast_available = False


def send_notification():
    """
    Send notification that user has entered the server
    """
    try:
        # Sound notification if available
        if winsound_available:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)

            # Play sound multiple times to ensure user doesn't miss notification
            for _ in range(3):
                time.sleep(1)
                winsound.PlaySound("SystemHand", winsound.SND_ALIAS)

        # Windows toast notification if available
        if toast_available:
            toaster.show_toast(
                "Squad Queue Monitor",
                get_text("entered_server"),
                duration=10,
                threaded=True  # Run in separate thread
            )

    except Exception as e:
        print(f"Error sending notification: {e}")