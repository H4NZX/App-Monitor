import sys
import csv
import time
import win32gui
import win32process
import win32api
import win32con
import pythoncom
import threading
from tkinter import *
from datetime import datetime, timedelta
from collections import defaultdict
import os

class TaskbarApp:
    def __init__(self):
        self.root = Tk()
        self.root.withdraw()
        
        self.current_app = None
        self.start_time = None
        self.total_times = defaultdict(int)
        self.session_data = []
        self.monitoring = False
        
        self.load_history()
        self.create_tray_icon()
        self.control_panel = None
        self.start_monitoring()

    def create_tray_icon(self):
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "TaskbarAppClass"
        wc.lpfnWndProc = self.window_procedure
        self.class_atom = win32gui.RegisterClass(wc)
        
        self.hwnd = win32gui.CreateWindow(
            self.class_atom,
            "AppMonitor",
            0, 0, 0, 0, 0, 0, 0, wc.hInstance, None
        )
        win32gui.UpdateWindow(self.hwnd)
        
        self.set_tray_icon("Initializing...")
        self.update_tray_tooltip()

    def window_procedure(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_COMMAND:
            self.handle_menu_command(wparam)
        elif msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
        elif msg == win32con.WM_USER + 20:
            if lparam == win32con.WM_RBUTTONUP:
                self.show_context_menu()
            elif lparam == win32con.WM_LBUTTONUP:
                self.show_control_panel()
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def set_tray_icon(self, tooltip):
        icon_flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        self.nid = (self.hwnd, 0, icon_flags, win32con.WM_USER + 20, hicon, tooltip)
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, self.nid)

    def update_tray_tooltip(self):
        def _update():
            while True:
                try:
                    current_total = self.get_current_total()
                    time_str = str(timedelta(seconds=int(current_total))).split('.')[0]
                    app_name = self.current_app[:20] + '...' if self.current_app and len(self.current_app) > 20 else self.current_app
                    tooltip = f"{app_name}\nTotal: {time_str}"
                    win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, (self.hwnd, 0, win32gui.NIF_TIP, 0, 0, tooltip))
                except Exception as e:
                    print(f"Tooltip update error: {e}")
                time.sleep(1)
        
        threading.Thread(target=_update, daemon=True).start()

    def start_monitoring(self):
        self.monitoring = True
        def monitor():
            while self.monitoring:
                new_app = self.get_active_app()
                if new_app != self.current_app:
                    self.handle_app_change(new_app)
                time.sleep(1)
        
        threading.Thread(target=monitor, daemon=True).start()

    def stop_monitoring(self):
        self.monitoring = False

    def get_active_app(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
            return win32process.GetModuleFileNameEx(handle, 0).split('\\')[-1]
        except:
            return "Unknown"

    def handle_app_change(self, new_app):
        if self.current_app:
            duration = time.time() - self.start_time
            self.save_session(self.current_app, datetime.fromtimestamp(self.start_time), int(duration))
        
        self.current_app = new_app
        self.start_time = time.time()
        self.update_top_apps()

    def save_session(self, app_name, start_time, duration):
        self.total_times[app_name] += duration
        with open('app_history.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                app_name,
                start_time.strftime("%Y-%m-%d"),
                start_time.strftime("%H:%M:%S"),
                duration
            ])

    def load_history(self):
        try:
            with open('app_history.csv', 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 4:
                        self.total_times[row[0]] += int(row[3])
        except FileNotFoundError:
            pass

    def get_current_total(self):
        if self.current_app and self.start_time:
            return self.total_times[self.current_app] + (time.time() - self.start_time)
        return 0

    def update_top_apps(self):
        temp_times = self.total_times.copy()
        if self.current_app and self.start_time:
            temp_times[self.current_app] += (time.time() - self.start_time)
        
        sorted_apps = sorted(temp_times.items(), key=lambda x: x[1], reverse=True)[:5]
        
        with open('top_apps.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Rank", "Application", "Total Time"])
            for rank, (app, seconds) in enumerate(sorted_apps, 1):
                writer.writerow([rank, app, str(timedelta(seconds=seconds))])

    def show_control_panel(self):
        if not self.control_panel or not self.control_panel.winfo_exists():
            self.control_panel = Toplevel()
            self.control_panel.title("App Monitor Control Panel")
            self.control_panel.geometry("300x400")
            
            Label(self.control_panel, text="Текущее приложение:", font=('Arial', 10, 'bold')).pack(pady=5)
            self.current_app_label = Label(self.control_panel, text="", font=('Arial', 9))
            self.current_app_label.pack()
            
            Label(self.control_panel, text="Общее время:", font=('Arial', 10, 'bold')).pack(pady=5)
            self.total_time_label = Label(self.control_panel, text="", font=('Arial', 9))
            self.total_time_label.pack()
            
            Label(self.control_panel, text="Топ приложений:", font=('Arial', 10, 'bold')).pack(pady=5)
            self.top_apps_text = Text(self.control_panel, height=10, width=30)
            self.top_apps_text.pack(padx=10)
            
            Button(self.control_panel, text="Начать мониторинг", command=self.start_monitoring).pack(pady=5)
            Button(self.control_panel, text="Остановить мониторинг", command=self.stop_monitoring).pack(pady=5)
            Button(self.control_panel, text="Скачать отчет", command=self.download_report).pack(pady=5)
            Button(self.control_panel, text="Обновить", command=self.update_control_panel).pack(pady=5)
            Button(self.control_panel, text="Выход", command=self.exit_app).pack(pady=5)
            
            self.update_control_panel()
        
        self.control_panel.deiconify()

    def update_control_panel(self):
        if self.current_app:
            self.current_app_label.config(text=self.current_app)
            total = self.get_current_total()
            self.total_time_label.config(text=str(timedelta(seconds=int(total))))
        
        try:
            with open('top_apps.csv', 'r') as f:
                self.top_apps_text.delete(1.0, END)
                reader = csv.reader(f)
                next(reader)
                for row in reader:
                    self.top_apps_text.insert(END, f"{row[0]}. {row[1]} - {row[2]}\n")
        except FileNotFoundError:
            self.top_apps_text.insert(END, "Нет доступных данных")

    def download_report(self):
        report_path = os.path.join(os.path.expanduser("~"), "Downloads", "app_report.csv")
        with open(report_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Приложение", "Общее время"])
            for app, total in self.total_times.items():
                writer.writerow([app, str(timedelta(seconds=total))])
        print(f"Отчет скачан в {report_path}")

    def show_context_menu(self):
        menu = win32gui.CreatePopupMenu()
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1000, "Показать панель управления")
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1001, "Выход")
        
        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(
            menu,
            win32con.TPM_LEFTALIGN | win32con.TPM_LEFTBUTTON,
            pos[0],
            pos[1],
            0,
            self.hwnd,
            None
        )
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        win32gui.DestroyMenu(menu)

    def handle_menu_command(self, command):
        if command == 1000:
            self.show_control_panel()
        elif command == 1001:
            self.exit_app()

    def exit_app(self):
        if self.current_app:
            duration = time.time() - self.start_time
            self.save_session(self.current_app, datetime.fromtimestamp(self.start_time), int(duration))
        
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, self.nid)
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    pythoncom.CoInitialize()
    app = TaskbarApp()
    win32gui.PumpMessages()