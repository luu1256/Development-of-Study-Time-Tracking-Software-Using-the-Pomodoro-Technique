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
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


def get_writable_base_dir():
    """Returns a reliable, writable directory both in .py mode and frozen .exe mode."""
    if getattr(sys, "frozen", False):
        candidate = os.path.dirname(sys.executable)
    else:
        candidate = os.path.dirname(os.path.abspath(__file__))

    try:
        test_file = os.path.join(candidate, ".write_test")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test_file)
        return candidate
    except OSError:
        fallback = os.path.join(os.path.expanduser("~"), "FocusFlowPro_Data")
        os.makedirs(fallback, exist_ok=True)
        return fallback


class BuiltInAudioEngine:
    """Generates and plays built-in ambient music loops and alarm chimes without external assets."""

    def __init__(self, base_dir):
        self.audio_dir = os.path.join(base_dir, "assets_audio")
        os.makedirs(self.audio_dir, exist_ok=True)

        self.tracks = {
            "Lo-Fi Warm Chords": os.path.join(self.audio_dir, "lofi_chords.wav"),
            "Soft Rain Ambience": os.path.join(self.audio_dir, "soft_rain.wav"),
            "432Hz Alpha Focus": os.path.join(self.audio_dir, "alpha_432hz.wav"),
        }
        self.alarm_path = os.path.join(self.audio_dir, "alarm_chime.wav")
        self.is_playing = False
        self.current_track = "Lo-Fi Warm Chords"

        self._ensure_audio_files()

    def _write_wav(self, filepath, samples, sample_rate=22050):
        if os.path.exists(filepath):
            return
        with wave.open(filepath, "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            packed = struct.pack(f"<{len(samples)}h", *samples)
            wf.writeframes(packed)

    def _ensure_audio_files(self):
        sr = 22050

        # 1. Lo-Fi Warm Chords (8-second soothing chord progression: Fmaj7 -> Em7 -> Dm7 -> Cmaj7)
        if not os.path.exists(self.tracks["Lo-Fi Warm Chords"]):
            chords = [
                [174.61, 220.00, 261.63, 329.63],  # Fmaj7
                [164.81, 196.00, 246.94, 293.66],  # Em7
                [146.83, 174.61, 220.00, 261.63],  # Dm7
                [130.81, 164.81, 196.00, 246.94],  # Cmaj7
            ]
            samples = []
            chord_len = sr * 2
            for freqs in chords:
                for i in range(chord_len):
                    t = i / sr
                    env = math.sin(math.pi * (i / chord_len)) ** 0.4
                    val = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
                    samples.append(int(val * env * 5200))
            self._write_wav(self.tracks["Lo-Fi Warm Chords"], samples, sr)

        # 2. Soft Rain Ambience (6-second low-pass smoothed rain noise)
        if not os.path.exists(self.tracks["Soft Rain Ambience"]):
            samples = []
            prev = 0.0
            total = sr * 6
            rng = random.Random(42)
            for i in range(total):
                white = rng.uniform(-1.0, 1.0)
                prev = 0.88 * prev + 0.12 * white
                # Gentle crossfade at loop boundaries
                fade = 1.0
                if i < 2000:
                    fade = i / 2000.0
                elif i > total - 2000:
                    fade = (total - i) / 2000.0
                samples.append(int(prev * fade * 9500))
            self._write_wav(self.tracks["Soft Rain Ambience"], samples, sr)

        # 3. 432Hz Alpha Focus Wave (6-second harmonic drone)
        if not os.path.exists(self.tracks["432Hz Alpha Focus"]):
            samples = []
            total = sr * 6
            for i in range(total):
                t = i / sr
                wave_val = 0.6 * math.sin(2 * math.pi * 216.0 * t) + 0.4 * math.sin(2 * math.pi * 432.0 * t)
                pulse = 0.85 + 0.15 * math.sin(2 * math.pi * 0.5 * t)
                samples.append(int(wave_val * pulse * 4800))
            self._write_wav(self.tracks["432Hz Alpha Focus"], samples, sr)

        # 4. Study Reminder & Session Complete Alarm Chime (C5 - E5 - G5 - C6 ascending bell)
        if not os.path.exists(self.alarm_path):
            notes = [523.25, 659.25, 783.99, 1046.50]
            samples = []
            note_len = int(sr * 0.28)
            for idx, freq in enumerate(notes):
                dur = note_len * 2 if idx == len(notes) - 1 else note_len
                for i in range(dur):
                    t = i / sr
                    decay = math.exp(-4.5 * t)
                    tone = 0.75 * math.sin(2 * math.pi * freq * t) + 0.25 * math.sin(2 * math.pi * (freq * 2) * t)
                    samples.append(int(tone * decay * 15000))
            self._write_wav(self.alarm_path, samples, sr)

    def start_music(self, track_name=None):
        if track_name:
            self.current_track = track_name
        filepath = self.tracks.get(self.current_track)
        if not filepath or not os.path.exists(filepath):
            return
        self.is_playing = True
        if HAS_WINSOUND:
            try:
                winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
            except Exception:
                pass

    def stop_music(self):
        self.is_playing = False
        if HAS_WINSOUND:
            try:
                winsound.PlaySound(None, 0)
            except Exception:
                pass

    def play_alarm(self, root_widget=None):
        """Plays alarm chime clearly and resumes background music afterward if it was active."""
        was_playing = self.is_playing
        if HAS_WINSOUND and os.path.exists(self.alarm_path):
            try:
                winsound.PlaySound(self.alarm_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                if was_playing and root_widget is not None:
                    root_widget.after(1800, lambda: self.start_music(self.current_track) if self.is_playing else None)
                return
            except Exception:
                pass
        if root_widget is not None:
            try:
                root_widget.bell()
            except Exception:
                pass


class CSVStorageManager:
    """Manages persistent application data using structured CSV files."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

        self.schemas = {
            "users": ["user_id", "username", "password_hash", "created_at"],
            "tasks": ["task_id", "user_id", "task_name", "is_urgent", "is_important", "label", "is_completed"],
            "sessions": ["session_id", "user_id", "task_name", "duration_minutes", "session_date", "start_hour", "status", "distractions_count"],
            "distractions": ["distraction_id", "user_id", "distraction_text", "logged_time"],
            "study_schedules": ["schedule_id", "user_id", "study_date", "study_time", "task_name", "status"],
            "friends": ["friend_id", "user_id", "friend_name", "status"]
        }

        for table, headers in self.schemas.items():
            path = self._get_path(table)
            if not os.path.exists(path):
                self.write_all(table, [])

    def _get_path(self, table):
        return os.path.join(self.data_dir, f"{table}.csv")

    def read_all(self, table):
        path = self._get_path(table)
        if not os.path.exists(path):
            return []
        with open(path, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def write_all(self, table, rows):
        path = self._get_path(table)
        headers = self.schemas[table]
        with open(path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    def get_next_id(self, table, id_field):
        rows = self.read_all(table)
        if not rows:
            return 1
        return max(int(r[id_field]) for r in rows) + 1

    def insert_row(self, table, row_dict):
        rows = self.read_all(table)
        rows.append(row_dict)
        self.write_all(table, rows)


class FocusFlowProApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FocusFlow Pro - Anti-Procrastination & Study Tracker")
        self.root.geometry("860x660")
        self.root.minsize(780, 600)

        # Hide main window until login succeeds
        self.root.withdraw()

        # Portable Base Directory, Audio Engine, and CSV Storage
        self.base_dir = get_writable_base_dir()
        self.audio = BuiltInAudioEngine(self.base_dir)
        self.db = CSVStorageManager(os.path.join(self.base_dir, "data"))
        self.insert_sample_data()

        # User Session State
        self.current_user_id = None
        self.current_username = None

        # Pomodoro Timer Variables
        self.work_time = 25 * 60
        self.short_break = 5 * 60
        self.long_break = 15 * 60

        self.time_left = self.work_time
        self.is_running = False
        self.is_focus_locked = False
        self.timer_id = None
        self.current_mode = "Work"
        self.completed_sessions_today = 0
        self.tab_switch_count = 0

        # Cozy Theme Colors
        self.bg_main = "#E8F5E9"
        self.bg_card = "#FFFFFF"
        self.text_dark = "#2E3B2E"
        self.border_color = "#C8E6C9"

        self.quotes = [
            "“Discipline is the bridge between goals and accomplishment.”",
            "“A journey of a thousand miles begins with a single step.”",
            "“Focus for 25 minutes today, reap success tomorrow.”",
            "“Persistence creates excellence.”",
            "“Don't limit your challenges. Challenge your limits!”"
        ]

        self.root.protocol("WM_DELETE_WINDOW", self.on_main_close)
        self.show_login_window()

    def center_window(self, win, width, height):
        win.update_idletasks()
        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()
        x = max(0, (screen_w - width) // 2)
        y = max(0, (screen_h - height) // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

    def hash_password(self, password):
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def extract_clean_task_name(self, raw_text):
        text = raw_text.strip()
        if "]" in text:
            text = text.rsplit("]", 1)[-1].strip()
        return text

    def insert_sample_data(self):
        users = self.db.read_all("users")
        if len(users) == 0:
            sample_uid = "1"
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.db.insert_row("users", {
                "user_id": sample_uid,
                "username": "student",
                "password_hash": self.hash_password("123456"),
                "created_at": now_str
            })

            sample_tasks = [
                ("1", "Python Final Project Report", "1", "1", "#Python", "0"),
                ("2", "HSK 2 Chinese Exam Prep", "0", "1", "#Chinese", "0"),
                ("3", "Cisco Packet Tracer Lab", "1", "0", "#Networking", "0"),
                ("4", "Oracle Database SQL Practice", "0", "0", "#Database", "1")
            ]
            for tid, tname, urg, imp, lbl, comp in sample_tasks:
                self.db.insert_row("tasks", {
                    "task_id": tid,
                    "user_id": sample_uid,
                    "task_name": tname,
                    "is_urgent": urg,
                    "is_important": imp,
                    "label": lbl,
                    "is_completed": comp
                })

            base_date = datetime.now()
            sid = 1
            for i in range(7):
                date_str = (base_date - timedelta(days=i)).strftime("%Y-%m-%d")
                for _ in range(random.randint(2, 4)):
                    t_name = random.choice([t[1] for t in sample_tasks])
                    status = "Completed" if random.random() > 0.15 else "Failed (Tab Switch)"
                    self.db.insert_row("sessions", {
                        "session_id": str(sid),
                        "user_id": sample_uid,
                        "task_name": t_name,
                        "duration_minutes": "25",
                        "session_date": date_str,
                        "start_hour": str(random.choice([8, 14, 20, 21])),
                        "status": status,
                        "distractions_count": str(random.randint(0, 2))
                    })
                    sid += 1

            sample_distractions = [
                ("1", "Check online shopping deals", (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M:%S")),
                ("2", "Reply to unread messages", (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"))
            ]
            for did, text, t_str in sample_distractions:
                self.db.insert_row("distractions", {
                    "distraction_id": did,
                    "user_id": sample_uid,
                    "distraction_text": text,
                    "logged_time": t_str
                })

            sample_schedules = [
                ("1", base_date.strftime("%Y-%m-%d"), "20:00", "Python Final Project Report", "Pending"),
                ("2", (base_date + timedelta(days=1)).strftime("%Y-%m-%d"), "09:00", "HSK 2 Chinese Exam Prep", "Pending")
            ]
            for scid, sdate, stime, stask, sstat in sample_schedules:
                self.db.insert_row("study_schedules", {
                    "schedule_id": scid,
                    "user_id": sample_uid,
                    "study_date": sdate,
                    "study_time": stime,
                    "task_name": stask,
                    "status": sstat
                })

            sample_friends = [
                ("1", "Alex Johnson (CS Dept)", "Studying Python"),
                ("2", "Sarah Lee", "5-min Break")
            ]
            for fid, fname, fstat in sample_friends:
                self.db.insert_row("friends", {
                    "friend_id": fid,
                    "user_id": sample_uid,
                    "friend_name": fname,
                    "status": fstat
                })

    def on_main_close(self):
        if self.is_focus_locked:
            messagebox.showwarning("Focus Mode Locked", "Please click 'Stop' or 'Take Break' before closing the application.", parent=self.root)
            return
        self.audio.stop_music()
        self.root.destroy()

    # --- LOGIN & REGISTRATION ---
    def show_login_window(self):
        self.login_win = tk.Toplevel(self.root)
        self.login_win.title("FocusFlow Pro - User Login")
        self.center_window(self.login_win, 390, 320)
        self.login_win.config(bg=self.bg_main)
        self.login_win.protocol("WM_DELETE_WINDOW", self.root.destroy)

        tk.Label(self.login_win, text="FOCUSFLOW PRO", font=("Helvetica", 18, "bold"), fg="#2E7D32", bg=self.bg_main).pack(pady=15)
        tk.Label(self.login_win, text="Sign in to access your CSV study workspace", font=("Helvetica", 9), fg=self.text_dark, bg=self.bg_main).pack()

        form_frame = tk.Frame(self.login_win, bg=self.bg_card, highlightbackground=self.border_color, highlightthickness=1, padx=20, pady=15)
        form_frame.pack(pady=12)

        tk.Label(form_frame, text="Username:", bg=self.bg_card, font=("Helvetica", 10)).grid(row=0, column=0, sticky="w", pady=5)
        self.ent_username = tk.Entry(form_frame, width=20, font=("Helvetica", 10))
        self.ent_username.insert(0, "student")
        self.ent_username.grid(row=0, column=1, pady=5)

        tk.Label(form_frame, text="Password:", bg=self.bg_card, font=("Helvetica", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.ent_password = tk.Entry(form_frame, width=20, show="*", font=("Helvetica", 10))
        self.ent_password.insert(0, "123456")
        self.ent_password.grid(row=1, column=1, pady=5)

        btn_box = tk.Frame(self.login_win, bg=self.bg_main)
        btn_box.pack(pady=5)

        tk.Button(btn_box, text="🔑 Login", command=self.handle_login, bg="#81C784", fg="white", font=("Helvetica", 9, "bold"), padx=12, pady=4).grid(row=0, column=0, padx=5)
        tk.Button(btn_box, text="📝 Register", command=self.handle_register, bg="#4FC3F7", fg="white", font=("Helvetica", 9, "bold"), padx=12, pady=4).grid(row=0, column=1, padx=5)

    def handle_login(self):
        uname = self.ent_username.get().strip()
        pwd = self.ent_password.get().strip()

        if not uname or not pwd:
            messagebox.showwarning("Warning", "Please enter both username and password!", parent=self.login_win)
            return

        pwd_hash = self.hash_password(pwd)
        users = self.db.read_all("users")
        matched_user = next((u for u in users if u["username"] == uname and u["password_hash"] == pwd_hash), None)

        if matched_user:
            self.current_user_id = matched_user["user_id"]
            self.current_username = uname
            self.login_win.destroy()

            self.root.deiconify()
            self.center_window(self.root, 860, 660)
            self.setup_ui()
            self.load_tasks_by_eisenhower()
            self.bind_window_events()
            self.check_scheduled_reminders()
        else:
            messagebox.showerror("Error", "Invalid username or password!", parent=self.login_win)

    def handle_register(self):
        uname = self.ent_username.get().strip()
        pwd = self.ent_password.get().strip()

        if not uname or not pwd:
            messagebox.showwarning("Warning", "Please fill in all registration fields!", parent=self.login_win)
            return

        users = self.db.read_all("users")
        if any(u["username"] == uname for u in users):
            messagebox.showerror("Error", "Username already exists. Please choose another!", parent=self.login_win)
            return

        new_id = str(self.db.get_next_id("users", "user_id"))
        self.db.insert_row("users", {
            "user_id": new_id,
            "username": uname,
            "password_hash": self.hash_password(pwd),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        messagebox.showinfo("Success", "Account created successfully! You can now log in.", parent=self.login_win)

    def logout(self):
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?", parent=self.root):
            self.stop_timer_internal()
            self.audio.stop_music()
            self.exit_focus_lock_mode()
            self.current_user_id = None
            self.current_username = None
            self.root.withdraw()
            self.show_login_window()

    # --- CLOUD SYNC (EXPORT / IMPORT BACKUP) ---
    def export_cloud_sync_data(self):
        uid = self.current_user_id
        sync_payload = {
            "version": "v12_portable",
            "username": self.current_username,
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tasks": [r for r in self.db.read_all("tasks") if r["user_id"] == uid],
            "sessions": [r for r in self.db.read_all("sessions") if r["user_id"] == uid],
            "distractions": [r for r in self.db.read_all("distractions") if r["user_id"] == uid],
            "schedules": [r for r in self.db.read_all("study_schedules") if r["user_id"] == uid]
        }

        filename = filedialog.asksaveasfilename(
            title="Export Cloud Sync File",
            defaultextension=".focusflow_cloud",
            filetypes=[("FocusFlow Cloud Backup", "*.focusflow_cloud"), ("JSON Files", "*.json")],
            initialfile=f"{self.current_username}_backup.focusflow_cloud"
        )

        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(sync_payload, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Success", f"Backup exported for '{self.current_username}'.", parent=self.root)

    def import_cloud_sync_data(self):
        filename = filedialog.askopenfilename(
            title="Select Cloud Sync File to Import",
            filetypes=[("FocusFlow Cloud Backup", "*.focusflow_cloud"), ("JSON Files", "*.json")]
        )

        if filename:
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    payload = json.load(f)

                uid = self.current_user_id
                existing_tasks = self.db.read_all("tasks")
                existing_names = {t["task_name"] for t in existing_tasks if t["user_id"] == uid}

                for t in payload.get("tasks", []):
                    if t["task_name"] not in existing_names:
                        self.db.insert_row("tasks", {
                            "task_id": str(self.db.get_next_id("tasks", "task_id")),
                            "user_id": uid,
                            "task_name": t["task_name"],
                            "is_urgent": t.get("is_urgent", "0"),
                            "is_important": t.get("is_important", "0"),
                            "label": t.get("label", "#General"),
                            "is_completed": t.get("is_completed", "0")
                        })

                for s in payload.get("sessions", []):
                    self.db.insert_row("sessions", {
                        "session_id": str(self.db.get_next_id("sessions", "session_id")),
                        "user_id": uid,
                        "task_name": s["task_name"],
                        "duration_minutes": s["duration_minutes"],
                        "session_date": s["session_date"],
                        "start_hour": s["start_hour"],
                        "status": s["status"],
                        "distractions_count": s.get("distractions_count", "0")
                    })

                for d in payload.get("distractions", []):
                    self.db.insert_row("distractions", {
                        "distraction_id": str(self.db.get_next_id("distractions", "distraction_id")),
                        "user_id": uid,
                        "distraction_text": d["distraction_text"],
                        "logged_time": d["logged_time"]
                    })

                for sc in payload.get("schedules", []):
                    self.db.insert_row("study_schedules", {
                        "schedule_id": str(self.db.get_next_id("study_schedules", "schedule_id")),
                        "user_id": uid,
                        "study_date": sc["study_date"],
                        "study_time": sc["study_time"],
                        "task_name": sc["task_name"],
                        "status": sc.get("status", "Pending")
                    })

                self.load_tasks_by_eisenhower()
                messagebox.showinfo("Success", f"Data restored successfully for '{self.current_username}'!", parent=self.root)
            except Exception as e:
                messagebox.showerror("Import Error", f"Invalid backup file: {str(e)}", parent=self.root)

    def open_sync_window(self):
        win = tk.Toplevel(self.root)
        win.title("☁️ Cloud Sync & CSV Backup")
        self.center_window(win, 400, 200)
        win.config(bg=self.bg_main)

        tk.Label(win, text="CROSS-DEVICE CLOUD SYNC", font=("Helvetica", 11, "bold"), fg="#0d47a1", bg=self.bg_main).pack(pady=10)
        tk.Label(win, text=f"Active Account: {self.current_username}", font=("Helvetica", 9, "italic"), bg=self.bg_main).pack(pady=2)

        btn_frame = tk.Frame(win, bg=self.bg_main)
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="📤 Export Backup File", command=self.export_cloud_sync_data, bg="#e1f5fe", width=25).pack(pady=4)
        tk.Button(btn_frame, text="📥 Import Backup File", command=self.import_cloud_sync_data, bg="#c8e6c9", width=25).pack(pady=4)

    # --- ANTI-PROCRASTINATION ALT-TAB GUARD ---
    def bind_window_events(self):
        self.root.bind("<FocusOut>", self.on_window_deactivate)

    def on_window_deactivate(self, event):
        if event.widget == self.root and self.is_running and self.current_mode == "Work":
            self.tab_switch_count += 1
            warn_msg = f"⚠️ Distraction Warning (Alt-Tab): {self.tab_switch_count}/3"
            self.lbl_warning.config(text=warn_msg, fg="red")
            if self.is_focus_locked and hasattr(self, "lock_warning_label") and self.lock_warning_label.winfo_exists():
                self.lock_warning_label.config(text=warn_msg, fg="#FF5252")

            if self.tab_switch_count >= 3:
                self.stop_timer_internal()
                self.exit_focus_lock_mode()
                self.audio.play_alarm(self.root)
                messagebox.showerror(
                    "Session Canceled!",
                    "You switched away from the app 3 times during focus mode.\nThis Pomodoro session is marked as FAILED!",
                    parent=self.root
                )
                self.save_session(status="Failed (Alt-Tab Limit)")
                self.reset_timer_display()

    # --- FULLSCREEN FOCUS LOCK MODE ---
    def enter_focus_lock_mode(self, active_task):
        """Expands window to fullscreen and locks all functions except Take Break and Stop."""
        self.is_focus_locked = True
        self.top_bar.pack_forget()
        self.main_pane.pack_forget()

        self.root.attributes("-fullscreen", True)

        self.lock_frame = tk.Frame(self.root, bg="#1B262C")
        self.lock_frame.pack(fill="both", expand=True)

        center_box = tk.Frame(self.lock_frame, bg="#1B262C")
        center_box.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            center_box,
            text="🔒 STRICT FOCUS LOCK MODE",
            font=("Helvetica", 16, "bold"),
            fg="#81C784",
            bg="#1B262C"
        ).pack(pady=(0, 10))

        tk.Label(
            center_box,
            text=f"Current Task: {active_task}",
            font=("Helvetica", 14),
            fg="#ECEFF1",
            bg="#1B262C"
        ).pack(pady=(0, 20))

        mins, secs = divmod(self.time_left, 60)
        self.lock_timer_label = tk.Label(
            center_box,
            text=f"{mins:02d}:{secs:02d}",
            font=("Helvetica", 88, "bold"),
            fg="#FFFFFF",
            bg="#1B262C"
        )
        self.lock_timer_label.pack(pady=10)

        self.lock_quote_label = tk.Label(
            center_box,
            text=self.lbl_quote.cget("text"),
            font=("Helvetica", 12, "italic"),
            fg="#B0BEC5",
            bg="#1B262C",
            wraplength=650
        )
        self.lock_quote_label.pack(pady=(10, 15))

        self.lock_warning_label = tk.Label(
            center_box,
            text="🛡️ All other features are locked until you take a break or stop.",
            font=("Helvetica", 11, "bold"),
            fg="#4FC3F7",
            bg="#1B262C"
        )
        self.lock_warning_label.pack(pady=(0, 30))

        # ONLY TWO ALLOWED CONTROLS: Take Break and Stop
        lock_btn_frame = tk.Frame(center_box, bg="#1B262C")
        lock_btn_frame.pack()

        tk.Button(
            lock_btn_frame,
            text="☕ Take Break",
            command=self.start_break,
            width=16,
            height=2,
            bg="#FFB74D",
            fg="white",
            font=("Helvetica", 12, "bold"),
            cursor="hand2"
        ).grid(row=0, column=0, padx=15)

        tk.Button(
            lock_btn_frame,
            text="⏹ Stop",
            command=self.stop_timer_click,
            width=16,
            height=2,
            bg="#E57373",
            fg="white",
            font=("Helvetica", 12, "bold"),
            cursor="hand2"
        ).grid(row=0, column=1, padx=15)

    def exit_focus_lock_mode(self):
        if not self.is_focus_locked:
            return
        self.is_focus_locked = False
        self.root.attributes("-fullscreen", False)
        if hasattr(self, "lock_frame") and self.lock_frame.winfo_exists():
            self.lock_frame.destroy()
        self.top_bar.pack(fill="x", padx=0, pady=0)
        self.main_pane.pack(fill="both", expand=True, padx=10, pady=8)

    # --- MAIN DASHBOARD UI ---
    def setup_ui(self):
        self.root.config(bg=self.bg_main)
        for widget in self.root.winfo_children():
            widget.destroy()

        # 1. Header Toolbar (Username without level + Built-in Audio Track Selector)
        self.top_bar = tk.Frame(self.root, bg="#eceff1")
        self.top_bar.pack(fill="x", padx=0, pady=0)

        tk.Label(self.top_bar, text=f"👤 {self.current_username}", font=("Helvetica", 10, "bold"), bg="#eceff1", fg="#2E7D32").pack(side="left", padx=10, pady=5)
        tk.Button(self.top_bar, text="☁️ Cloud Sync", command=self.open_sync_window, bg="#bbdefb", font=("Helvetica", 8, "bold")).pack(side="left", padx=3)
        tk.Button(self.top_bar, text="🎨 Theme", command=self.change_bg_color, bg="#ffffff", font=("Helvetica", 8)).pack(side="left", padx=2)

        # Built-in Audio Track Selector & Toggle
        self.track_combo = ttk.Combobox(self.top_bar, values=list(self.audio.tracks.keys()), width=17, state="readonly", font=("Helvetica", 8))
        self.track_combo.set(self.audio.current_track)
        self.track_combo.bind("<<ComboboxSelected>>", self.on_track_changed)
        self.track_combo.pack(side="left", padx=(6, 2))

        self.btn_music = tk.Button(self.top_bar, text="🎵 Audio: OFF", command=self.toggle_music, bg="#ffffff", font=("Helvetica", 8))
        self.btn_music.pack(side="left", padx=2)

        tk.Button(self.top_bar, text="🚪 Logout", command=self.logout, bg="#ffcdd2", font=("Helvetica", 8, "bold")).pack(side="right", padx=10)
        tk.Button(self.top_bar, text="👥 Buddies", command=self.show_friends_window, bg="#e1f5fe", font=("Helvetica", 8)).pack(side="right", padx=2)

        # 2. Main Split Container
        self.main_pane = tk.Frame(self.root, bg=self.bg_main)
        self.main_pane.pack(fill="both", expand=True, padx=10, pady=8)

        # LEFT COLUMN
        left_col = tk.Frame(self.main_pane, bg=self.bg_main, width=350)
        left_col.pack(side="left", fill="both", expand=False, padx=(0, 8))

        # Timer Card
        timer_card = tk.Frame(left_col, bg=self.bg_card, highlightbackground=self.border_color, highlightthickness=1, padx=12, pady=10)
        timer_card.pack(fill="x", pady=(0, 8))

        self.fatigue_label = tk.Label(timer_card, text="🎯 Fatigue Index: Normal (0%)", font=("Helvetica", 9, "bold"), fg="#2E7D32", bg=self.bg_card)
        self.fatigue_label.pack(pady=(0, 2))

        self.timer_label = tk.Label(timer_card, text="25:00", font=("Helvetica", 42, "bold"), fg="#2E3B2E", bg=self.bg_card)
        self.timer_label.pack(pady=2)

        self.lbl_quote = tk.Label(timer_card, text=random.choice(self.quotes), font=("Helvetica", 8, "italic"), fg="#555", bg=self.bg_card, wraplength=280)
        self.lbl_quote.pack(pady=2)

        self.mode_label = tk.Label(timer_card, text="Status: Ready", font=("Helvetica", 9, "bold"), fg="#3F51B5", bg=self.bg_card)
        self.mode_label.pack(pady=1)

        self.lbl_warning = tk.Label(timer_card, text="", font=("Helvetica", 8, "bold"), bg=self.bg_card)
        self.lbl_warning.pack()

        btn_frame = tk.Frame(timer_card, bg=self.bg_card)
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="▶ Start Focus", command=self.start_work, width=10, bg="#81C784", fg="white", font=("Helvetica", 8, "bold")).grid(row=0, column=0, padx=2)
        tk.Button(btn_frame, text="☕ Take Break", command=self.start_break, width=10, bg="#FFB74D", fg="white", font=("Helvetica", 8, "bold")).grid(row=0, column=1, padx=2)
        tk.Button(btn_frame, text="⏹ Stop", command=self.stop_timer_click, width=8, bg="#E57373", fg="white", font=("Helvetica", 8, "bold")).grid(row=0, column=2, padx=2)

        # Daily Study Scheduler Card
        sched_card = tk.Frame(left_col, bg=self.bg_card, highlightbackground=self.border_color, highlightthickness=1, padx=12, pady=8)
        sched_card.pack(fill="x", pady=(0, 8))

        tk.Label(sched_card, text="🗓️ Daily Study Scheduler (With Alarm)", font=("Helvetica", 9, "bold"), bg=self.bg_card, fg=self.text_dark).pack(anchor="w", pady=(0, 3))

        row_dt = tk.Frame(sched_card, bg=self.bg_card)
        row_dt.pack(fill="x")
        tk.Label(row_dt, text="Date:", bg=self.bg_card, font=("Helvetica", 8)).pack(side="left")
        self.ent_sched_date = tk.Entry(row_dt, width=10, font=("Helvetica", 8))
        self.ent_sched_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.ent_sched_date.pack(side="left", padx=2)

        tk.Label(row_dt, text="Time:", bg=self.bg_card, font=("Helvetica", 8)).pack(side="left", padx=2)
        self.spin_hour = ttk.Spinbox(row_dt, from_=0, to=23, width=3, format="%02.0f")
        self.spin_hour.set("20")
        self.spin_hour.pack(side="left")

        tk.Label(row_dt, text=":", bg=self.bg_card).pack(side="left")
        self.spin_min = ttk.Spinbox(row_dt, from_=0, to=59, width=3, format="%02.0f")
        self.spin_min.set("00")
        self.spin_min.pack(side="left")

        row_btn = tk.Frame(sched_card, bg=self.bg_card)
        row_btn.pack(fill="x", pady=4)
        tk.Button(row_btn, text="+ Add Schedule", command=self.add_study_schedule, bg="#81C784", fg="white", font=("Helvetica", 8, "bold")).pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(row_btn, text="📋 View List", command=self.show_schedules_window, bg="#e1f5fe", font=("Helvetica", 8)).pack(side="left", padx=2, expand=True, fill="x")
        tk.Button(row_btn, text="🔔 Test Alarm", command=lambda: self.audio.play_alarm(self.root), bg="#FFF9C4", font=("Helvetica", 8)).pack(side="left", padx=2)

        # Brain Dump Card
        bd_card = tk.Frame(left_col, bg=self.bg_card, highlightbackground=self.border_color, highlightthickness=1, padx=12, pady=8)
        bd_card.pack(fill="x")

        tk.Label(bd_card, text="🧠 Brain Dump (Distractions)", font=("Helvetica", 9, "bold"), bg=self.bg_card, fg=self.text_dark).pack(anchor="w", pady=(0, 3))
        bd_row = tk.Frame(bd_card, bg=self.bg_card)
        bd_row.pack(fill="x")
        self.distraction_entry = tk.Entry(bd_row, width=28, font=("Helvetica", 8))
        self.distraction_entry.pack(side="left", padx=(0, 4))
        tk.Button(bd_row, text="Log", command=self.log_distraction, bg="#80DEEA", font=("Helvetica", 8, "bold")).pack(side="left", fill="x", expand=True)

        # RIGHT COLUMN
        right_col = tk.Frame(self.main_pane, bg=self.bg_main)
        right_col.pack(side="right", fill="both", expand=True)

        task_card = tk.Frame(right_col, bg=self.bg_card, highlightbackground=self.border_color, highlightthickness=1, padx=12, pady=10)
        task_card.pack(fill="both", expand=True, pady=(0, 8))

        tk.Label(task_card, text="📌 Task & Priority Management", font=("Helvetica", 11, "bold"), fg=self.text_dark, bg=self.bg_card).pack(anchor="w", pady=(0, 4))

        # Search Row
        search_row = tk.Frame(task_card, bg=self.bg_card)
        search_row.pack(fill="x", pady=2)
        tk.Label(search_row, text="🔍 Search:", bg=self.bg_card, font=("Helvetica", 8)).pack(side="left")
        self.ent_search = tk.Entry(search_row, width=16, font=("Helvetica", 8))
        self.ent_search.pack(side="left", padx=2)
        tk.Button(search_row, text="Find", command=self.search_tasks, bg="#E0E0E0", font=("Helvetica", 8)).pack(side="left", padx=1)
        tk.Button(search_row, text="Reset", command=self.load_tasks_by_eisenhower, bg="#E0E0E0", font=("Helvetica", 8)).pack(side="left", padx=1)

        # Entry Row
        entry_row = tk.Frame(task_card, bg=self.bg_card)
        entry_row.pack(fill="x", pady=2)
        tk.Label(entry_row, text="Task:", bg=self.bg_card, font=("Helvetica", 8)).pack(side="left")
        self.task_entry = ttk.Combobox(entry_row, width=32, font=("Helvetica", 8))
        self.task_entry.pack(side="left", padx=2, fill="x", expand=True)

        # Tag & Urgency Checkboxes
        tag_row = tk.Frame(task_card, bg=self.bg_card)
        tag_row.pack(fill="x", pady=2)
        tk.Label(tag_row, text="Tag:", bg=self.bg_card, font=("Helvetica", 8)).pack(side="left")
        self.ent_label = tk.Entry(tag_row, width=10, font=("Helvetica", 8))
        self.ent_label.insert(0, "#General")
        self.ent_label.pack(side="left", padx=2)

        self.var_urgent = tk.IntVar()
        self.var_important = tk.IntVar()
        tk.Checkbutton(tag_row, text="Urgent", variable=self.var_urgent, bg=self.bg_card, font=("Helvetica", 8)).pack(side="left")
        tk.Checkbutton(tag_row, text="Important", variable=self.var_important, bg=self.bg_card, font=("Helvetica", 8)).pack(side="left")

        # Action Buttons
        btn_action_row = tk.Frame(task_card, bg=self.bg_card)
        btn_action_row.pack(fill="x", pady=3)
        tk.Button(btn_action_row, text="+ Add Task", command=self.add_eisenhower_task, bg="#81C784", fg="white", font=("Helvetica", 8, "bold")).pack(side="left", expand=True, fill="x", padx=2)
        tk.Button(btn_action_row, text="✔ Mark Complete", command=self.mark_task_completed, bg="#80DEEA", font=("Helvetica", 8, "bold")).pack(side="left", expand=True, fill="x", padx=2)

        # Live Task Table
        tk.Label(task_card, text="Active Task List (Stored in data/tasks.csv):", font=("Helvetica", 9, "bold"), bg=self.bg_card, fg="#555").pack(anchor="w", pady=(6, 2))

        self.task_tree = ttk.Treeview(task_card, columns=("tag", "priority", "name"), show="headings", height=8)
        self.task_tree.heading("tag", text="Tag")
        self.task_tree.heading("priority", text="Priority")
        self.task_tree.heading("name", text="Task Name")
        self.task_tree.column("tag", width=80)
        self.task_tree.column("priority", width=90)
        self.task_tree.column("name", width=180)
        self.task_tree.pack(fill="both", expand=True, pady=2)

        # Bottom Analytics & Exporter Buttons
        tk.Button(right_col, text="📊 Analytics & Distraction Logs", command=self.show_analytics, bg="#bbdefb", font=("Helvetica", 8, "bold")).pack(fill="x", pady=1)
        tk.Button(right_col, text="🤖 AI Study Plan & Fatigue Suggestion", command=self.suggest_plan, bg="#FFFDD0", font=("Helvetica", 8, "bold")).pack(fill="x", pady=1)
        tk.Button(right_col, text="📄 Export Word Report (.doc)", command=self.export_word_report, bg="#B2DFDB", font=("Helvetica", 8, "bold")).pack(fill="x", pady=1)

    def change_bg_color(self):
        color = colorchooser.askcolor(title="Select Background Color")[1]
        if color:
            self.bg_main = color
            self.root.config(bg=color)
            self.main_pane.config(bg=color)

    def on_track_changed(self, event=None):
        selected = self.track_combo.get()
        self.audio.current_track = selected
        if self.audio.is_playing:
            self.audio.start_music(selected)

    def toggle_music(self):
        if not self.audio.is_playing:
            selected = self.track_combo.get()
            self.audio.start_music(selected)
            self.btn_music.config(text="🎵 Audio: ON", bg="#C8E6C9")
        else:
            self.audio.stop_music()
            self.btn_music.config(text="🎵 Audio: OFF", bg="#ffffff")

    def show_friends_window(self):
        win = tk.Toplevel(self.root)
        win.title("👥 Study Buddies")
        self.center_window(win, 450, 300)
        win.config(bg=self.bg_main)

        tk.Label(win, text="Study Group Members:", font=("Helvetica", 10, "bold"), bg=self.bg_main, fg=self.text_dark).pack(pady=5)

        tree = ttk.Treeview(win, columns=("id", "name", "status"), show="headings", height=6)
        tree.heading("id", text="ID")
        tree.heading("name", text="Member Name")
        tree.heading("status", text="Status")
        tree.column("id", width=40)
        tree.column("name", width=180)
        tree.column("status", width=180)
        tree.pack(padx=10, pady=5, fill="both", expand=True)

        friends = [r for r in self.db.read_all("friends") if r["user_id"] == self.current_user_id]
        for f in friends:
            tree.insert("", "end", values=(f["friend_id"], f["friend_name"], f["status"]))

        add_frame = tk.Frame(win, bg=self.bg_main)
        add_frame.pack(pady=5)
        tk.Label(add_frame, text="New Buddy:", bg=self.bg_main).pack(side="left", padx=2)
        ent_f_name = tk.Entry(add_frame, width=18)
        ent_f_name.pack(side="left", padx=2)

        def add_friend():
            fname = ent_f_name.get().strip()
            if fname:
                fid = str(self.db.get_next_id("friends", "friend_id"))
                self.db.insert_row("friends", {
                    "friend_id": fid,
                    "user_id": self.current_user_id,
                    "friend_name": fname,
                    "status": "Available"
                })
                tree.insert("", "end", values=(fid, fname, "Available"))
                ent_f_name.delete(0, tk.END)

        tk.Button(add_frame, text="+ Add Buddy", command=add_friend, bg="#81C784", fg="white", font=("Helvetica", 8, "bold")).pack(side="left", padx=4)

    def mark_task_completed(self):
        raw_task = self.task_entry.get().strip()
        clean_task = self.extract_clean_task_name(raw_task)
        if not clean_task:
            return

        all_tasks = self.db.read_all("tasks")
        updated = False
        for t in all_tasks:
            if t["user_id"] == self.current_user_id and clean_task.lower() in t["task_name"].lower():
                t["is_completed"] = "1"
                updated = True

        if updated:
            self.db.write_all("tasks", all_tasks)
            self.load_tasks_by_eisenhower()
            messagebox.showinfo("Success", f"Task '{clean_task}' marked as COMPLETED!", parent=self.root)

    def search_tasks(self):
        keyword = self.ent_search.get().strip().lower()
        if not keyword:
            self.load_tasks_by_eisenhower()
            return

        rows = [
            t for t in self.db.read_all("tasks")
            if t["user_id"] == self.current_user_id and (keyword in t["task_name"].lower() or keyword in t["label"].lower())
        ]

        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        formatted_tasks = []
        for t in rows:
            done_tag = "✔ " if t["is_completed"] == "1" else ""
            urg, imp = t["is_urgent"] == "1", t["is_important"] == "1"
            prio_str = "Do First" if (urg and imp) else ("Schedule" if (imp and not urg) else ("Delegate" if (urg and not imp) else "Eliminate"))
            tag_str = f"[{t['label']}]"
            formatted_tasks.append(f"{done_tag}{tag_str} [{prio_str}] {t['task_name']}")
            self.task_tree.insert("", "end", values=(tag_str, prio_str, f"{done_tag}{t['task_name']}"))

        self.task_entry["values"] = formatted_tasks
        if formatted_tasks:
            self.task_entry.current(0)

    def add_eisenhower_task(self):
        raw_name = self.task_entry.get().strip()
        name = self.extract_clean_task_name(raw_name)
        lbl = self.ent_label.get().strip() or "#General"
        if not name:
            messagebox.showwarning("Validation Error", "Please enter a task name!", parent=self.root)
            return

        all_tasks = self.db.read_all("tasks")
        existing = next((t for t in all_tasks if t["user_id"] == self.current_user_id and t["task_name"].lower() == name.lower()), None)

        if existing:
            existing["is_urgent"] = str(self.var_urgent.get())
            existing["is_important"] = str(self.var_important.get())
            existing["label"] = lbl
            existing["is_completed"] = "0"
            self.db.write_all("tasks", all_tasks)
        else:
            self.db.insert_row("tasks", {
                "task_id": str(self.db.get_next_id("tasks", "task_id")),
                "user_id": self.current_user_id,
                "task_name": name,
                "is_urgent": str(self.var_urgent.get()),
                "is_important": str(self.var_important.get()),
                "label": lbl,
                "is_completed": "0"
            })

        self.load_tasks_by_eisenhower()

    def load_tasks_by_eisenhower(self):
        user_tasks = [t for t in self.db.read_all("tasks") if t["user_id"] == self.current_user_id]
        user_tasks.sort(key=lambda t: (int(t["is_completed"]), -int(t["is_important"]), -int(t["is_urgent"])))

        for item in self.task_tree.get_children():
            self.task_tree.delete(item)

        formatted_tasks = []
        for t in user_tasks:
            done_tag = "✔ " if t["is_completed"] == "1" else ""
            urg, imp = t["is_urgent"] == "1", t["is_important"] == "1"
            prio = "Do First" if (urg and imp) else ("Schedule" if (imp and not urg) else ("Delegate" if (urg and not imp) else "Eliminate"))
            tag_str = f"[{t['label']}]"
            formatted_tasks.append(f"{done_tag}{tag_str} [{prio}] {t['task_name']}")
            self.task_tree.insert("", "end", values=(tag_str, prio, f"{done_tag}{t['task_name']}"))

        self.task_entry["values"] = formatted_tasks
        if formatted_tasks:
            self.task_entry.current(0)

    def add_study_schedule(self):
        s_date = self.ent_sched_date.get().strip()
        h, m = f"{int(self.spin_hour.get()):02d}", f"{int(self.spin_min.get()):02d}"
        s_time = f"{h}:{m}"
        clean_task = self.extract_clean_task_name(self.task_entry.get())

        if not s_date or not clean_task:
            messagebox.showwarning("Validation Error", "Please enter a valid date and task!", parent=self.root)
            return

        self.db.insert_row("study_schedules", {
            "schedule_id": str(self.db.get_next_id("study_schedules", "schedule_id")),
            "user_id": self.current_user_id,
            "study_date": s_date,
            "study_time": s_time,
            "task_name": clean_task,
            "status": "Pending"
        })
        messagebox.showinfo("Success", f"Scheduled session for '{clean_task}' at {s_time} on {s_date}!", parent=self.root)

    def show_schedules_window(self):
        win = tk.Toplevel(self.root)
        win.title("Scheduled Study Sessions")
        self.center_window(win, 500, 320)
        win.config(bg=self.bg_main)

        tree = ttk.Treeview(win, columns=("id", "date", "time", "task", "status"), show="headings", height=8)
        tree.heading("id", text="ID")
        tree.heading("date", text="Date")
        tree.heading("time", text="Time")
        tree.heading("task", text="Task Name")
        tree.heading("status", text="Status")
        tree.column("id", width=30)
        tree.column("date", width=90)
        tree.column("time", width=60)
        tree.column("task", width=200)
        tree.column("status", width=80)
        tree.pack(padx=10, pady=5, fill="both", expand=True)

        schedules = [s for s in self.db.read_all("study_schedules") if s["user_id"] == self.current_user_id]
        schedules.sort(key=lambda x: (x["study_date"], x["study_time"]))
        for s in schedules:
            tree.insert("", "end", values=(s["schedule_id"], s["study_date"], s["study_time"], s["task_name"], s["status"]))

        def delete_selected():
            selected = tree.selection()
            if not selected:
                return
            item_id = str(tree.item(selected[0])["values"][0])
            all_scheds = [s for s in self.db.read_all("study_schedules") if s["schedule_id"] != item_id]
            self.db.write_all("study_schedules", all_scheds)
            tree.delete(selected[0])
            messagebox.showinfo("Success", "Schedule entry removed.", parent=win)

        tk.Button(win, text="❌ Delete Selected Entry", command=delete_selected, bg="#FFCDD2", font=("Helvetica", 8, "bold")).pack(pady=4)

    def check_scheduled_reminders(self):
        if self.current_user_id and not self.is_focus_locked:
            now = datetime.now()
            current_date, current_time = now.strftime("%Y-%m-%d"), now.strftime("%H:%M")

            all_scheds = self.db.read_all("study_schedules")
            triggered = False
            for s in all_scheds:
                if (s["user_id"] == self.current_user_id and s["study_date"] == current_date
                        and s["study_time"] == current_time and s["status"] == "Pending"):
                    s["status"] = "Notified"
                    triggered = True
                    self.task_entry.set(s["task_name"])
                    self.audio.play_alarm(self.root)
                    messagebox.showinfo(
                        "⏰ STUDY ALARM!",
                        f"Scheduled session starting now: {s['task_name']}\nTime: {current_time} ({current_date})",
                        parent=self.root
                    )
            if triggered:
                self.db.write_all("study_schedules", all_scheds)

        self.root.after(5000, self.check_scheduled_reminders)

    def log_distraction(self):
        text = self.distraction_entry.get().strip()
        if text:
            self.db.insert_row("distractions", {
                "distraction_id": str(self.db.get_next_id("distractions", "distraction_id")),
                "user_id": self.current_user_id,
                "distraction_text": text,
                "logged_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            self.distraction_entry.delete(0, tk.END)
            messagebox.showinfo("Logged", "Distraction logged to Brain Dump. Stay focused!", parent=self.root)

    # --- TIMER CONTROLS ---
    def update_timer(self):
        if self.is_running and self.time_left > 0:
            mins, secs = divmod(self.time_left, 60)
            time_str = f"{mins:02d}:{secs:02d}"
            self.timer_label.config(text=time_str)
            if self.is_focus_locked and hasattr(self, "lock_timer_label") and self.lock_timer_label.winfo_exists():
                self.lock_timer_label.config(text=time_str)
            self.time_left -= 1
            self.timer_id = self.root.after(1000, self.update_timer)
        elif self.is_running and self.time_left == 0:
            self.is_running = False
            self.audio.play_alarm(self.root)
            if self.current_mode == "Work":
                self.completed_sessions_today += 1
                self.save_session(status="Completed")
                self.exit_focus_lock_mode()
                messagebox.showinfo("Congratulations!", f"You finished Pomodoro session #{self.completed_sessions_today}!", parent=self.root)
                self.check_burnout_risk()
            else:
                messagebox.showinfo("Notice", "Break time is over. Ready to study!", parent=self.root)
            self.reset_timer_display()

    def check_burnout_risk(self):
        fatigue_pct = min(100, self.completed_sessions_today * 20)
        if fatigue_pct < 50:
            self.fatigue_label.config(text=f"🎯 Fatigue Index: Normal ({fatigue_pct}%)", fg="green")
        elif fatigue_pct < 80:
            self.fatigue_label.config(text=f"🧠 Fatigue Index: Moderate ({fatigue_pct}%)", fg="orange")
        else:
            self.fatigue_label.config(text=f"⚠️ Fatigue Warning: Take a Long Break ({fatigue_pct}%)", fg="red")

    def start_work(self):
        raw_task = self.task_entry.get().strip()
        if not raw_task:
            messagebox.showwarning("Validation Error", "Please select or enter a task before starting!", parent=self.root)
            return

        self.stop_timer_internal()
        self.tab_switch_count = 0
        self.lbl_warning.config(text="🛡️ Alt-Tab Guard Active...", fg="#E57373")
        self.lbl_quote.config(text=random.choice(self.quotes))
        self.current_mode = "Work"
        self.mode_label.config(text=f"Studying: {raw_task}")
        self.time_left = self.work_time
        self.is_running = True

        self.enter_focus_lock_mode(raw_task)
        self.update_timer()

    def start_break(self):
        self.stop_timer_internal()
        self.exit_focus_lock_mode()
        self.lbl_warning.config(text="")
        self.current_mode = "Break"
        if self.completed_sessions_today > 0 and self.completed_sessions_today % 4 == 0:
            self.time_left = self.long_break
            self.mode_label.config(text="Mode: LONG BREAK (15m) ☕")
        else:
            self.time_left = self.short_break
            self.mode_label.config(text="Mode: Short Break (5m) 🍵")
        self.is_running = True
        self.update_timer()

    def stop_timer_click(self):
        self.stop_timer_internal()
        self.exit_focus_lock_mode()
        self.reset_timer_display()

    def stop_timer_internal(self):
        self.is_running = False
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

    def reset_timer_display(self):
        self.time_left = self.work_time
        mins, secs = divmod(self.time_left, 60)
        self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
        self.lbl_warning.config(text="")
        self.mode_label.config(text="Status: Ready")
        self.tab_switch_count = 0

    def save_session(self, status="Completed"):
        clean_task = self.extract_clean_task_name(self.task_entry.get())
        now = datetime.now()
        self.db.insert_row("sessions", {
            "session_id": str(self.db.get_next_id("sessions", "session_id")),
            "user_id": self.current_user_id,
            "task_name": clean_task,
            "duration_minutes": "25",
            "session_date": now.strftime("%Y-%m-%d"),
            "start_hour": str(now.hour),
            "status": status,
            "distractions_count": str(self.tab_switch_count)
        })

    # --- ANALYTICS & REPORTS ---
    def suggest_plan(self):
        sessions = [
            s for s in self.db.read_all("sessions")
            if s["user_id"] == self.current_user_id and s["status"] == "Completed"
        ]
        hours = [int(s["start_hour"]) for s in sessions]
        if not hours:
            messagebox.showinfo("AI Study Plan", "Not enough completed session data yet.", parent=self.root)
            return

        morning = sum(1 for h in hours if 5 <= h < 12)
        afternoon = sum(1 for h in hours if 12 <= h < 18)
        evening = sum(1 for h in hours if 18 <= h <= 23)
        best_time = (
            "Morning (5AM-12PM)" if morning >= max(afternoon, evening)
            else ("Afternoon (12PM-6PM)" if afternoon >= evening else "Evening (6PM-11PM)")
        )
        plan_msg = (
            f"📊 HABIT ANALYSIS ({self.current_username}):\n"
            f"- Golden Focus Window: {best_time}.\n"
            f"- Completed Sessions: {len(hours)} Pomodoros.\n\n"
            f"💡 OPTIMAL STRATEGY:\n"
            f"1. Schedule [Do First] tasks during {best_time}.\n"
            f"2. Use Fullscreen Focus Lock Mode for high-priority tasks!"
        )
        messagebox.showinfo("🤖 AI Study Plan Suggestion", plan_msg, parent=self.root)

    def show_analytics(self):
        win = tk.Toplevel(self.root)
        win.title("Analytics & Distraction Logs")
        self.center_window(win, 450, 380)
        win.config(bg=self.bg_main)

        user_sessions = [s for s in self.db.read_all("sessions") if s["user_id"] == self.current_user_id]
        completed = sum(1 for s in user_sessions if s["status"] == "Completed")
        total = len(user_sessions)
        rate = (completed / total * 100) if total > 0 else 0

        tk.Label(win, text=f"📊 Session Success Rate: {rate:.1f}% ({completed}/{total})", font=("Helvetica", 11, "bold"), fg="#2E7D32", bg=self.bg_main).pack(pady=10)
        tk.Label(win, text="Recent Brain Dump Distractions:", font=("Helvetica", 9, "bold"), bg=self.bg_main).pack(anchor="w", padx=15)

        user_distractions = [d for d in self.db.read_all("distractions") if d["user_id"] == self.current_user_id]
        for d in reversed(user_distractions[-5:]):
            tk.Label(win, text=f"• {d['distraction_text']} ({d['logged_time'][11:16]})", fg="#444", bg=self.bg_main).pack(anchor="w", padx=25)

    def export_word_report(self):
        filename = os.path.join(self.base_dir, f"FocusFlow_{self.current_username}_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.doc")
        user_sessions = [s for s in self.db.read_all("sessions") if s["user_id"] == self.current_user_id]
        completed_sessions = [s for s in user_sessions if s["status"] == "Completed"]
        completed = len(completed_sessions)
        total = len(user_sessions)
        rate = (completed / total * 100) if total > 0 else 0

        task_totals = {}
        for s in completed_sessions:
            t = s["task_name"]
            task_totals[t] = task_totals.get(t, 0) + int(s["duration_minutes"])

        doc_html = f"""<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
<head><meta charset='utf-8'><title>FocusFlow Performance Report</title></head>
<body>
    <h1>FOCUSFLOW PRO STUDY PERFORMANCE REPORT</h1>
    <p><b>User Account:</b> {self.current_username}</p>
    <p><b>Data Storage Engine:</b> Structured CSV Files (data/*.csv)</p>
    <p><b>Generated At:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <ul>
        <li><b>Total Sessions Attempted:</b> {total}</li>
        <li><b>Successful Completed Sessions:</b> {completed}</li>
        <li><b>Success Rate:</b> {rate:.1f}%</li>
    </ul>
    <h2>⏱️ Focus Time Breakdown by Task</h2>
    <table border='1' cellpadding='8' style='border-collapse: collapse;'>
        <tr><th>Task Name</th><th>Total Time (Minutes)</th></tr>
"""
        for t_name, mins in task_totals.items():
            doc_html += f"<tr><td>{t_name}</td><td>{mins} mins</td></tr>\n"
        doc_html += "</table></body></html>"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(doc_html)
        messagebox.showinfo("Export Success", f"Word report generated successfully!\nFile: {filename}", parent=self.root)


if __name__ == "__main__":
    root = tk.Tk()
    app = FocusFlowProApp(root)
    root.mainloop()