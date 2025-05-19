# ui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import os
import pyautogui
import urllib.request
from PIL import Image, ImageTk
import io
import re
import time
import webbrowser
import cv2

from config import (
    CHECK_INTERVAL, QUEUE_TEXT_PATTERN, IN_GAME_INDICATORS,
    LOGO_PATH, CREATOR_GITHUB_URL, GAME_PROCESS_NAME, GAME_WINDOW_TITLE
)
from language import get_text, i18n
from screen_capture import capture_window, capture_full_screen, preprocess_image, save_debug_images
from ocr_processor import extract_text, analyze_queue_status, test_regex
from notification import send_notification  # Добавьте этот импорт


class SquadQueueMonitorUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Squad Queue Monitor")
        self.root.geometry("550x600")
        self.root.resizable(True, True)

        # Global variables for monitoring state
        self.running = False
        self.monitor_thread = None
        self.last_position = None
        self.last_total = None
        self.in_game_detected = False

        # Initialize UI elements
        self.setup_tabs()
        self.setup_monitor_tab()
        self.setup_settings_tab()
        self.setup_debug_tab()
        self.setup_about_tab()

        # Start screen resolution update
        self.update_screen_resolution_info()

        # Add startup message to logs
        self.log(get_text("program_started"))

    def load_local_logo(self):
        """
        Load logo from assets folder
        """
        try:
            # Check if logo exists
            if os.path.exists(LOGO_PATH):
                img = Image.open(LOGO_PATH)
                # Resize image for display
                img = img.resize((300, 150), Image.LANCZOS)
                photo_img = ImageTk.PhotoImage(img)
                return photo_img
            else:
                print(f"Logo file not found at {LOGO_PATH}")
                # Create a placeholder logo with text
                return self.create_placeholder_logo()
        except Exception as e:
            print(f"Error loading logo: {e}")
            return self.create_placeholder_logo()

    def create_placeholder_logo(self):
        """
        Create a placeholder logo when the actual logo is not available
        """
        try:
            # Create a simple placeholder image
            img = Image.new('RGB', (300, 150), color="#007acc")
            # Add text
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()

            draw.text((60, 55), "Squad Monitor", fill="white", font=font)
            photo_img = ImageTk.PhotoImage(img)
            return photo_img
        except Exception as e:
            print(f"Error creating placeholder logo: {e}")
            return None

    def open_github(self, event):
        """
        Open creator's GitHub page when the link is clicked
        """
        webbrowser.open(CREATOR_GITHUB_URL)

    def change_language(self):
        """
        Change the interface language
        """
        lang_code = self.language_var.get()
        i18n.set_language(lang_code)

        # Update UI elements with new language
        self.update_ui_texts()

    def setup_tabs(self):
        """
        Set up the main tab control
        """
        self.tab_control = ttk.Notebook(self.root)
        self.monitor_tab = ttk.Frame(self.tab_control)
        self.settings_tab = ttk.Frame(self.tab_control)
        self.debug_tab = ttk.Frame(self.tab_control)
        self.about_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.monitor_tab, text=get_text("monitor_tab"))
        self.tab_control.add(self.settings_tab, text=get_text("settings_tab"))
        self.tab_control.add(self.debug_tab, text=get_text("debug_tab"))
        self.tab_control.add(self.about_tab, text=get_text("about_tab"))
        self.tab_control.pack(expand=1, fill="both")

    def setup_monitor_tab(self):
        """
        Set up the monitoring tab with status and controls
        """
        # Status variable
        self.status_var = tk.StringVar()
        self.status_var.set(get_text("not_running"))

        # Logo frame
        logo_frame = ttk.Frame(self.monitor_tab)
        logo_frame.pack(padx=10, pady=10, fill="x")

        # Load and display logo
        try:
            logo_image = self.load_local_logo()
            if logo_image:
                logo_label = tk.Label(logo_frame, image=logo_image)
                logo_label.image = logo_image  # Keep reference to image
                logo_label.pack(anchor="center")
        except Exception as e:
            print(f"Error displaying logo: {e}")

        # Language selector with styling
        language_frame = ttk.Frame(self.monitor_tab)
        language_frame.pack(padx=10, pady=5, fill="x")

        language_label = ttk.Label(language_frame, text=get_text("language_label"))
        language_label.pack(side=tk.LEFT, padx=5)

        # Language variables
        self.language_var = tk.StringVar(value="en")

        # Radio buttons for language selection
        language_en = ttk.Radiobutton(
            language_frame,
            text=get_text("language_en"),
            variable=self.language_var,
            value="en",
            command=self.change_language
        )
        language_en.pack(side=tk.LEFT, padx=5)

        language_uk = ttk.Radiobutton(
            language_frame,
            text=get_text("language_uk"),
            variable=self.language_var,
            value="uk",
            command=self.change_language
        )
        language_uk.pack(side=tk.LEFT, padx=5)

        # Window status frame - добавляем новый фрейм для отображения статуса окна
        window_status_frame = ttk.Frame(self.monitor_tab)
        window_status_frame.pack(padx=10, pady=5, fill="x")

        # Статус окна
        self.window_status_var = tk.StringVar()
        self.window_status_var.set(get_text("checking_window"))

        window_status_label = ttk.Label(
            window_status_frame,
            text=get_text("window_status_label")
        )
        window_status_label.pack(side=tk.LEFT, padx=5)

        # Индикатор статуса окна с цветной меткой
        self.window_status_indicator = ttk.Label(
            window_status_frame,
            textvariable=self.window_status_var,
            foreground="gray"
        )
        self.window_status_indicator.pack(side=tk.LEFT, padx=5)

        # Кнопка проверки окна
        check_window_button = ttk.Button(
            window_status_frame,
            text=get_text("check_window_button"),
            command=self.check_game_window
        )
        check_window_button.pack(side=tk.RIGHT, padx=5)

        # Status frame with styled border
        self.status_frame = ttk.LabelFrame(self.monitor_tab, text=get_text("status_frame"))
        self.status_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Status with larger font
        status_label = ttk.Label(self.status_frame, textvariable=self.status_var, font=("Arial", 14))
        status_label.pack(padx=10, pady=20)

        # Resolution info
        self.resolution_var = tk.StringVar()
        resolution_label = ttk.Label(self.status_frame, textvariable=self.resolution_var, font=("Arial", 10))
        resolution_label.pack(padx=10, pady=5)

        # Control buttons
        button_frame = ttk.Frame(self.monitor_tab)
        button_frame.pack(padx=10, pady=10, fill="x")

        self.start_button = ttk.Button(
            button_frame,
            text=get_text("start_button"),
            command=self.start_monitoring
        )
        self.start_button.pack(side=tk.LEFT, padx=5, expand=True, fill="x")

        self.stop_button = ttk.Button(
            button_frame,
            text=get_text("stop_button"),
            command=self.stop_monitoring,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.RIGHT, padx=5, expand=True, fill="x")

        # Запустим проверку окна игры при запуске
        self.root.after(1000, self.check_game_window)

    def check_game_window(self):
        """
        Проверяет, запущен ли процесс игры, и обновляет индикатор
        """
        from screen_capture import is_game_running, find_game_window

        # Проверяем, запущен ли процесс игры
        is_running, process_name, pid = is_game_running()

        if is_running:
            # Игра запущена, пытаемся найти окно
            game_hwnd, game_title = find_game_window()

            if game_hwnd:
                # Окно игры найдено
                self.window_status_var.set(get_text("process_and_window_found", process_name, game_title))
                self.window_status_indicator.config(foreground="green")
                self.log(get_text("game_process_and_window_found_log", process_name, pid, game_title))
            else:
                # Процесс запущен, но окно не найдено (возможно, игра загружается)
                self.window_status_var.set(get_text("process_found_no_window", process_name))
                self.window_status_indicator.config(foreground="orange")
                self.log(get_text("game_process_found_no_window_log", process_name, pid))
        else:
            # Игра не запущена
            self.window_status_var.set(get_text("process_not_found", GAME_PROCESS_NAME))
            self.window_status_indicator.config(foreground="red")
            self.log(get_text("game_process_not_found_log", GAME_PROCESS_NAME))

        # Запланируем следующую проверку через 5 секунд
        self.root.after(5000, self.check_game_window)

    def setup_settings_tab(self):
        """
        Set up the settings tab
        """
        # Settings frame
        self.settings_frame = ttk.LabelFrame(
            self.settings_tab,
            text=get_text("settings_frame")
        )
        self.settings_frame.pack(padx=10, pady=10, fill="both")

        # Interval setting
        self.interval_label = ttk.Label(
            self.settings_frame,
            text=get_text("interval_label")
        )
        self.interval_label.grid(column=0, row=0, padx=5, pady=5, sticky=tk.W)

        self.interval_entry = ttk.Entry(self.settings_frame)
        self.interval_entry.grid(column=1, row=0, padx=5, pady=5)
        self.interval_entry.insert(0, str(CHECK_INTERVAL))

        # Game process name setting
        process_name_label = ttk.Label(
            self.settings_frame,
            text=get_text("process_name_label")
        )
        process_name_label.grid(column=0, row=1, padx=5, pady=5, sticky=tk.W)

        self.process_name_entry = ttk.Entry(self.settings_frame, width=30)
        self.process_name_entry.grid(column=1, row=1, padx=5, pady=5)
        self.process_name_entry.insert(0, GAME_PROCESS_NAME)

        # Button to show process list
        process_list_button = ttk.Button(
            self.settings_frame,
            text=get_text("process_list_button"),
            command=self.show_process_list
        )
        process_list_button.grid(column=2, row=1, padx=5, pady=5)

        # Game window title setting (fallback)
        window_title_label = ttk.Label(
            self.settings_frame,
            text=get_text("window_title_label")
        )
        window_title_label.grid(column=0, row=2, padx=5, pady=5, sticky=tk.W)

        self.window_title_entry = ttk.Entry(self.settings_frame, width=30)
        self.window_title_entry.grid(column=1, row=2, padx=5, pady=5)
        self.window_title_entry.insert(0, GAME_WINDOW_TITLE)

        # Button to show window list (fallback)
        window_list_button = ttk.Button(
            self.settings_frame,
            text=get_text("window_list_button"),
            command=self.show_window_list
        )
        window_list_button.grid(column=2, row=2, padx=5, pady=5)

        # Queue pattern setting
        self.pattern_label = ttk.Label(
            self.settings_frame,
            text=get_text("pattern_label")
        )
        self.pattern_label.grid(column=0, row=3, padx=5, pady=5, sticky=tk.W)

        self.queue_pattern_entry = ttk.Entry(self.settings_frame, width=30)
        self.queue_pattern_entry.grid(column=1, row=3, padx=5, pady=5)
        self.queue_pattern_entry.insert(0, QUEUE_TEXT_PATTERN)

        # Example text
        self.example_label = ttk.Label(
            self.settings_frame,
            text=get_text("example_label")
        )
        self.example_label.grid(column=0, row=4, padx=5, pady=5, sticky=tk.W)

        self.example_text = ttk.Label(
            self.settings_frame,
            text="Position: 1 / 1",
            font=("Arial", 10, "italic")
        )
        self.example_text.grid(column=1, row=4, padx=5, pady=5, sticky=tk.W)

        # In-game indicators
        self.indicators_label = ttk.Label(
            self.settings_frame,
            text=get_text("indicators_label")
        )
        self.indicators_label.grid(column=0, row=5, padx=5, pady=5, sticky=tk.W)

        self.ingame_indicators_entry = tk.Text(self.settings_frame, height=3, width=30)
        self.ingame_indicators_entry.grid(column=1, row=5, padx=5, pady=5)
        self.ingame_indicators_entry.insert("1.0", ", ".join(IN_GAME_INDICATORS))

        # Buttons
        settings_buttons_frame = ttk.Frame(self.settings_tab)
        settings_buttons_frame.pack(padx=10, pady=10, fill="x")

        self.save_button = ttk.Button(
            settings_buttons_frame,
            text=get_text("save_button"),
            command=self.save_settings
        )
        self.save_button.pack(side=tk.LEFT, padx=5, expand=True, fill="x")

        self.test_button = ttk.Button(
            settings_buttons_frame,
            text=get_text("test_button"),
            command=self.test_capture
        )
        self.test_button.pack(side=tk.RIGHT, padx=5, expand=True, fill="x")

    def show_process_list(self):
        """
        Показывает список запущенных процессов для выбора игрового процесса
        """
        from screen_capture import get_running_processes

        processes = get_running_processes()

        # Создаем диалоговое окно
        process_list_window = tk.Toplevel(self.root)
        process_list_window.title("Running Processes")
        process_list_window.geometry("600x500")

        # Добавляем инструкцию
        instruction = ttk.Label(
            process_list_window,
            text="Double-click a process to set it as the game process:",
            font=("Arial", 10, "bold")
        )
        instruction.pack(pady=10)

        # Создаем поле поиска
        search_frame = ttk.Frame(process_list_window)
        search_frame.pack(fill="x", padx=10, pady=5)

        search_label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=5)

        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5, fill="x", expand=True)

        # Создаем список с прокруткой
        list_frame = ttk.Frame(process_list_window)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("PID", "Name", "Path")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        # Определяем заголовки
        tree.heading("PID", text="PID")
        tree.heading("Name", text="Process Name")
        tree.heading("Path", text="Executable Path")

        # Устанавливаем ширину столбцов
        tree.column("PID", width=80)
        tree.column("Name", width=150)
        tree.column("Path", width=350)

        # Добавляем полосу прокрутки
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        vsb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        # Вставляем данные
        for pid, name, exe in processes:
            tree.insert("", "end", values=(pid, name, exe))

        # Функция поиска
        def filter_processes(*args):
            search_text = search_var.get().lower()
            tree.delete(*tree.get_children())
            for pid, name, exe in processes:
                if (search_text in str(pid).lower() or
                        search_text in name.lower() or
                        search_text in exe.lower()):
                    tree.insert("", "end", values=(pid, name, exe))

        # Привязываем изменение текста к поиску
        search_var.trace("w", filter_processes)

        # Обработчик двойного клика
        def on_double_click(event):
            selected_item = tree.selection()[0]
            values = tree.item(selected_item, "values")
            process_name = values[1]  # Имя процесса

            # Обновляем настройку игрового процесса
            global GAME_PROCESS_NAME
            GAME_PROCESS_NAME = process_name

            # Обновляем поле ввода в настройках
            self.process_name_entry.delete(0, tk.END)
            self.process_name_entry.insert(0, process_name)

            messagebox.showinfo("Process Selected", f"Selected game process: {process_name}")
            process_list_window.destroy()

            # Перезапускаем проверку
            self.check_game_window()

        tree.bind("<Double-1>", on_double_click)

        # Кнопка закрыть
        close_button = ttk.Button(
            process_list_window,
            text="Close",
            command=process_list_window.destroy
        )
        close_button.pack(pady=10)

    def show_window_list(self):
        """
        Показывает список всех окон для удобства выбора
        """
        from screen_capture import get_window_titles

        window_titles = get_window_titles()

        # Создаем диалоговое окно
        window_list = tk.Toplevel(self.root)
        window_list.title("Available Windows")
        window_list.geometry("500x400")

        # Добавляем инструкцию
        instruction = ttk.Label(
            window_list,
            text="Double-click a window title to use it:",
            font=("Arial", 10, "bold")
        )
        instruction.pack(pady=10)

        # Создаем список с прокруткой
        frame = ttk.Frame(window_list)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        listbox = tk.Listbox(
            frame,
            yscrollcommand=scrollbar.set,
            font=("Consolas", 10),
            height=15,
            width=50
        )
        listbox.pack(fill="both", expand=True)

        scrollbar.config(command=listbox.yview)

        # Добавляем заголовки окон в список
        for title, pid in window_titles:
            if title.strip():  # Пропускаем пустые заголовки
                listbox.insert(tk.END, f"{title} (PID: {pid})")

        # Обработчик двойного клика
        def on_double_click(event):
            selection = listbox.curselection()
            if selection:
                full_title = listbox.get(selection[0])
                # Извлекаем только заголовок окна (без PID)
                title = full_title.split(" (PID:")[0]
                self.window_title_entry.delete(0, tk.END)
                self.window_title_entry.insert(0, title)
                window_list.destroy()

        listbox.bind("<Double-1>", on_double_click)

        # Кнопка закрыть
        close_button = ttk.Button(
            window_list,
            text="Close",
            command=window_list.destroy
        )
        close_button.pack(pady=10)

    def setup_debug_tab(self):
        """
        Set up the debug tab
        """
        # Debug frame
        self.debug_frame = ttk.LabelFrame(
            self.debug_tab,
            text=get_text("debug_frame")
        )
        self.debug_frame.pack(padx=10, pady=10, fill="both")

        # Save screenshots checkbox
        self.save_screenshot_var = tk.BooleanVar()
        self.save_screenshot_check = ttk.Checkbutton(
            self.debug_frame,
            text=get_text("save_screenshots"),
            variable=self.save_screenshot_var,
            command=self.toggle_save_screenshots
        )
        self.save_screenshot_check.pack(padx=10, pady=5, anchor="w")

        # Debug buttons
        button_frame = ttk.Frame(self.debug_frame)
        button_frame.pack(padx=10, pady=5, fill="x")

        self.test_ocr_button = ttk.Button(
            button_frame,
            text=get_text("test_ocr"),
            command=self.test_capture
        )
        self.test_ocr_button.pack(side=tk.LEFT, padx=5, pady=5, expand=True, fill="x")

        self.test_regex_button = ttk.Button(
            button_frame,
            text=get_text("test_regex"),
            command=self.test_regex
        )
        self.test_regex_button.pack(side=tk.RIGHT, padx=5, pady=5, expand=True, fill="x")

        # Log frame
        self.log_frame = ttk.LabelFrame(
            self.debug_tab,
            text=get_text("logs_frame")
        )
        self.log_frame.pack(padx=10, pady=10, fill="both", expand=True)

        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            wrap=tk.WORD,
            width=50,
            height=12
        )
        self.log_text.pack(padx=10, pady=10, fill="both", expand=True)

    def setup_about_tab(self):
        """
        Set up the about tab
        """
        about_frame = ttk.Frame(self.about_tab)
        about_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Add logo to about tab
        try:
            about_logo_image = self.load_local_logo()
            if about_logo_image:
                about_logo_label = tk.Label(about_frame, image=about_logo_image)
                about_logo_label.image = about_logo_image  # Keep reference to image
                about_logo_label.pack(anchor="center", pady=15)
        except Exception as e:
            print(f"Error displaying logo on about tab: {e}")

        # Author information with GitHub link
        author_frame = ttk.Frame(about_frame)
        author_frame.pack(pady=10, fill="x")

        author_label = ttk.Label(
            author_frame,
            text=get_text("created_by"),
            font=("Arial", 10)
        )
        author_label.pack(side=tk.LEFT, padx=(20, 5))

        # GitHub link as clickable label - with blue color and underline
        github_link = ttk.Label(
            author_frame,
            text=get_text("github_link"),
            foreground="blue",
            cursor="hand2",
            font=("Arial", 10, "underline")
        )
        github_link.pack(side=tk.LEFT, padx=5)
        github_link.bind("<Button-1>", self.open_github)

        # About text
        self.about_label = scrolledtext.ScrolledText(about_frame, wrap=tk.WORD, height=15)
        self.about_label.pack(fill="both", expand=True, padx=10, pady=10)
        self.about_label.insert(tk.END, get_text("about_text"))
        self.about_label.config(state=tk.DISABLED)  # Make text read-only

        # Copyright label
        self.copyright_label = ttk.Label(
            about_frame,
            text=get_text("copyright"),
            font=("Arial", 8)
        )
        self.copyright_label.pack(side=tk.BOTTOM, pady=10)

    def update_ui_texts(self):
        """
        Update all UI texts based on the selected language
        """
        # Update tab labels
        self.tab_control.tab(0, text=get_text("monitor_tab"))
        self.tab_control.tab(1, text=get_text("settings_tab"))
        self.tab_control.tab(2, text=get_text("debug_tab"))
        self.tab_control.tab(3, text=get_text("about_tab"))

        # Update monitor tab
        self.status_frame.config(text=get_text("status_frame"))

        # Update window status
        from screen_capture import is_game_running, find_game_window
        is_running, process_name, pid = is_game_running()

        if is_running:
            game_hwnd, game_title = find_game_window()
            if game_hwnd:
                self.window_status_var.set(get_text("process_and_window_found", process_name, game_title))
                self.window_status_indicator.config(foreground="green")
            else:
                self.window_status_var.set(get_text("process_found_no_window", process_name))
                self.window_status_indicator.config(foreground="orange")
        else:
            self.window_status_var.set(get_text("process_not_found", GAME_PROCESS_NAME))
            self.window_status_indicator.config(foreground="red")

        # Update status text based on current state
        if self.running:
            self.status_var.set(get_text("running"))
        else:
            self.status_var.set(get_text("not_running"))

        # Update screen resolution
        screen_width, screen_height = pyautogui.size()
        self.resolution_var.set(get_text("resolution", screen_width, screen_height))

        # Update buttons
        self.start_button.config(text=get_text("start_button"))
        self.stop_button.config(text=get_text("stop_button"))

        # Update settings tab
        self.settings_frame.config(text=get_text("settings_frame"))
        self.interval_label.config(text=get_text("interval_label"))
        self.pattern_label.config(text=get_text("pattern_label"))
        self.example_label.config(text=get_text("example_label"))
        self.indicators_label.config(text=get_text("indicators_label"))
        self.save_button.config(text=get_text("save_button"))
        self.test_button.config(text=get_text("test_button"))

        # Update debug tab
        self.debug_frame.config(text=get_text("debug_frame"))
        self.save_screenshot_check.config(text=get_text("save_screenshots"))
        self.test_ocr_button.config(text=get_text("test_ocr"))
        self.test_regex_button.config(text=get_text("test_regex"))
        self.log_frame.config(text=get_text("logs_frame"))

        # Update about tab
        self.about_label.config(state=tk.NORMAL)
        self.about_label.delete("1.0", tk.END)
        self.about_label.insert(tk.END, get_text("about_text"))
        self.about_label.config(state=tk.DISABLED)
        self.copyright_label.config(text=get_text("copyright"))

    def start_monitoring(self):
        """
        Start monitoring in a separate thread
        """
        if self.running:
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_queue)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        self.status_var.set(get_text("running"))
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)

    def stop_monitoring(self):
        """
        Stop monitoring
        """
        self.running = False
        self.status_var.set(get_text("stopped"))
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def monitor_queue(self):
        """
        Main queue monitoring function - scans the game window or full screen
        """
        was_in_queue = False

        while self.running:
            try:
                # Check if game is running
                from screen_capture import is_game_running, find_game_window, capture_window, capture_full_screen

                is_running, process_name, pid = is_game_running()

                if is_running:
                    # Game is running, try to capture window
                    game_hwnd, game_title = find_game_window()

                    if game_hwnd:
                        # Game window found, update status if changed
                        if self.window_status_var.get() != get_text("process_and_window_found", process_name,
                                                                    game_title):
                            self.window_status_var.set(get_text("process_and_window_found", process_name, game_title))
                            self.window_status_indicator.config(foreground="green")
                            self.log(get_text("game_process_and_window_found_log", process_name, pid, game_title))

                        # Capture game window
                        screenshot = capture_window()
                    else:
                        # Game process running but window not found
                        if self.window_status_var.get() != get_text("process_found_no_window", process_name):
                            self.window_status_var.set(get_text("process_found_no_window", process_name))
                            self.window_status_indicator.config(foreground="orange")
                            self.log(get_text("game_process_found_no_window_log", process_name, pid))

                        # Fallback to full screen
                        screenshot = capture_full_screen()
                else:
                    # Game not running
                    if self.window_status_var.get() != get_text("process_not_found", GAME_PROCESS_NAME):
                        self.window_status_var.set(get_text("process_not_found", GAME_PROCESS_NAME))
                        self.window_status_indicator.config(foreground="red")
                        self.log(get_text("game_process_not_found_log", GAME_PROCESS_NAME))

                    # Fallback to full screen
                    screenshot = capture_full_screen()

                # Skip if screenshot capture failed
                if screenshot is None:
                    time.sleep(CHECK_INTERVAL)
                    continue

                # Preprocess image
                processed = preprocess_image(screenshot)

                # Extract text
                text = extract_text(processed)

                # Debug: save screenshots and text if enabled
                if self.save_screenshot_var.get():
                    save_debug_images(screenshot, processed, text)

                # Analyze queue status
                in_queue, position, total = analyze_queue_status(text)

                # Update state variables
                self.last_position = position
                self.last_total = total

                # Logic for detecting game entry
                if was_in_queue and not in_queue:
                    # If we were in queue but now we're not - possibly entered the game
                    self.in_game_detected = True
                    send_notification()
                    self.status_var.set(get_text("entered_server"))
                    self.log(get_text("entered_server"))

                was_in_queue = in_queue

                # Update status in interface
                if in_queue:
                    if position is not None and total is not None:
                        self.status_var.set(get_text("in_queue", position, total))
                        self.log(get_text("in_queue", position, total))
                    else:
                        self.status_var.set(get_text("queue_pos_unknown"))
                        self.log(get_text("queue_pos_unknown"))
                elif self.status_var.get() != get_text("entered_server") and not self.save_screenshot_var.get():
                    self.status_var.set(get_text("running"))

            except Exception as e:
                self.log(f"Error in main loop: {e}")
                self.status_var.set(f"Error: {str(e)}")

            # Pause before next check
            time.sleep(CHECK_INTERVAL)

    def save_settings(self):
        """
        Save settings from the UI
        """
        try:
            # Declare globals before using them
            global CHECK_INTERVAL, GAME_PROCESS_NAME, GAME_WINDOW_TITLE, QUEUE_TEXT_PATTERN, IN_GAME_INDICATORS

            # Update check interval
            CHECK_INTERVAL = int(self.interval_entry.get())

            # Update game process name
            GAME_PROCESS_NAME = self.process_name_entry.get().strip()

            # Update game window title (fallback)
            GAME_WINDOW_TITLE = self.window_title_entry.get().strip()

            # Update queue pattern
            QUEUE_TEXT_PATTERN = self.queue_pattern_entry.get()

            # Update in-game indicators
            indicators_text = self.ingame_indicators_entry.get("1.0", tk.END).strip()
            IN_GAME_INDICATORS = [ind.strip() for ind in indicators_text.split(",") if ind.strip()]

            # Test pattern with example
            example_text = "Position: 1 / 1"  # Fixed English example for queue detection
            success, pos, total = test_regex(QUEUE_TEXT_PATTERN, example_text)

            if success:
                messagebox.showinfo("Settings", get_text("settings_saved", pos, total))
            else:
                messagebox.showwarning("Warning", get_text("settings_warning"))

        except ValueError:
            messagebox.showerror("Error", get_text("settings_error"))
        except re.error as e:
            messagebox.showerror("Regular Expression Error", get_text("regex_error", str(e)))

    def test_capture(self):
        """
        Test screen capture and text recognition
        """
        # Try to capture game window first
        from screen_capture import is_game_running, find_game_window, capture_window, capture_full_screen

        is_running, process_name, pid = is_game_running()

        if is_running:
            game_hwnd, game_title = find_game_window()
            if game_hwnd:
                self.log(f"Capturing game window: {game_title}")
                screenshot = capture_window()
            else:
                self.log("Game process running but window not found, using full screen")
                screenshot = capture_full_screen()
        else:
            self.log(f"Game process {GAME_PROCESS_NAME} not running, using full screen")
            screenshot = capture_full_screen()

        if screenshot is None:
            messagebox.showerror("Error", get_text("capture_error"))
            return

        # Process and analyze
        processed = preprocess_image(screenshot)
        text = extract_text(processed)

        # Save files for inspection
        cv2.imwrite("test_capture.png", screenshot)
        cv2.imwrite("test_processed.png", processed)
        with open("test_text.txt", "w", encoding="utf-8") as f:
            f.write(text)

        # Analyze queue status
        in_queue, position, total = analyze_queue_status(text)
        result = get_text("test_result")

        if in_queue:
            if position is not None and total is not None:
                result += get_text("queue_detected", position, total)
            else:
                result += get_text("queue_detected_unknown")
        else:
            result += get_text("queue_not_detected")

        # Show result and open files
        messagebox.showinfo("Test Result", result)
        for file in ["test_capture.png", "test_processed.png", "test_text.txt"]:
            if os.path.exists(file):
                try:
                    os.startfile(file)
                except:
                    # Fallback to webbrowser for non-Windows systems
                    webbrowser.open(os.path.abspath(file))

    def test_regex(self):
        """
        Test the regular expression for queue detection
        """
        pattern = self.queue_pattern_entry.get()
        example = "Position: 1 / 1"  # Fixed English example

        success, pos, total = test_regex(pattern, example)
        if success:
            self.log(get_text("test_regex_result", pos, total))
            messagebox.showinfo("Regex Test", get_text("test_regex_result", pos, total))
        else:
            self.log(get_text("regex_test_failed", example))
            messagebox.showerror("Regex Test", get_text("regex_test_failed", example))

    def toggle_save_screenshots(self):
        """
        Enable/disable saving screenshots for debugging
        """
        if self.save_screenshot_var.get():
            messagebox.showinfo("Debug", get_text("debug_enabled"))
        else:
            messagebox.showinfo("Debug", get_text("debug_disabled"))

    def update_screen_resolution_info(self):
        """
        Update screen resolution information
        """
        screen_width, screen_height = pyautogui.size()
        self.resolution_var.set(get_text("resolution", screen_width, screen_height))

        # Update every 5 seconds
        self.root.after(5000, self.update_screen_resolution_info)

    def log(self, message):
        """
        Add message to the log
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"

        self.log_text.insert(tk.END, log_message + "\n")
        self.log_text.see(tk.END)  # Scroll to end

        # Also print to console
        print(log_message)