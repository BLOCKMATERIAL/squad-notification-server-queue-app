import os

# Global settings
CHECK_INTERVAL = 5  # Check interval in seconds
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
OCR_CONFIG = '--psm 6'  # Page segmentation mode: assumes single text block

# Queue detection patterns (always in English regardless of interface language)
QUEUE_TEXT_PATTERN = r"Position:\s*(\d+)\s*/\s*(\d+)"  # Pattern "Position: X / Y"

# In-game indicators (words that may indicate game status)
IN_GAME_INDICATORS = ["Deploy", "Respawn", "Squad", "Main Menu", "Leave queue"]

# Local logo path
assets_dir = os.path.join(os.getcwd(), "assets")
os.makedirs(assets_dir, exist_ok=True)
LOGO_PATH = os.path.join(assets_dir, "logo.png")
GAME_PROCESS_NAME = "SquadGame.exe"
GAME_WINDOW_TITLE = "Squad"

# Creator's GitHub URL
CREATOR_GITHUB_URL = "https://github.com/blockmaterial"  # Replace with your actual GitHub URL

# Debug paths
DEBUG_DIR = os.path.join(os.getcwd(), "debug")
os.makedirs(DEBUG_DIR, exist_ok=True)