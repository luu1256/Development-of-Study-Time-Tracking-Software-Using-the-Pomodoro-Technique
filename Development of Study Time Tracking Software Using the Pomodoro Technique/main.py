import tkinter as tk
from tkinter import messagebox, ttk, colorchooser, filedialog
import csv
import os
import sys
import math
import wave
import struct
import hashlib
import json
from datetime import datetime, timedelta
import random

try:
    import winsound
    can_play_sound = True
except ImportError:
    can_play_sound = False


def get_app_dir():
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))

    data_path = os.path.join(base, "data")
    try:
        os.makedirs(data_path, exist_ok=True)
        return base
    except OSError:
        user_dir = os.path.join(os.path.expanduser("~"), "FocusFlow_Files")
        os.makedirs(user_dir, exist_ok=True)
        return user_dir


class AudioPlayer:
    def __init__(self, base_dir):
        self.folder = os.path.join(base_dir, "audio")
        os.makedirs(self.folder, exist_ok=True)

        self.tracks = {
            "Lo-Fi Chords": os.path.join(self.folder, "lofi.wav"),
            "Rain Sound": os.path.join(self.folder, "rain.wav"),
            "Alpha Wave 432Hz": os.path.join(self.folder, "alpha.wav"),
        }
        self.alarm_file = os.path.join(self.folder, "alarm.wav")
        self.playing = False
        self.selected_track = "Lo-Fi Chords"

        self.create_default_audio()

    def save_wav(self, path, data, rate=22050):
        if os.path.exists(path):
            return
        with wave.open(path, "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(rate)
            raw = struct.pack(f"<{len(data)}h", *data)
            f.writeframes(raw)

    def create_default_audio(self):
        rate = 22050

        if not os.path.exists(self.tracks["Lo-Fi Chords"]):
            chords = [
                [174.61, 220.00, 261.63, 329.63],
                [164.81, 196.00, 246.94, 293.66],
                [146.83, 174.61, 220.00, 261.63],
                [130.81, 164.81, 196.00, 246.94],
            ]
            samples = []
            length = rate * 2
            for notes in chords:
                for i in range(length):
                    t = i / rate
                    fade = math.sin(math.pi * (i / length)) ** 0.4
                    s = sum(math.sin(2 * math.pi * freq * t) for freq in notes) / len(notes)
                    samples.append(int(s * fade * 5000))
            self.save_wav(self.tracks["Lo-Fi Chords"], samples, rate)

        if not os.path.exists(self.tracks["Rain Sound"]):
            samples = []
            last = 0.0
            total = rate * 6
            rand = random.Random(10)
            for i in range(total):
                noise = rand.uniform(-1.0, 1.0)
                last = 0.88 * last + 0.12 * noise
                edge = 1.0
                if i < 2000:
                    edge = i / 2000.0
                elif i > total - 2000:
                    edge = (total - i) / 2000.0
                samples.append(int(last * edge * 9000))
            self.save_wav(self.tracks["Rain Sound"], samples, rate)

        if not os.path.exists(self.tracks["Alpha Wave 432Hz"]):
            samples = []
            total = rate * 6
            for i in range(total):
                t = i / rate
                v = 0.6 * math.sin(2 * math.pi * 216.0 * t) + 0.4 * math.sin(2 * math.pi * 432.0 * t)
                mod = 0.85 + 0.15 * math.sin(2 * math.pi * 0.5 * t)
                samples.append(int(v * mod * 4600))
            self.save_wav(self.tracks["Alpha Wave 432Hz"], samples, rate)

        if not os.path.exists(self.alarm_file):
            tones = [523.25, 659.25, 783.99, 1046.50]
            samples = []
            step = int(rate * 0.28)
            for idx, freq in enumerate(tones):
                dur = step * 2 if idx == len(tones) - 1 else step
                for i in range(dur):
                    t = i / rate
                    env = math.exp(-4.5 * t)
                    v = 0.75 * math.sin(2 * math.pi * freq * t) + 0.25 * math.sin(2 * math.pi * (freq * 2) * t)
                    samples.append(int(v * env * 14500))
            self.save_wav(self.alarm_file, samples, rate)

    def play_music(self, name=None):
        if name:
            self.selected_track = name
        path = self.tracks.get(self.selected_track)
        if not path or not os.path.exists(path):
            return
        self.playing = True
        if can_play_sound:
            try:
                winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            except Exception:
                pass

    def stop_music(self):
        self.playing = False
        if can_play_sound:
            try:
                winsound.PlaySound(None, 0)
            except Exception:
                pass

    def ring_alarm(self, window=None):
        resume = self.playing
        if can_play_sound and os.path.exists(self.alarm_file):
            try:
                winsound.PlaySound(self.alarm_file, winsound.SND_FILENAME | winsound.SND_ASYNC)
                if resume and window is not None:
                    window.after(1800, lambda: self.play_music(self.selected_track) if self.playing else None)
                return
            except Exception:
                pass
        if window is not None:
            try:
                window.bell()
            except Exception:
                pass


class DataManager:
    def __init__(self, folder):
        self.folder = folder
        os.makedirs(self.folder, exist_ok=True)

        self.tables = {
            "users": ["user_id", "username", "password_hash", "created_at"],
            "tasks": ["task_id", "user_id", "task_name", "is_urgent", "is_important", "label", "is_completed"],
            "sessions": ["session_id", "user_id", "task_name", "duration_minutes", "session_date", "start_hour", "status", "distractions_count"],
            "distractions": ["distraction_id", "user_id", "distraction_text", "logged_time"],
            "study_schedules": ["schedule_id", "user_id", "study_date", "study_time", "task_name", "status"],
            "friends": ["friend_id", "user_id", "friend_name", "status"]
        }

        for name in self.tables:
            file_path = self.file_path(name)
            if not os.path.exists(file_path):
                self.save(name, [])

    def file_path(self, name):
        return os.path.join(self.folder, f"{name}.csv")

    def load(self, name):
        path = self.file_path(name)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def save(self, name, rows):
        path = self.file_path(name)
        cols = self.tables[name]
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=cols)
            writer.writeheader()
            writer.writerows(rows)

    def next_id(self, name, key):
        rows = self.load(name)
        highest = 0
        for r in rows:
            val = int(r[key])
            if val > highest:
                highest = val
        return highest + 1

    def append(self, name, record):
        rows = self.load(name)
        rows.append(record)
        self.save(name, rows)


class PomodoroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FocusFlow Pro - Study Time Tracker")
        self.root.geometry("860x660")
        self.root.minsize(780, 600)
        self.root.withdraw()

        self.app_dir = get_app_dir()
        self.audio = AudioPlayer(self.app_dir)
        self.db = DataManager(os.path.join(self.app_dir, "data"))
        self.seed_data()

        self.user_id = None
        self.username = None

        self.work_seconds = 25 * 60
        self.short_break_seconds = 5 * 60
        self.long_break_seconds = 15 * 60

        self.remaining = self.work_seconds
        self.running = False
        self.locked = False
        self.job_id = None
        self.mode = "Work"
        self.sessions_today = 0
        self.focus_lost_count = 0

        self.bg_color = "#E8F5E9"
        self.card_color = "#FFFFFF"
        self.text_color = "#2E3B2E"
        self.line_color = "#C8E6C9"

        self.quotes = [
            "Discipline is the bridge between goals and accomplishment.",
            "A journey of a thousand miles begins with a single step.",
            "Focus for 25 minutes today, reap success tomorrow.",
            "Persistence creates excellence.",
            "Do not limit your challenges. Challenge your limits."
        ]

        self.root.protocol("WM_DELETE_WINDOW", self.handle_close)
        self.open_login()

    def center(self, win, w, h):
        win.update_idletasks()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")

    def make_hash(self, text):
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def strip_tags(self, text):
        val = text.strip()
        if "]" in val:
            val = val.rsplit("]", 1)[-1].strip()
        return val

    def seed_data(self):
        if len(self.db.load("users")) > 0:
            return

        uid = "1"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.append("users", {
            "user_id": uid,
            "username": "student",
            "password_hash": self.make_hash("123456"),
            "created_at": now_str
        })

        tasks = [
            ("1", "Python Final Project Report", "1", "1", "#Python", "0"),
            ("2", "HSK 2 Chinese Exam Prep", "0", "1", "#Chinese", "0"),
            ("3", "Cisco Packet Tracer Lab", "1", "0", "#Networking", "0"),
            ("4", "Oracle Database SQL Practice", "0", "0", "#Database", "1")
        ]
        for tid, name, urg, imp, lbl, done in tasks:
            self.db.append("tasks", {
                "task_id": tid,
                "user_id": uid,
                "task_name": name,
                "is_urgent": urg,
                "is_important": imp,
                "label": lbl,
                "is_completed": done
            })

        today = datetime.now()
        sid = 1
        for d in range(7):
            day_str = (today - timedelta(days=d)).strftime("%Y-%m-%d")
            for _ in range(random.randint(2, 4)):
                chosen = random.choice(tasks)[1]
                st = "Completed" if random.random() > 0.15 else "Failed (Tab Switch)"
                self.db.append("sessions", {
                    "session_id": str(sid),
                    "user_id": uid,
                    "task_name": chosen,
                    "duration_minutes": "25",
                    "session_date": day_str,
                    "start_hour": str(random.choice([8, 14, 20, 21])),
                    "status": st,
                    "distractions_count": str(random.randint(0, 2))
                })
                sid += 1

        self.db.append("distractions", {
            "distraction_id": "1",
            "user_id": uid,
            "distraction_text": "Check online shopping deals",
            "logged_time": (today - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")
        })
        self.db.append("distractions", {
            "distraction_id": "2",
            "user_id": uid,
            "distraction_text": "Reply to unread messages",
            "logged_time": (today - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
        })

        self.db.append("study_schedules", {
            "schedule_id": "1",
            "user_id": uid,
            "study_date": today.strftime("%Y-%m-%d"),
            "study_time": "20:00",
            "task_name": "Python Final Project Report",
            "status": "Pending"
        })
        self.db.append("study_schedules", {
            "schedule_id": "2",
            "user_id": uid,
            "study_date": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
            "study_time": "09:00",
            "task_name": "HSK 2 Chinese Exam Prep",
            "status": "Pending"
        })

        self.db.append("friends", {
            "friend_id": "1",
            "user_id": uid,
            "friend_name": "David Tran",
            "status": "Studying Python"
        })
        self.db.append("friends", {
            "friend_id": "2",
            "user_id": uid,
            "friend_name": "Hannah Nguyen",
            "status": "On Break"
        })

    def handle_close(self):
        if self.locked:
            messagebox.showwarning("Locked", "Click Stop or Take Break before closing the window.", parent=self.root)
            return
        self.audio.stop_music()
        self.root.destroy()

    def open_login(self):
        self.login_win = tk.Toplevel(self.root)
        self.login_win.title("FocusFlow Pro - Login")
        self.center(self.login_win, 380, 310)
        self.login_win.config(bg=self.bg_color)
        self.login_win.protocol("WM_DELETE_WINDOW", self.root.destroy)

        tk.Label(self.login_win, text="FocusFlow Pro", font=("Helvetica", 18, "bold"), fg="#2E7D32", bg=self.bg_color).pack(pady=15)
        tk.Label(self.login_win, text="Sign in to open your study workspace", font=("Helvetica", 9), fg=self.text_color, bg=self.bg_color).pack()

        box = tk.Frame(self.login_win, bg=self.card_color, highlightbackground=self.line_color, highlightthickness=1, padx=20, pady=15)
        box.pack(pady=12)

        tk.Label(box, text="Username:", bg=self.card_color, font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.user_input = tk.Entry(box, width=20, font=("Helvetica", 10))
        self.user_input.insert(0, "student")
        self.user_input.grid(row=0, column=1, pady=5)

        tk.Label(box, text="Password:", bg=self.card_color, font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.pass_input = tk.Entry(box, width=20, show="*", font=("Helvetica", 10))
        self.pass_input.insert(0, "123456")
        self.pass_input.grid(row=1, column=1, pady=5)

        btns = tk.Frame(self.login_win, bg=self.bg_color)
        btns.pack(pady=5)

        tk.Button(btns, text="Login", command=self.do_login, bg="#81C784", fg="white", font=("Helvetica", 9, "bold"), width=10, pady=3).grid(row=0, column=0, padx=5)
        tk.Button(btns, text="Register", command=self.do_register, bg="#4FC3F7", fg="white", font=("Helvetica", 9, "bold"), width=10, pady=3).grid(row=0, column=1, padx=5)

    def do_login(self):
        uname = self.user_input.get().strip()
        pwd = self.pass_input.get().strip()
        if not uname or not pwd:
            messagebox.showwarning("Input Required", "Please enter username and password.", parent=self.login_win)
            return

        hashed = self.make_hash(pwd)
        found = None
        for u in self.db.load("users"):
            if u["username"] == uname and u["password_hash"] == hashed:
                found = u
                break

        if found:
            self.user_id = found["user_id"]
            self.username = uname
            self.login_win.destroy()

            self.root.deiconify()
            self.center(self.root, 860, 660)
            self.build_ui()
            self.refresh_tasks()
            self.root.bind("<FocusOut>", self.on_focus_out)
            self.poll_schedules()
        else:
            messagebox.showerror("Login Failed", "Wrong username or password.", parent=self.login_win)

    def do_register(self):
        uname = self.user_input.get().strip()
        pwd = self.pass_input.get().strip()
        if not uname or not pwd:
            messagebox.showwarning("Input Required", "Please fill in username and password.", parent=self.login_win)
            return

        for u in self.db.load("users"):
            if u["username"] == uname:
                messagebox.showerror("Error", "This username is already taken.", parent=self.login_win)
                return

        new_uid = str(self.db.next_id("users", "user_id"))
        self.db.append("users", {
            "user_id": new_uid,
            "username": uname,
            "password_hash": self.make_hash(pwd),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        messagebox.showinfo("Registered", "Account created. You can log in now.", parent=self.login_win)

    def do_logout(self):
        if messagebox.askyesno("Logout", "Do you want to log out?", parent=self.root):
            self.cancel_timer()
            self.audio.stop_music()
            self.exit_lock_mode()
            self.user_id = None
            self.username = None
            self.root.withdraw()
            self.open_login()

    def export_backup(self):
        uid = self.user_id
        data = {
            "username": self.username,
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tasks": [r for r in self.db.load("tasks") if r["user_id"] == uid],
            "sessions": [r for r in self.db.load("sessions") if r["user_id"] == uid],
            "distractions": [r for r in self.db.load("distractions") if r["user_id"] == uid],
            "schedules": [r for r in self.db.load("study_schedules") if r["user_id"] == uid]
        }

        path = filedialog.asksaveasfilename(
            title="Save Backup File",
            defaultextension=".json",
            filetypes=[("JSON Backup", "*.json")],
            initialfile=f"{self.username}_backup.json"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Exported", "Backup file saved successfully.", parent=self.root)

    def import_backup(self):
        path = filedialog.askopenfilename(
            title="Open Backup File",
            filetypes=[("JSON Backup", "*.json")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            uid = self.user_id
            current_tasks = self.db.load("tasks")
            existing_names = [t["task_name"] for t in current_tasks if t["user_id"] == uid]

            for t in data.get("tasks", []):
                if t["task_name"] not in existing_names:
                    self.db.append("tasks", {
                        "task_id": str(self.db.next_id("tasks", "task_id")),
                        "user_id": uid,
                        "task_name": t["task_name"],
                        "is_urgent": t.get("is_urgent", "0"),
                        "is_important": t.get("is_important", "0"),
                        "label": t.get("label", "#General"),
                        "is_completed": t.get("is_completed", "0")
                    })

            for s in data.get("sessions", []):
                self.db.append("sessions", {
                    "session_id": str(self.db.next_id("sessions", "session_id")),
                    "user_id": uid,
                    "task_name": s["task_name"],
                    "duration_minutes": s["duration_minutes"],
                    "session_date": s["session_date"],
                    "start_hour": s["start_hour"],
                    "status": s["status"],
                    "distractions_count": s.get("distractions_count", "0")
                })

            for d in data.get("distractions", []):
                self.db.append("distractions", {
                    "distraction_id": str(self.db.next_id("distractions", "distraction_id")),
                    "user_id": uid,
                    "distraction_text": d["distraction_text"],
                    "logged_time": d["logged_time"]
                })

            for sc in data.get("schedules", []):
                self.db.append("study_schedules", {
                    "schedule_id": str(self.db.next_id("study_schedules", "schedule_id")),
                    "user_id": uid,
                    "study_date": sc["study_date"],
                    "study_time": sc["study_time"],
                    "task_name": sc["task_name"],
                    "status": sc.get("status", "Pending")
                })

            self.refresh_tasks()
            messagebox.showinfo("Imported", "Backup data restored.", parent=self.root)
        except Exception as err:
            messagebox.showerror("Error", f"Could not read backup file: {err}", parent=self.root)

    def open_backup_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Data Backup & Restore")
        self.center(win, 380, 190)
        win.config(bg=self.bg_color)

        tk.Label(win, text="Data Backup & Transfer", font=("Helvetica", 11, "bold"), fg="#0D47A1", bg=self.bg_color).pack(pady=10)
        tk.Label(win, text=f"User: {self.username}", font=("Helvetica", 9), bg=self.bg_color).pack(pady=2)

        box = tk.Frame(win, bg=self.bg_color)
        box.pack(pady=10)
        tk.Button(box, text="Export Data (.json)", command=self.export_backup, bg="#E1F5FE", width=24).pack(pady=4)
        tk.Button(box, text="Import Data (.json)", command=self.import_backup, bg="#C8E6C9", width=24).pack(pady=4)

    def on_focus_out(self, event):
        if event.widget == self.root and self.running and self.mode == "Work":
            self.focus_lost_count += 1
            msg = f"Warning: Switched window ({self.focus_lost_count}/3)"
            self.warn_label.config(text=msg, fg="red")
            if self.locked and hasattr(self, "lock_warn_label") and self.lock_warn_label.winfo_exists():
                self.lock_warn_label.config(text=msg, fg="#FF5252")

            if self.focus_lost_count >= 3:
                self.cancel_timer()
                self.exit_lock_mode()
                self.audio.ring_alarm(self.root)
                messagebox.showerror("Session Failed", "You left the study window 3 times. Session marked as failed.", parent=self.root)
                self.record_session("Failed (Tab Switch)")
                self.reset_clock()

    def enter_lock_mode(self, task_title):
        self.locked = True
        self.top_bar.pack_forget()
        self.main_pane.pack_forget()
        self.root.attributes("-fullscreen", True)

        self.lock_screen = tk.Frame(self.root, bg="#1E272E")
        self.lock_screen.pack(fill="both", expand=True)

        center = tk.Frame(self.lock_screen, bg="#1E272E")
        center.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(center, text="FOCUS MODE ACTIVE", font=("Helvetica", 15, "bold"), fg="#81C784", bg="#1E272E").pack(pady=(0, 8))
        tk.Label(center, text=f"Task: {task_title}", font=("Helvetica", 13), fg="#ECEFF1", bg="#1E272E").pack(pady=(0, 18))

        mins, secs = divmod(self.remaining, 60)
        self.lock_clock = tk.Label(center, text=f"{mins:02d}:{secs:02d}", font=("Helvetica", 84, "bold"), fg="#FFFFFF", bg="#1E272E")
        self.lock_clock.pack(pady=10)

        tk.Label(center, text=self.quote_label.cget("text"), font=("Helvetica", 11, "italic"), fg="#B0BEC5", bg="#1E272E", wraplength=620).pack(pady=(10, 14))

        self.lock_warn_label = tk.Label(center, text="Other controls are locked until you take a break or stop.", font=("Helvetica", 10), fg="#4FC3F7", bg="#1E272E")
        self.lock_warn_label.pack(pady=(0, 26))

        controls = tk.Frame(center, bg="#1E272E")
        controls.pack()
        tk.Button(controls, text="Take Break", command=self.start_break, width=15, height=2, bg="#FFB74D", fg="white", font=("Helvetica", 11, "bold")).grid(row=0, column=0, padx=14)
        tk.Button(controls, text="Stop", command=self.stop_clock, width=15, height=2, bg="#E57373", fg="white", font=("Helvetica", 11, "bold")).grid(row=0, column=1, padx=14)

    def exit_lock_mode(self):
        if not self.locked:
            return
        self.locked = False
        self.root.attributes("-fullscreen", False)
        if hasattr(self, "lock_screen") and self.lock_screen.winfo_exists():
            self.lock_screen.destroy()
        self.top_bar.pack(fill="x")
        self.main_pane.pack(fill="both", expand=True, padx=10, pady=8)

    def build_ui(self):
        self.root.config(bg=self.bg_color)
        for w in self.root.winfo_children():
            w.destroy()

        self.top_bar = tk.Frame(self.root, bg="#ECEFF1")
        self.top_bar.pack(fill="x")

        tk.Label(self.top_bar, text=f"User: {self.username}", font=("Helvetica", 10, "bold"), bg="#ECEFF1", fg="#2E7D32").pack(side="left", padx=10, pady=5)
        tk.Button(self.top_bar, text="Backup", command=self.open_backup_dialog, bg="#BBDEFB", font=("Helvetica", 8, "bold")).pack(side="left", padx=3)
        tk.Button(self.top_bar, text="Theme", command=self.pick_theme_color, bg="#FFFFFF", font=("Helvetica", 8)).pack(side="left", padx=2)

        self.track_box = ttk.Combobox(self.top_bar, values=list(self.audio.tracks.keys()), width=17, state="readonly", font=("Helvetica", 8))
        self.track_box.set(self.audio.selected_track)
        self.track_box.bind("<<ComboboxSelected>>", self.change_track)
        self.track_box.pack(side="left", padx=(6, 2))

        self.music_btn = tk.Button(self.top_bar, text="Music: OFF", command=self.toggle_audio, bg="#FFFFFF", font=("Helvetica", 8))
        self.music_btn.pack(side="left", padx=2)

        tk.Button(self.top_bar, text="Logout", command=self.do_logout, bg="#FFCDD2", font=("Helvetica", 8, "bold")).pack(side="right", padx=10)
        tk.Button(self.top_bar, text="Buddies", command=self.open_buddies, bg="#E1F5FE", font=("Helvetica", 8)).pack(side="right", padx=2)

        self.main_pane = tk.Frame(self.root, bg=self.bg_color)
        self.main_pane.pack(fill="both", expand=True, padx=10, pady=8)

        left_col = tk.Frame(self.main_pane, bg=self.bg_color, width=350)
        left_col.pack(side="left", fill="both", expand=False, padx=(0, 8))

        timer_card = tk.Frame(left_col, bg=self.card_color, highlightbackground=self.line_color, highlightthickness=1, padx=12, pady=10)
        timer_card.pack(fill="x", pady=(0, 8))

        self.fatigue_label = tk.Label(timer_card, text="Fatigue Level: Normal (0%)", font=("Helvetica", 9, "bold"), fg="#2E7D32", bg=self.card_color)
        self.fatigue_label.pack(pady=(0, 2))

        self.clock_label = tk.Label(timer_card, text="25:00", font=("Helvetica", 42, "bold"), fg="#2E3B2E", bg=self.card_color)
        self.clock_label.pack(pady=2)

        self.quote_label = tk.Label(timer_card, text=random.choice(self.quotes), font=("Helvetica", 8, "italic"), fg="#555555", bg=self.card_color, wraplength=280)
        self.quote_label.pack(pady=2)

        self.status_label = tk.Label(timer_card, text="Status: Ready", font=("Helvetica", 9, "bold"), fg="#3F51B5", bg=self.card_color)
        self.status_label.pack(pady=1)

        self.warn_label = tk.Label(timer_card, text="", font=("Helvetica", 8, "bold"), bg=self.card_color)
        self.warn_label.pack()

        btn_row = tk.Frame(timer_card, bg=self.card_color)
        btn_row.pack(pady=5)
        tk.Button(btn_row, text="Start Focus", command=self.start_work, width=10, bg="#81C784", fg="white", font=("Helvetica", 8, "bold")).grid(row=0, column=0, padx=2)
        tk.Button(btn_row, text="Take Break", command=self.start_break, width=10, bg="#FFB74D", fg="white", font=("Helvetica", 8, "bold")).grid(row=0, column=1, padx=2)
        tk.Button(btn_row, text="Stop", command=self.stop_clock, width=8, bg="#E57373", fg="white", font=("Helvetica", 8, "bold")).grid(row=0, column=2, padx=2)

        sched_card = tk.Frame(left_col, bg=self.card_color, highlightbackground=self.line_color, highlightthickness=1, padx=12, pady=8)
        sched_card.pack(fill="x", pady=(0, 8))

        tk.Label(sched_card, text="Study Schedule & Alarm", font=("Helvetica", 9, "bold"), bg=self.card_color, fg=self.text_color).pack(anchor="w", pady=(0, 3))

        dt_row = tk.Frame(sched_card, bg=self.card_color)
        dt_row.pack(fill="x")
        tk.Label(dt_row, text="Date:", bg=self.card_color, font=("Helvetica", 8)).pack(side="left")
        self.date_input = tk.Entry(dt_row, width=10, font=("Helvetica", 8))
        self.date_input.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_input.pack(side="left", padx=2)

        tk.Label(dt_row, text="Time:", bg=self.card_color, font=("Helvetica", 8)).pack(side="left", padx=2)
        self.hour_box = ttk.Spinbox(dt_row, from_=0, to=23, width=3, format="%02.0f")
        self.hour_box.set("20")
        self.hour_box.pack(side="left")

        tk.Label(dt_row, text=":", bg=self.card_color).pack(side="left")
        self.min_box = ttk.Spinbox(dt_row, from_=0, to=59, width=3, format="%02.0f")
        self.min_box.set("00")
        self.min_box.pack(side="left")

        s_btns = tk.Frame(sched_card, bg=self.card_color)
        s_btns.pack(fill="x", pady=4)
        tk.Button(s_btns, text="Add Schedule", command=self.save_schedule, bg="#81C784", fg="white", font=("Helvetica", 8, "bold")).pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(s_btns, text="View List", command=self.open_schedules, bg="#E1F5FE", font=("Helvetica", 8)).pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(s_btns, text="Test Alarm", command=lambda: self.audio.ring_alarm(self.root), bg="#FFF9C4", font=("Helvetica", 8)).pack(side="left", padx=2)

        note_card = tk.Frame(left_col, bg=self.card_color, highlightbackground=self.line_color, highlightthickness=1, padx=12, pady=8)
        note_card.pack(fill="x")

        tk.Label(note_card, text="Distraction Notes (Brain Dump)", font=("Helvetica", 9, "bold"), bg=self.card_color, fg=self.text_color).pack(anchor="w", pady=(0, 3))
        n_row = tk.Frame(note_card, bg=self.card_color)
        n_row.pack(fill="x")
        self.note_input = tk.Entry(n_row, width=28, font=("Helvetica", 8))
        self.note_input.pack(side="left", padx=(0, 4))
        tk.Button(n_row, text="Save", command=self.save_note, bg="#80DEEA", font=("Helvetica", 8, "bold")).pack(side="left", fill="x", expand=True)

        right_col = tk.Frame(self.main_pane, bg=self.bg_color)
        right_col.pack(side="right", fill="both", expand=True)

        task_card = tk.Frame(right_col, bg=self.card_color, highlightbackground=self.line_color, highlightthickness=1, padx=12, pady=10)
        task_card.pack(fill="both", expand=True, pady=(0, 8))

        tk.Label(task_card, text="Task & Priority Manager", font=("Helvetica", 11, "bold"), fg=self.text_color, bg=self.card_color).pack(anchor="w", pady=(0, 4))

        find_row = tk.Frame(task_card, bg=self.card_color)
        find_row.pack(fill="x", pady=2)
        tk.Label(find_row, text="Search:", bg=self.card_color, font=("Helvetica", 8)).pack(side="left")
        self.search_input = tk.Entry(find_row, width=16, font=("Helvetica", 8))
        self.search_input.pack(side="left", padx=2)
        tk.Button(find_row, text="Find", command=self.filter_tasks, bg="#E0E0E0", font=("Helvetica", 8)).pack(side="left", padx=1)
        tk.Button(find_row, text="Reset", command=self.refresh_tasks, bg="#E0E0E0", font=("Helvetica", 8)).pack(side="left", padx=1)

        t_row = tk.Frame(task_card, bg=self.card_color)
        t_row.pack(fill="x", pady=2)
        tk.Label(t_row, text="Task:", bg=self.card_color, font=("Helvetica", 8)).pack(side="left")
        self.task_box = ttk.Combobox(t_row, width=32, font=("Helvetica", 8))
        self.task_box.pack(side="left", padx=2, fill="x", expand=True)

        opt_row = tk.Frame(task_card, bg=self.card_color)
        opt_row.pack(fill="x", pady=2)
        tk.Label(opt_row, text="Tag:", bg=self.card_color, font=("Helvetica", 8)).pack(side="left")
        self.tag_input = tk.Entry(opt_row, width=10, font=("Helvetica", 8))
        self.tag_input.insert(0, "#General")
        self.tag_input.pack(side="left", padx=2)

        self.urgent_var = tk.IntVar()
        self.important_var = tk.IntVar()
        tk.Checkbutton(opt_row, text="Urgent", variable=self.urgent_var, bg=self.card_color, font=("Helvetica", 8)).pack(side="left")
        tk.Checkbutton(opt_row, text="Important", variable=self.important_var, bg=self.card_color, font=("Helvetica", 8)).pack(side="left")

        t_btns = tk.Frame(task_card, bg=self.card_color)
        t_btns.pack(fill="x", pady=3)
        tk.Button(t_btns, text="Add Task", command=self.save_task, bg="#81C784", fg="white", font=("Helvetica", 8, "bold")).pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(t_btns, text="Complete Task", command=self.complete_task, bg="#80DEEA", font=("Helvetica", 8, "bold")).pack(side="left", expand=True, fill="x", padx=2)

        tk.Label(task_card, text="Task List:", font=("Helvetica", 9, "bold"), bg=self.card_color, fg="#555555").pack(anchor="w", pady=(6, 2))

        self.tree = ttk.Treeview(task_card, columns=("tag", "priority", "name"), show="headings", height=8)
        self.tree.heading("tag", text="Tag")
        self.tree.heading("priority", text="Priority")
        self.tree.heading("name", text="Task Name")
        self.tree.column("tag", width=80)
        self.tree.column("priority", width=90)
        self.tree.column("name", width=180)
        self.tree.pack(fill="both", expand=True, pady=2)

        tk.Button(right_col, text="Performance Analytics", command=self.open_analytics, bg="#BBDEFB", font=("Helvetica", 8, "bold")).pack(fill="x", pady=1)
        tk.Button(right_col, text="Study Schedule Suggestion", command=self.open_suggestion, bg="#FFFDD0", font=("Helvetica", 8, "bold")).pack(fill="x", pady=1)
        tk.Button(right_col, text="Export Report (.doc)", command=self.export_doc, bg="#B2DFDB", font=("Helvetica", 8, "bold")).pack(fill="x", pady=1)

    def pick_theme_color(self):
        chosen = colorchooser.askcolor(title="Choose Background Color")[1]
        if chosen:
            self.bg_color = chosen
            self.root.config(bg=chosen)
            self.main_pane.config(bg=chosen)

    def change_track(self, event=None):
        name = self.track_box.get()
        self.audio.selected_track = name
        if self.audio.playing:
            self.audio.play_music(name)

    def toggle_audio(self):
        if not self.audio.playing:
            self.audio.play_music(self.track_box.get())
            self.music_btn.config(text="Music: ON", bg="#C8E6C9")
        else:
            self.audio.stop_music()
            self.music_btn.config(text="Music: OFF", bg="#FFFFFF")

    def open_buddies(self):
        win = tk.Toplevel(self.root)
        win.title("Study Buddies")
        self.center(win, 440, 290)
        win.config(bg=self.bg_color)

        tk.Label(win, text="Study Group Members:", font=("Helvetica", 10, "bold"), bg=self.bg_color, fg=self.text_color).pack(pady=5)

        tv = ttk.Treeview(win, columns=("id", "name", "status"), show="headings", height=6)
        tv.heading("id", text="ID")
        tv.heading("name", text="Name")
        tv.heading("status", text="Status")
        tv.column("id", width=40)
        tv.column("name", width=180)
        tv.column("status", width=180)
        tv.pack(padx=10, pady=5, fill="both", expand=True)

        for r in self.db.load("friends"):
            if r["user_id"] == self.user_id:
                tv.insert("", "end", values=(r["friend_id"], r["friend_name"], r["status"]))

        row = tk.Frame(win, bg=self.bg_color)
        row.pack(pady=5)
        tk.Label(row, text="Name:", bg=self.bg_color).pack(side="left", padx=2)
        name_ent = tk.Entry(row, width=18)
        name_ent.pack(side="left", padx=2)

        def add_buddy():
            val = name_ent.get().strip()
            if val:
                fid = str(self.db.next_id("friends", "friend_id"))
                self.db.append("friends", {
                    "friend_id": fid,
                    "user_id": self.user_id,
                    "friend_name": val,
                    "status": "Available"
                })
                tv.insert("", "end", values=(fid, val, "Available"))
                name_ent.delete(0, tk.END)

        tk.Button(row, text="Add", command=add_buddy, bg="#81C784", fg="white", font=("Helvetica", 8, "bold")).pack(side="left", padx=4)

    def complete_task(self):
        clean = self.strip_tags(self.task_box.get())
        if not clean:
            return

        rows = self.db.load("tasks")
        changed = False
        for t in rows:
            if t["user_id"] == self.user_id and clean.lower() in t["task_name"].lower():
                t["is_completed"] = "1"
                changed = True

        if changed:
            self.db.save("tasks", rows)
            self.refresh_tasks()
            messagebox.showinfo("Done", f"Marked '{clean}' as completed.", parent=self.root)

    def filter_tasks(self):
        kw = self.search_input.get().strip().lower()
        if not kw:
            self.refresh_tasks()
            return

        for item in self.tree.get_children():
            self.tree.delete(item)

        items = []
        for t in self.db.load("tasks"):
            if t["user_id"] == self.user_id and (kw in t["task_name"].lower() or kw in t["label"].lower()):
                prefix = "[Done] " if t["is_completed"] == "1" else ""
                urg = t["is_urgent"] == "1"
                imp = t["is_important"] == "1"
                prio = "Do First" if (urg and imp) else ("Schedule" if (imp and not urg) else ("Delegate" if (urg and not imp) else "Eliminate"))
                tag = f"[{t['label']}]"
                items.append(f"{prefix}{tag} [{prio}] {t['task_name']}")
                self.tree.insert("", "end", values=(tag, prio, f"{prefix}{t['task_name']}"))

        self.task_box["values"] = items
        if items:
            self.task_box.current(0)

    def save_task(self):
        name = self.strip_tags(self.task_box.get())
        lbl = self.tag_input.get().strip() or "#General"
        if not name:
            messagebox.showwarning("Input Required", "Please enter a task name.", parent=self.root)
            return

        rows = self.db.load("tasks")
        match = None
        for t in rows:
            if t["user_id"] == self.user_id and t["task_name"].lower() == name.lower():
                match = t
                break

        if match:
            match["is_urgent"] = str(self.urgent_var.get())
            match["is_important"] = str(self.important_var.get())
            match["label"] = lbl
            match["is_completed"] = "0"
            self.db.save("tasks", rows)
        else:
            self.db.append("tasks", {
                "task_id": str(self.db.next_id("tasks", "task_id")),
                "user_id": self.user_id,
                "task_name": name,
                "is_urgent": str(self.urgent_var.get()),
                "is_important": str(self.important_var.get()),
                "label": lbl,
                "is_completed": "0"
            })

        self.refresh_tasks()

    def refresh_tasks(self):
        rows = [t for t in self.db.load("tasks") if t["user_id"] == self.user_id]
        rows.sort(key=lambda x: (int(x["is_completed"]), -int(x["is_important"]), -int(x["is_urgent"])))

        for item in self.tree.get_children():
            self.tree.delete(item)

        items = []
        for t in rows:
            prefix = "[Done] " if t["is_completed"] == "1" else ""
            urg = t["is_urgent"] == "1"
            imp = t["is_important"] == "1"
            prio = "Do First" if (urg and imp) else ("Schedule" if (imp and not urg) else ("Delegate" if (urg and not imp) else "Eliminate"))
            tag = f"[{t['label']}]"
            items.append(f"{prefix}{tag} [{prio}] {t['task_name']}")
            self.tree.insert("", "end", values=(tag, prio, f"{prefix}{t['task_name']}"))

        self.task_box["values"] = items
        if items:
            self.task_box.current(0)

    def save_schedule(self):
        d = self.date_input.get().strip()
        h = f"{int(self.hour_box.get()):02d}"
        m = f"{int(self.min_box.get()):02d}"
        t_str = f"{h}:{m}"
        clean = self.strip_tags(self.task_box.get())

        if not d or not clean:
            messagebox.showwarning("Input Required", "Please enter a valid date and task.", parent=self.root)
            return

        self.db.append("study_schedules", {
            "schedule_id": str(self.db.next_id("study_schedules", "schedule_id")),
            "user_id": self.user_id,
            "study_date": d,
            "study_time": t_str,
            "task_name": clean,
            "status": "Pending"
        })
        messagebox.showinfo("Saved", f"Scheduled '{clean}' at {t_str} on {d}.", parent=self.root)

    def open_schedules(self):
        win = tk.Toplevel(self.root)
        win.title("Study Schedules")
        self.center(win, 490, 310)
        win.config(bg=self.bg_color)

        tv = ttk.Treeview(win, columns=("id", "date", "time", "task", "status"), show="headings", height=8)
        tv.heading("id", text="ID")
        tv.heading("date", text="Date")
        tv.heading("time", text="Time")
        tv.heading("task", text="Task")
        tv.heading("status", text="Status")
        tv.column("id", width=30)
        tv.column("date", width=90)
        tv.column("time", width=60)
        tv.column("task", width=200)
        tv.column("status", width=80)
        tv.pack(padx=10, pady=5, fill="both", expand=True)

        rows = [s for s in self.db.load("study_schedules") if s["user_id"] == self.user_id]
        rows.sort(key=lambda x: (x["study_date"], x["study_time"]))
        for s in rows:
            tv.insert("", "end", values=(s["schedule_id"], s["study_date"], s["study_time"], s["task_name"], s["status"]))

        def remove_item():
            sel = tv.selection()
            if not sel:
                return
            sid = str(tv.item(sel[0])["values"][0])
            kept = [s for s in self.db.load("study_schedules") if s["schedule_id"] != sid]
            self.db.save("study_schedules", kept)
            tv.delete(sel[0])

        tk.Button(win, text="Delete Selected", command=remove_item, bg="#FFCDD2", font=("Helvetica", 8, "bold")).pack(pady=4)

    def poll_schedules(self):
        if self.user_id and not self.locked:
            now = datetime.now()
            d_now = now.strftime("%Y-%m-%d")
            t_now = now.strftime("%H:%M")

            rows = self.db.load("study_schedules")
            updated = False
            for s in rows:
                if s["user_id"] == self.user_id and s["study_date"] == d_now and s["study_time"] == t_now and s["status"] == "Pending":
                    s["status"] = "Notified"
                    updated = True
                    self.task_box.set(s["task_name"])
                    self.audio.ring_alarm(self.root)
                    messagebox.showinfo("Study Reminder", f"Time to study: {s['task_name']} ({t_now})", parent=self.root)
            if updated:
                self.db.save("study_schedules", rows)

        self.root.after(5000, self.poll_schedules)

    def save_note(self):
        txt = self.note_input.get().strip()
        if txt:
            self.db.append("distractions", {
                "distraction_id": str(self.db.next_id("distractions", "distraction_id")),
                "user_id": self.user_id,
                "distraction_text": txt,
                "logged_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            self.note_input.delete(0, tk.END)
            messagebox.showinfo("Saved", "Note saved. Return to your study task.", parent=self.root)

    def tick(self):
        if self.running and self.remaining > 0:
            mins, secs = divmod(self.remaining, 60)
            formatted = f"{mins:02d}:{secs:02d}"
            self.clock_label.config(text=formatted)
            if self.locked and hasattr(self, "lock_clock") and self.lock_clock.winfo_exists():
                self.lock_clock.config(text=formatted)
            self.remaining -= 1
            self.job_id = self.root.after(1000, self.tick)
        elif self.running and self.remaining == 0:
            self.running = False
            self.audio.ring_alarm(self.root)
            if self.mode == "Work":
                self.sessions_today += 1
                self.record_session("Completed")
                self.exit_lock_mode()
                messagebox.showinfo("Session Complete", f"Completed Pomodoro #{self.sessions_today}.", parent=self.root)
                self.update_fatigue()
            else:
                messagebox.showinfo("Break Over", "Break finished. Ready for the next session.", parent=self.root)
            self.reset_clock()

    def update_fatigue(self):
        pct = min(100, self.sessions_today * 20)
        if pct < 50:
            self.fatigue_label.config(text=f"Fatigue Level: Normal ({pct}%)", fg="green")
        elif pct < 80:
            self.fatigue_label.config(text=f"Fatigue Level: Moderate ({pct}%)", fg="orange")
        else:
            self.fatigue_label.config(text=f"Fatigue Level: High - Take a Long Break ({pct}%)", fg="red")

    def start_work(self):
        chosen = self.task_box.get().strip()
        if not chosen:
            messagebox.showwarning("Input Required", "Select or type a task first.", parent=self.root)
            return

        self.cancel_timer()
        self.focus_lost_count = 0
        self.warn_label.config(text="Window focus monitor active", fg="#E57373")
        self.quote_label.config(text=random.choice(self.quotes))
        self.mode = "Work"
        self.status_label.config(text=f"Studying: {chosen}")
        self.remaining = self.work_seconds
        self.running = True

        self.enter_lock_mode(chosen)
        self.tick()

    def start_break(self):
        self.cancel_timer()
        self.exit_lock_mode()
        self.warn_label.config(text="")
        self.mode = "Break"
        if self.sessions_today > 0 and self.sessions_today % 4 == 0:
            self.remaining = self.long_break_seconds
            self.status_label.config(text="Mode: Long Break (15 min)")
        else:
            self.remaining = self.short_break_seconds
            self.status_label.config(text="Mode: Short Break (5 min)")
        self.running = True
        self.tick()

    def stop_clock(self):
        self.cancel_timer()
        self.exit_lock_mode()
        self.reset_clock()

    def cancel_timer(self):
        self.running = False
        if self.job_id:
            self.root.after_cancel(self.job_id)
            self.job_id = None

    def reset_clock(self):
        self.remaining = self.work_seconds
        mins, secs = divmod(self.remaining, 60)
        self.clock_label.config(text=f"{mins:02d}:{secs:02d}")
        self.warn_label.config(text="")
        self.status_label.config(text="Status: Ready")
        self.focus_lost_count = 0

    def record_session(self, status):
        clean = self.strip_tags(self.task_box.get())
        now = datetime.now()
        self.db.append("sessions", {
            "session_id": str(self.db.next_id("sessions", "session_id")),
            "user_id": self.user_id,
            "task_name": clean,
            "duration_minutes": "25",
            "session_date": now.strftime("%Y-%m-%d"),
            "start_hour": str(now.hour),
            "status": status,
            "distractions_count": str(self.focus_lost_count)
        })

    def open_suggestion(self):
        rows = [s for s in self.db.load("sessions") if s["user_id"] == self.user_id and s["status"] == "Completed"]
        hours = [int(s["start_hour"]) for s in rows]
        if not hours:
            messagebox.showinfo("Study Suggestion", "Complete more sessions to generate a suggestion.", parent=self.root)
            return

        morn = sum(1 for h in hours if 5 <= h < 12)
        aft = sum(1 for h in hours if 12 <= h < 18)
        eve = sum(1 for h in hours if 18 <= h <= 23)
        best = "Morning (5:00 - 12:00)" if morn >= max(aft, eve) else ("Afternoon (12:00 - 18:00)" if aft >= eve else "Evening (18:00 - 23:00)")

        msg = (
            f"Study Habit Summary ({self.username}):\n"
            f"- Most Productive Period: {best}\n"
            f"- Completed Sessions: {len(hours)}\n\n"
            f"Recommendation:\n"
            f"1. Work on [Do First] tasks during {best}.\n"
            f"2. Use Focus Mode for difficult assignments."
        )
        messagebox.showinfo("Study Schedule Suggestion", msg, parent=self.root)

    def open_analytics(self):
        win = tk.Toplevel(self.root)
        win.title("Performance Analytics")
        self.center(win, 440, 360)
        win.config(bg=self.bg_color)

        rows = [s for s in self.db.load("sessions") if s["user_id"] == self.user_id]
        done = sum(1 for s in rows if s["status"] == "Completed")
        total = len(rows)
        pct = (done / total * 100) if total > 0 else 0

        tk.Label(win, text=f"Completion Rate: {pct:.1f}% ({done}/{total} sessions)", font=("Helvetica", 11, "bold"), fg="#2E7D32", bg=self.bg_color).pack(pady=10)
        tk.Label(win, text="Recent Distraction Notes:", font=("Helvetica", 9, "bold"), bg=self.bg_color).pack(anchor="w", padx=15)

        notes = [d for d in self.db.load("distractions") if d["user_id"] == self.user_id]
        for d in reversed(notes[-5:]):
            tk.Label(win, text=f"- {d['distraction_text']} ({d['logged_time'][11:16]})", fg="#444444", bg=self.bg_color).pack(anchor="w", padx=25)

    def export_doc(self):
        out_path = os.path.join(self.app_dir, f"Study_Report_{self.username}_{datetime.now().strftime('%Y%m%d_%H%M')}.doc")
        rows = [s for s in self.db.load("sessions") if s["user_id"] == self.user_id]
        done_rows = [s for s in rows if s["status"] == "Completed"]
        done = len(done_rows)
        total = len(rows)
        pct = (done / total * 100) if total > 0 else 0

        by_task = {}
        for s in done_rows:
            name = s["task_name"]
            by_task[name] = by_task.get(name, 0) + int(s["duration_minutes"])

        html = f"""<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
<head><meta charset='utf-8'><title>Study Report</title></head>
<body>
    <h1>STUDY TIME TRACKING REPORT</h1>
    <p><b>Username:</b> {self.username}</p>
    <p><b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <ul>
        <li><b>Total Sessions:</b> {total}</li>
        <li><b>Completed Sessions:</b> {done}</li>
        <li><b>Success Rate:</b> {pct:.1f}%</li>
    </ul>
    <h2>Study Time by Task</h2>
    <table border='1' cellpadding='8' style='border-collapse: collapse;'>
        <tr><th>Task Name</th><th>Total Time (Minutes)</th></tr>
"""
        for name, mins in by_task.items():
            html += f"<tr><td>{name}</td><td>{mins} mins</td></tr>\n"
        html += "</table></body></html>"

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        messagebox.showinfo("Report Exported", f"Saved report to:\n{out_path}", parent=self.root)


if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroApp(root)
    root.mainloop()