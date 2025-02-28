import csv
import time
import win32gui
import win32process
import win32api
import win32con
from tkinter import *
from datetime import datetime, timedelta
from collections import defaultdict

class AppMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("AppMonitor")
        self.root.configure(bg='#333333')
        
        # Настройка окна
        window_width = 200
        window_height = 80
        self.root.geometry(f"{window_width}x{window_height}+20+20")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        self.current_app = None
        self.start_time = None
        self.session_data = []
        self.total_times = defaultdict(int)  # Хранилище общего времени
        
        self.load_history()
        
        # Стили
        bg_color = '#333333'
        text_color = '#FFFFFF'
        
        # Элементы интерфейса
        main_frame = Frame(root, bg=bg_color)
        main_frame.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        self.current_app_label = Label(main_frame, 
                                     text="", 
                                     font=('Arial', 8),
                                     fg=text_color,
                                     bg=bg_color,
                                     anchor='w')
        self.current_app_label.pack(fill=X)
        
        self.time_label = Label(main_frame, 
                              text="00:00:00", 
                              font=('Arial', 16, 'bold'),
                              fg='#00FF00',
                              bg=bg_color)
        self.time_label.pack(fill=X)
        
        close_btn = Button(main_frame, 
                         text="×", 
                         font=('Arial', 10),
                         command=self.on_close,
                         bg='#444444',
                         fg=text_color,
                         borderwidth=0,
                         activebackground='#666666')
        close_btn.place(x=window_width-25, y=2, width=20, height=20)
        
        self.update_app_info()
        self.update_display()

    def get_active_app(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
            exe_path = win32process.GetModuleFileNameEx(handle, 0)
            return exe_path.split('\\')[-1]
        except:
            return "Unknown"

    def save_session(self, app_name, start_time, duration):
        # Сохраняем сессию и обновляем общее время
        self.total_times[app_name] += duration
        date = start_time.strftime("%Y-%m-%d")
        time_start = start_time.strftime("%H:%M:%S")
        
        with open('app_history.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([app_name, date, time_start, duration])
        
        self.update_top_apps()

    def load_history(self):
        # Загружаем историю и считаем общее время
        try:
            with open('app_history.csv', 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4:
                        app = row[0]
                        duration = int(row[3])
                        self.total_times[app] += duration
        except FileNotFoundError:
            pass

    def get_current_total(self):
        # Возвращает общее время для текущего приложения + текущую сессию
        if self.current_app and self.start_time:
            return self.total_times.get(self.current_app, 0) + (time.time() - self.start_time)
        return 0

    def update_top_apps(self):
        # Обновляем топ с учётом текущей сессии
        temp_times = self.total_times.copy()
        if self.current_app and self.start_time:
            temp_times[self.current_app] += (time.time() - self.start_time)
        
        sorted_apps = sorted(temp_times.items(), key=lambda x: x[1], reverse=True)[:5]
        
        with open('top_apps.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Rank", "Application", "Total Seconds", "Human Readable Time"])
            for rank, (app, seconds) in enumerate(sorted_apps, 1):
                time_str = str(timedelta(seconds=seconds)).split('.')[0]
                writer.writerow([rank, app, seconds, time_str])

    def update_app_info(self):
        new_app = self.get_active_app()
        
        if new_app != self.current_app:
            if self.current_app is not None:
                # Сохраняем предыдущую сессию
                duration = time.time() - self.start_time
                start_datetime = datetime.fromtimestamp(self.start_time)
                self.save_session(self.current_app, start_datetime, int(duration))
            
            # Начинаем новую сессию
            self.current_app = new_app
            self.start_time = time.time()
            
            # Обновляем метку
            app_name = self.current_app[:18] + '...' if len(self.current_app) > 18 else self.current_app
            self.current_app_label.config(text=app_name)
        
        self.root.after(1000, self.update_app_info)

    def update_display(self):
        if self.current_app:
            # Показываем общее время для приложения
            total = self.get_current_total()
            time_str = str(timedelta(seconds=int(total))).split('.')[0]
            self.time_label.config(text=time_str)
        
        self.root.after(1000, self.update_display)

    def on_close(self):
        if self.current_app is not None:
            duration = time.time() - self.start_time
            start_datetime = datetime.fromtimestamp(self.start_time)
            self.save_session(self.current_app, start_datetime, int(duration))
        self.root.destroy()

if __name__ == "__main__":
    root = Tk()
    app = AppMonitor(root)
    root.mainloop()