
import pytesseract
import re
import os
from config import TESSERACT_PATH, OCR_CONFIG, QUEUE_TEXT_PATTERN, IN_GAME_INDICATORS

# Set Tesseract executable path
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extract_text(image):
    """
    Extract text from processed image
    """
    if image is None:
        return ""

    try:
        # Use pytesseract for text recognition
        text = pytesseract.image_to_string(image, config=OCR_CONFIG)
        return text
    except Exception as e:
        print(f"Error recognizing text: {e}")
        return ""


def analyze_queue_status(text):
    """
    Analyze text to determine queue position
    Returns: (in_queue, position, total)
    where in_queue is a boolean value,
    position is current position (None if not in queue),
    total is total in queue (None if not in queue)
    """
    if not text:
        return False, None, None

    # Check for key phrases in English (always use English for OCR detection)
    queue_keywords = ["Position:", "Leave queue"]
    has_queue_indicator = any(keyword in text for keyword in queue_keywords)

    if has_queue_indicator:
        # Try the pattern
        match = re.search(QUEUE_TEXT_PATTERN, text)
        if match:
            try:
                position = int(match.group(1))
                total = int(match.group(2))
                return True, position, total
            except (ValueError, IndexError) as e:
                print(f"Error analyzing queue text: {e}")

        # If we found queue indicators but couldn't extract numbers, still consider in queue
        return True, None, None

    # Check if there are indicators that the user is already in the game
    for indicator in IN_GAME_INDICATORS:
        if indicator in text and not has_queue_indicator:
            # If there's a game indicator but no queue indicators, user is in game
            return False, None, None

    return False, None, None


def test_regex(pattern, example_text):
    """
    Test regex pattern against example text
    """
    try:
        match = re.search(pattern, example_text)
        if match:
            try:
                position = match.group(1)
                total = match.group(2)
                return True, position, total
            except (IndexError, ValueError):
                pass
        return False, None, None
    except re.error:
        return False, None, None