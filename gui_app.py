import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import cv2
import os
from datetime import datetime

from utils.detector import FaceLandmarkDetector
from utils.ear import eye_aspect_ratio
from utils.alarm import play_alarm, stop_alarm


EAR_THRESHOLD = 0.23
CLOSED_FRAMES = 20
LOG_FILE = "logs/drowsiness_log.txt"


class DrowsinessApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Drowsiness Detection System")
        self.root.geometry("1400x820")
        self.root.minsize(1200, 720)
        self.root.configure(bg="#020617")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.cap = None
        self.detector = None
        self.running = False
        self.closed_count = 0
        self.alarm_triggered = False

        self.setup_ui()

    def setup_ui(self):
        header = tk.Frame(self.root, bg="#020617")
        header.pack(fill="x", padx=20, pady=(15, 8))

        title = tk.Label(
            header,
            text="Drowsiness Detection Dashboard",
            font=("Segoe UI", 28, "bold"),
            fg="white",
            bg="#020617"
        )
        title.pack()

        subtitle = tk.Label(
            header,
            text="AI-based real-time eye monitoring and alert system",
            font=("Segoe UI", 12),
            fg="#94a3b8",
            bg="#020617"
        )
        subtitle.pack(pady=(8, 0))

        body = tk.Frame(self.root, bg="#020617")
        body.pack(fill="both", expand=True, padx=20, pady=15)

        left_panel = tk.Frame(body, bg="#081224")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 12))

        right_panel = tk.Frame(body, bg="#081224", width=340)
        right_panel.pack(side="right", fill="y")
        right_panel.pack_propagate(False)

        camera_frame = tk.Frame(
            left_panel,
            bg="#0b1120",
            highlightbackground="#1e3a8a",
            highlightthickness=2
        )
        camera_frame.pack(fill="both", expand=True, padx=18, pady=(18, 12))

        self.video_label = tk.Label(
            camera_frame,
            text="📷 Camera Feed Will Appear Here",
            font=("Segoe UI", 20, "bold"),
            fg="#38bdf8",
            bg="#020617"
        )
        self.video_label.pack(fill="both", expand=True, padx=12, pady=12)

        button_frame = tk.Frame(left_panel, bg="#081224")
        button_frame.pack(pady=(0, 18))

        self.start_btn = tk.Button(
            button_frame,
            text="▶ Start Detection",
            font=("Segoe UI", 12, "bold"),
            bg="#22c55e",
            fg="white",
            activebackground="#16a34a",
            activeforeground="white",
            bd=0,
            padx=22,
            pady=12,
            cursor="hand2",
            command=self.start_detection
        )
        self.start_btn.pack(side="left", padx=8)

        self.stop_btn = tk.Button(
            button_frame,
            text="⏹ Stop Detection",
            font=("Segoe UI", 12, "bold"),
            bg="#ef4444",
            fg="white",
            activebackground="#dc2626",
            activeforeground="white",
            bd=0,
            padx=22,
            pady=12,
            cursor="hand2",
            state="disabled",
            command=self.stop_detection
        )
        self.stop_btn.pack(side="left", padx=8)

        self.clear_btn = tk.Button(
            button_frame,
            text="🗑 Clear Logs",
            font=("Segoe UI", 12, "bold"),
            bg="#334155",
            fg="white",
            activebackground="#475569",
            activeforeground="white",
            bd=0,
            padx=22,
            pady=12,
            cursor="hand2",
            command=self.clear_logs
        )
        self.clear_btn.pack(side="left", padx=8)

        right_title = tk.Label(
            right_panel,
            text="Live Status",
            font=("Segoe UI", 20, "bold"),
            fg="white",
            bg="#081224"
        )
        right_title.pack(pady=(18, 16))

        self.status_value = self.create_card(right_panel, "System Status", "Stopped", "white")
        self.ear_value = self.create_card(right_panel, "Current EAR", "0.00", "white")
        self.alert_value = self.create_card(right_panel, "Alert State", "NORMAL", "#22c55e")
        self.face_value = self.create_card(right_panel, "Face Status", "Not Detected", "white")

        logs_title = tk.Label(
            right_panel,
            text="Recent Logs",
            font=("Segoe UI", 18, "bold"),
            fg="white",
            bg="#081224"
        )
        logs_title.pack(pady=(18, 10))

        log_container = tk.Frame(
            right_panel,
            bg="#020617",
            highlightbackground="#334155",
            highlightthickness=1
        )
        log_container.pack(fill="both", expand=True, padx=15, pady=(0, 16))

        self.log_box = tk.Text(
            log_container,
            bg="#020617",
            fg="#38bdf8",
            font=("Consolas", 10),
            insertbackground="white",
            wrap="word",
            relief="flat",
            bd=0
        )
        self.log_box.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)

        scrollbar = ttk.Scrollbar(log_container, command=self.log_box.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=10)
        self.log_box.configure(yscrollcommand=scrollbar.set)

    def create_card(self, parent, label_text, value_text, value_color):
        card = tk.Frame(parent, bg="#1e293b")
        card.pack(fill="x", padx=15, pady=8)

        label = tk.Label(
            card,
            text=label_text,
            font=("Segoe UI", 10),
            fg="#94a3b8",
            bg="#1e293b",
            anchor="w"
        )
        label.pack(fill="x", padx=14, pady=(12, 2))

        value = tk.Label(
            card,
            text=value_text,
            font=("Segoe UI", 17, "bold"),
            fg=value_color,
            bg="#1e293b",
            anchor="w"
        )
        value.pack(fill="x", padx=14, pady=(0, 12))

        return value

    def log_event(self, message):
        os.makedirs("logs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {message}"

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

        self.log_box.insert("end", entry + "\n")
        self.log_box.see("end")

    def clear_logs(self):
        self.log_box.delete("1.0", "end")
        os.makedirs("logs", exist_ok=True)
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")

    def draw_eye(self, frame, eye_points):
        for point in eye_points:
            cv2.circle(frame, point, 2, (0, 255, 255), -1)

    def start_detection(self):
        if self.running:
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Could not open webcam.")
            return

        self.detector = FaceLandmarkDetector()
        self.running = True
        self.closed_count = 0
        self.alarm_triggered = False

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_value.config(text="Monitoring", fg="#38bdf8")
        self.alert_value.config(text="NORMAL", fg="#22c55e")
        self.face_value.config(text="Waiting...", fg="white")
        self.log_event("Detection started")

        self.update_frame()

    def stop_detection(self):
        self.running = False
        stop_alarm()

        if self.cap is not None:
            self.cap.release()
            self.cap = None

        if self.detector is not None:
            self.detector.close()
            self.detector = None

        self.video_label.configure(image="", text="📷 Camera Feed Stopped")
        self.video_label.imgtk = None

        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_value.config(text="Stopped", fg="white")
        self.ear_value.config(text="0.00", fg="white")
        self.alert_value.config(text="NORMAL", fg="#22c55e")
        self.face_value.config(text="Not Detected", fg="white")
        self.log_event("Detection stopped")

    def update_frame(self):
        if not self.running or self.cap is None or self.detector is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.log_event("Could not read frame from webcam")
            self.stop_detection()
            return

        frame = cv2.resize(frame, (920, 560))
        left_eye, right_eye, face_rect = self.detector.get_landmarks(frame)

        if left_eye and right_eye and face_rect:
            left_ear = eye_aspect_ratio(left_eye)
            right_ear = eye_aspect_ratio(right_eye)
            avg_ear = (left_ear + right_ear) / 2.0

            x1, y1, x2, y2 = face_rect
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 100, 0), 2)

            self.draw_eye(frame, left_eye)
            self.draw_eye(frame, right_eye)

            cv2.putText(
                frame,
                f"EAR: {avg_ear:.2f}",
                (28, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            self.ear_value.config(text=f"{avg_ear:.2f}", fg="white")
            self.face_value.config(text="Detected", fg="#22c55e")

            if avg_ear < EAR_THRESHOLD:
                self.closed_count += 1
            else:
                self.closed_count = 0
                self.alarm_triggered = False
                stop_alarm()
                self.alert_value.config(text="NORMAL", fg="#22c55e")

            if self.closed_count >= CLOSED_FRAMES:
                cv2.putText(
                    frame,
                    "DROWSINESS DETECTED!",
                    (180, 85),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.1,
                    (0, 0, 255),
                    3
                )
                self.alert_value.config(text="DROWSY", fg="#ef4444")

                if not self.alarm_triggered:
                    play_alarm()
                    self.log_event("Drowsiness detected")
                    self.alarm_triggered = True
        else:
            stop_alarm()
            self.closed_count = 0
            self.alarm_triggered = False
            self.face_value.config(text="Not Detected", fg="white")
            self.alert_value.config(text="NORMAL", fg="#22c55e")

            cv2.putText(
                frame,
                "No face detected",
                (28, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 255),
                2
            )

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        imgtk = ImageTk.PhotoImage(image=img)

        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk, text="")

        self.root.after(10, self.update_frame)

    def on_closing(self):
        stop_alarm()

        if self.cap is not None:
            self.cap.release()

        if self.detector is not None:
            self.detector.close()

        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = DrowsinessApp(root)
    root.mainloop()