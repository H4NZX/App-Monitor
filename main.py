import tkinter as tk
import sqlite3
import pygetwindow as gw
import threading
import time
from datetime import datetime
import csv
import json
import os

CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"min_duration": 5}

def save_config():
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"min_duration": min_duration}, f)

def create_db():
    conn = sqlite3.connect('active_app_time.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS app_time
                 (app_name TEXT, duration INTEGER, timestamp TEXT)''')
    conn.commit()
    conn.close()

def format_duration(duration):
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours}ч {minutes}м {seconds}с"

def log_active_app(app_name, duration):
    if duration >= min_duration:
        try:
            conn = sqlite3.connect('active_app_time.db')
            c = conn.cursor()
            c.execute("INSERT INTO app_time (app_name, duration, timestamp) VALUES (?, ?, ?)",
                      (app_name, duration, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            formatted_duration = format_duration(duration)
            log_listbox.insert(tk.END, f"{app_name}: {formatted_duration}")
        except Exception as e:
            print(f"Ошибка при логировании приложения: {e}")

def export_to_csv():
    try:
        conn = sqlite3.connect('active_app_time.db')
        c = conn.cursor()
        c.execute("SELECT * FROM app_time")
        rows = c.fetchall()
        conn.close()

        with open('app_time_log.csv', 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(['App Name', 'Duration (seconds)', 'Timestamp'])
            csvwriter.writerows(rows)

        status_label.config(text="Данные успешно экспортированы в app_time_log.csv", fg="blue")
    except Exception as e:
        print(f"Ошибка при экспорте данных: {e}")

def track_active_app():
    global current_app, app_start_time
    while tracking:
        try:
            active_window = gw.getActiveWindow()
            if active_window:
                app_name = active_window.title
                if app_name != current_app:
                    if current_app:
                        duration = int(time.time() - app_start_time)
                        log_active_app(current_app, duration)
                    current_app = app_name
                    app_start_time = time.time()
            time.sleep(1)
        except Exception as e:
            print(f"Ошибка при отслеживании активного приложения: {e}")

def start_tracking():
    global tracking
    tracking = True
    status_label.config(text="Отслеживание активного приложения начато.", fg="green")
    threading.Thread(target=track_active_app, daemon=True).start()

def stop_tracking():
    global tracking
    tracking = False
    status_label.config(text="Отслеживание остановлено.", fg="red")

root = tk.Tk()
root.title("Трекер активных приложений")
root.geometry("400x400")
root.configure(bg="#f0f0f0")

header_label = tk.Label(root, text="Трекер активных приложений", font=("Arial", 16, "bold"), bg="#f0f0f0")
header_label.pack(pady=10)

status_label = tk.Label(root, text="Нажмите 'Начать отслеживание' для начала.", bg="#f0f0f0")
status_label.pack(pady=20)

log_listbox = tk.Listbox(root, width=50, height=10)
log_listbox.pack(pady=10)

start_button = tk.Button(root, text="Начать отслеживание", command=start_tracking, width=20, bg="#4CAF50", fg="white")
start_button.pack(pady=5)

stop_button = tk.Button(root, text="Остановить отслеживание", command=stop_tracking, width=20, bg="#f44336", fg="white")
stop_button.pack(pady=5)

export_button = tk.Button(root, text="Экспорт в CSV", command=export_to_csv, width=20, bg="#2196F3", fg="white")
export_button.pack(pady=5)

current_app = None
app_start_time = None
tracking = False
min_duration = load_config().get("min_duration", 5)

create_db()
root.mainloop()
