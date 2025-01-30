import tkinter as tk
import time
import sqlite3
import pygetwindow as gw
from datetime import datetime
import threading

def create_db():
    conn = sqlite3.connect('active_app_time.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS app_time
                 (app_name TEXT, duration INTEGER, timestamp TEXT)''')
    conn.commit()
    conn.close()

def log_active_app(app_name, duration):
    conn = sqlite3.connect('active_app_time.db')
    c = conn.cursor()
    c.execute("INSERT INTO app_time (app_name, duration, timestamp) VALUES (?, ?, ?)",
              (app_name, duration, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def track_active_app():
    global tracking
    current_app = None
    start_time = time.time()
    
    while tracking:
        active_window = gw.getActiveWindow()
        if active_window:
            app_name = active_window.title
            if app_name != current_app:
                if current_app:
                    duration = int(time.time() - start_time)
                    log_active_app(current_app, duration)
                current_app = app_name
                start_time = time.time()
        time.sleep(1)

def start_tracking():
    global tracking
    tracking = True
    tracking_thread = threading.Thread(target=track_active_app, daemon=True)
    tracking_thread.start()
    status_label.config(text="Отслеживание активного приложения начато.", fg="green")

def stop_tracking():
    global tracking
    tracking = False
    status_label.config(text="Отслеживание остановлено.", fg="red")

root = tk.Tk()
root.title("Трекер активных приложений")
root.geometry("400x200")
root.configure(bg="#f0f0f0")

header_label = tk.Label(root, text="Трекер активных приложений", font=("Arial", 16, "bold"), bg="#f0f0f0")
header_label.pack(pady=10)

status_label = tk.Label(root, text="Нажмите 'Начать отслеживание' для начала.", bg="#f0f0f0")
status_label.pack(pady=20)

start_button = tk.Button(root, text="Начать отслеживание", command=start_tracking, width=20, bg="#4CAF50", fg="white")
start_button.pack(pady=5)

stop_button = tk.Button(root, text="Остановить отслеживание", command=stop_tracking, width=20, bg="#f44336", fg="white")
stop_button.pack(pady=5)

create_db()

tracking = False

root.mainloop()
