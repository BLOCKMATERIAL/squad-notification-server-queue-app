import cv2
import numpy as np
import os
import win32gui
import win32ui
import win32con
import win32api
import win32process
import psutil  # For working with system processes
from ctypes import windll
from PIL import Image
from config import DEBUG_DIR, GAME_PROCESS_NAME


def is_game_running():
    """
    Check if the game process is running through the system process list
    """
    try:
        # Find the game process (SquadGame.exe or whatever it's called in the system)
        for proc in psutil.process_iter(['pid', 'name']):
            if GAME_PROCESS_NAME.lower() in proc.info['name'].lower():
                return True, proc.info['name'], proc.info['pid']
        return False, None, None
    except Exception as e:
        print(f"Error checking game process: {e}")
        return False, None, None


def find_game_window():
    """
    Find the game window using process information
    """
    game_running, process_name, pid = is_game_running()

    if not game_running:
        return None, None

    # If the game process is running, find the corresponding window
    def callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
            # Get the PID of the process that owns the window
            _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
            if window_pid == pid:
                title = win32gui.GetWindowText(hwnd)
                # Check window size (game window should be large)
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                if right - left > 300 and bottom - top > 200:
                    results.append((hwnd, title))
        return True

    results = []
    win32gui.EnumWindows(callback, results)

    # Choose the window with the largest area (probably the main game window)
    if results:
        results.sort(key=lambda x: get_window_area(x[0]), reverse=True)
        return results[0]

    return None, None


def get_window_area(hwnd):
    """
    Calculate window area
    """
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return (right - left) * (bottom - top)


def find_window_by_title(title_part):
    """
    Find window by part of title
    Returns: window handle and full title
    """

    def callback(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and title_part.lower() in title.lower():
                # Check if the window has non-zero dimensions (sign of a real application window)
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                if right - left > 100 and bottom - top > 100:  # Minimum size for a game window
                    results.append((hwnd, title))
        return True

    results = []
    win32gui.EnumWindows(callback, results)

    # Sort results: exact matches first, then by title length (shorter is better)
    if results:
        # Sort: exact matches first
        results.sort(key=lambda x: (x[1].lower() != title_part.lower(), len(x[1])))
        return results[0]

    return None, None


def capture_window(window_title=None):
    """
    Capture the content of the game window
    If window_title = None, try to find the window through the process
    """
    try:
        hwnd = None
        full_title = None

        # First try to find the window through the process
        game_hwnd, game_title = find_game_window()

        if game_hwnd:
            hwnd = game_hwnd
            full_title = game_title
            print(f"Found game window through process: '{full_title}'")
        # If not found through process and window_title is specified, use title search
        elif window_title:
            hwnd_from_title, title_from_title = find_window_by_title(window_title)
            if hwnd_from_title:
                hwnd = hwnd_from_title
                full_title = title_from_title
                print(f"Found window by title: '{full_title}'")

        if not hwnd:
            print("Game window not found")
            return None

        # Get window dimensions
        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        width = right - left
        height = bottom - top

        # If dimensions are too small, this may not be the game window
        if width < 300 or height < 200:
            print(f"Window dimensions too small: {width}x{height}")
            return None

        # Get window coordinates on screen
        window_left, window_top, _, _ = win32gui.GetWindowRect(hwnd)

        # Add client area offset relative to window
        left += window_left
        top += window_top

        # Create contexts for capture
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()

        # Create bitmap
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        saveDC.SelectObject(saveBitMap)

        # Copy window data to bitmap
        result = windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

        # Save bitmap to bytes array
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)

        # Create image from data
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )

        # Convert to OpenCV format
        screenshot = np.array(img)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

        # Release resources
        win32gui.DeleteObject(saveBitMap.GetHandle())
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)

        return screenshot
    except Exception as e:
        print(f"Error capturing window: {e}")
        return None


def capture_full_screen():
    """
    Fallback option - capture entire screen
    """
    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        screenshot = np.array(screenshot)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        return screenshot
    except Exception as e:
        print(f"Error capturing screen: {e}")
        return None


def preprocess_image(image):
    """
    Preprocess image to improve OCR
    """
    if image is None:
        return None

    try:
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply binarization (adaptive threshold)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Remove noise with morphological operations
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)

        return opening
    except Exception as e:
        print(f"Error processing image: {e}")
        return image  # Return original image in case of error


def save_debug_images(original, processed, text):
    """
    Save debug images and text
    """
    try:
        os.makedirs(DEBUG_DIR, exist_ok=True)

        cv2.imwrite(os.path.join(DEBUG_DIR, "debug_screenshot.png"), original)
        cv2.imwrite(os.path.join(DEBUG_DIR, "debug_processed.png"), processed)

        with open(os.path.join(DEBUG_DIR, "debug_text.txt"), "w", encoding="utf-8") as f:
            f.write(text)

        return True
    except Exception as e:
        print(f"Error saving debug images: {e}")
        return False


def get_running_processes():
    """
    Returns a list of running processes
    """
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            processes.append((proc.info['pid'], proc.info['name'], proc.info.get('exe', '')))
        return processes
    except Exception as e:
        print(f"Error getting process list: {e}")
        return []


def get_window_titles():
    """
    Get a list of titles of all visible windows
    """

    def callback(hwnd, titles):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            # Check if the window has non-zero dimensions
            if title:
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                if right - left > 50 and bottom - top > 50:  # Minimum size for a real window
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    titles.append((title, pid))
        return True

    titles = []
    win32gui.EnumWindows(callback, titles)
    return titles