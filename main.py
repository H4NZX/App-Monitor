import tkinter as tk
import time
import threading
import pygetwindow as gw
from datetime import datetime, timedelta
import sqlite3
import os
import json
from collections import Counter
from tkinter import messagebox
from PIL import Image, ImageTk

CONFIG_FILE = 'config.json'
min_duration = 5

def load_config():
    global min_duration
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            min_duration = config.get("min_duration", 5)

def create_db():
    conn = sqlite3.connect('active_app_time.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS app_time
                 (app_name TEXT, duration INTEGER, timestamp TEXT)''')
    conn.commit()
    conn.close()

def log_active_app(app_name, duration):
    if duration >= min_duration:
        try:
            conn = sqlite3.connect('active_app_time.db')
            c = conn.cursor()
            c.execute("INSERT INTO app_time (app_name, duration, timestamp) VALUES (?, ?, ?)",
                      (app_name, duration, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            conn.commit()
            conn.close()
            log_app_usage(app_name)
        except Exception as e:
            print(f"Ошибка при логировании приложения: {e}")

app_usage_data = []

def log_app_usage(app_name):
    app_usage_data.append((app_name, datetime.now()))

def get_top_apps(period='week'):
    now = datetime.now()
    if period == 'week':
        start_time = now - timedelta(days=7)
    elif period == 'month':
        start_time = now - timedelta(days=30)
    else:
        raise ValueError("Период должен быть 'week' или 'month'.")

    filtered_data = [app for app in app_usage_data if app[1] >= start_time]
    app_counts = Counter(app[0] for app in filtered_data)
    top_apps = app_counts.most_common(5)
    
    return top_apps

class AppTracker:
    def __init__(self, master):
        self.master = master
        self.is_tracking = False
        self.current_app = None
        self.app_start_time = None
        self.min_duration = min_duration

        self.frame = tk.Frame(master, bg="#2E2E2E")
        self.frame.pack(padx=10, pady=10)

        self.start_img = ImageTk.PhotoImage(Image.open('start.png').resize((64, 64), Image.LANCZOS))
        self.stop_img = ImageTk.PhotoImage(Image.open('stop.png').resize((64, 64), Image.LANCZOS))
        self.export_img = ImageTk.PhotoImage(Image.open('export.png').resize((64, 64), Image.LANCZOS))

        self.start_button = tk.Button(self.frame, image=self.start_img, command=self.start_tracking, bg="gray", fg="white")
        self.start_button.grid(row=0, column=0, padx=5, pady=5)

        self.stop_button = tk.Button(self.frame, image=self.stop_img, command=self.stop_tracking, bg="gray", fg="white")
        self.stop_button.grid(row=0, column=1, padx=5, pady=5)

        self.export_button = tk.Button(self.frame, image=self.export_img, command=self.export_data, bg="gray", fg="white")
        self.export_button.grid(row=0, column=2, padx=5, pady=5)

        self.status_label = tk.Label(self.frame, text="Статус: Не отслеживается", font=("Arial", 10), bg="#2E2E2E", fg="white")
        self.status_label.grid(row=1, columnspan=3, pady=5)

        self.top_apps_label = tk.Label(self.frame, text="Топ-5 приложений за неделю:", font=("Arial", 10), bg="#2E2E2E", fg="white")
        self.top_apps_label.grid(row=2, columnspan=3, pady=5)

        self.top_apps_listbox = tk.Listbox(self.frame, width=40, height=5, bg="#3E3E3E", fg="white")
        self.top_apps_listbox.grid(row=3, columnspan=3, pady=5)

        self.top_month_apps_label = tk.Label(self.frame, text="Топ-5 приложений за месяц:", font=("Arial", 10), bg="#2E2E2E", fg="white")
        self.top_month_apps_label.grid(row=4, columnspan=3, pady=5)

        self.top_month_apps_listbox = tk.Listbox(self.frame, width=40, height=5, bg="#3E3E3E", fg="white")
        self.top_month_apps_listbox.grid(row=5, columnspan=3, pady=5)

        create_db()

    def start_tracking(self):
        self.is_tracking = True
        self.status_label.config(text="Статус: Отслеживание начато.")
        threading.Thread(target=self.track_apps, daemon=True).start()

    def stop_tracking(self):
        self.is_tracking = False
        self.status_label.config(text="Статус: Не отслеживается.")
        self.update_top_apps()

    def track_apps(self):
        while self.is_tracking:
            try:
                active_window = gw.getActiveWindow()
                if active_window:
                    app_name = active_window.title
                    if app_name != self.current_app:
                        if self.current_app:
                            duration = int(time.time() - self.app_start_time)
                            log_active_app(self.current_app, duration)
                        self.current_app = app_name
                        self.app_start_time = time.time()
                time.sleep(1)
            except Exception as e:
                print(f"Ошибка при отслеживании активного приложения: {e}")

    def update_top_apps(self):
        self.top_apps_listbox.delete(0, tk.END)
        self.top_month_apps_listbox.delete(0, tk.END)

        top_weekly_apps = get_top_apps('week')
        for app, count in top_weekly_apps:
            self.top_apps_listbox.insert(tk.END, f"{app}: {count} раз")

        top_monthly_apps = get_top_apps('month')
        for app, count in top_monthly_apps:
            self.top_month_apps_listbox.insert(tk.END, f"{app}: {count} раз")

    def export_data(self):
        try:
            with open('app_usage_report.txt', 'w') as f:
                f.write("Отчет о времени использования приложений\n")
                f.write("====================================\n")
                for app, timestamp in app_usage_data:
                    f.write(f"{app} использовалось в {timestamp}\n")
            messagebox.showinfo("Экспорт данных", "Данные успешно экспортированы в app_usage_report.txt!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось экспортировать данные: {e}")

if __name__ == "__main__":
    load_config()
    root = tk.Tk()
    root.title("Трекер приложений")
    root.configure(bg="#2E2E2E")  # Установка цвета фона для окна
    app_tracker = AppTracker(root)
    root.mainloop()
