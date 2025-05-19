import os
import sys
import tkinter as tk
from ui import SquadQueueMonitorUI
from language import get_text


def main():
    """
    Main application entry point
    """
    # Create necessary directories
    os.makedirs("translations", exist_ok=True)
    os.makedirs("debug", exist_ok=True)
    os.makedirs("assets", exist_ok=True)

    # Create root window
    root = tk.Tk()
    app = SquadQueueMonitorUI(root)

    # Start the main loop
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Unhandled exception: {e}")
        sys.exit(1)
