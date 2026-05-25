from flask import Flask, render_template, Response, jsonify, request, send_from_directory
import cv2
import os
import time
import threading
from datetime import datetime
import numpy as np

from utils.alarm import play_alarm, stop_alarm
from utils.detector import FaceLandmarkDetector
from utils.ear import eye_aspect_ratio, mouth_aspect_ratio
from utils.voice import play_voice_alert
from utils.recorder import recorder
from utils.model import fatigue_predictor

app = Flask(__name__)
metrics_lock = threading.Lock()

# Configuration & Thresholds
EAR_THRESHOLD = 0.22
MAR_THRESHOLD = 0.50
CLOSED_FRAMES = 15
YAWN_FRAMES = 10
LOG_FILE = "logs/drowsiness_log.txt"
MAX_HISTORY = 50

# State Variables
running = False
face_detected = False
drowsy = False
yawning = False
alarm_enabled = True
voice_enabled = True
recording_enabled = True

# Metrics
current_ear = 0.0
current_mar = 0.0
head_pose = (0, 0, 0)
fatigue_score = 0.0
fatigue_status = "Normal"

# Counters
closed_count = 0
yawn_count = 0
total_yawns = 0
total_alerts = 0
blink_count = 0
frame_count = 0
last_yawn_time = 0

# History for charts
ear_history = []
mar_history = []
alert_history = []
recent_ear_values = []

# Calibration
is_calibrating = False
calibration_frames = 0
base_ear = 0.28
base_mar = 0.15

start_time = None

# FIXED FOR RENDER
cap = None
detector = None


def log_event(event_type, message):
    os.makedirs("logs", exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{event_type}] {message}\n")


def get_logs():
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return [line.strip() for line in lines[-15:]]


def update_history(ear, mar):
    ear_history.append(round(ear, 3))
    mar_history.append(round(mar, 3))

    if len(ear_history) > MAX_HISTORY:
        ear_history.pop(0)
        mar_history.pop(0)


def calculate_fatigue_score(ear, mar, b_rate, p, y, r, y_count):

    ear_threshold = base_ear * 0.9

    if ear < ear_threshold:
        ear_range = ear_threshold - EAR_THRESHOLD
        ear_score = min(1, (ear_threshold - ear) / ear_range) * 45
    else:
        ear_score = 0

    mar_limit = 0.4

    if mar > mar_limit:
        mar_score = min(1, (mar - mar_limit) / (MAR_THRESHOLD - mar_limit)) * 15
    else:
        mar_score = 0

    pose_dev = (abs(p) + abs(y) + abs(r))

    if pose_dev > 45:
        pose_score = min(1, (pose_dev - 45) / 45) * 20
    else:
        pose_score = 0

    yawn_impact = min(20, y_count * 4)

    score = ear_score + mar_score + pose_score + yawn_impact

    return min(100, round(score, 1))


def generate_frames():

    global closed_count, yawn_count, total_yawns, total_alerts, blink_count
    global current_ear, current_mar, face_detected, drowsy, yawning
    global head_pose, fatigue_score, fatigue_status, frame_count
    global is_calibrating, calibration_frames, base_ear, base_mar, recent_ear_values
    global cap, detector

    # FIXED FOR RENDER
    if cap is None or detector is None:
        return

    while True:

        success, frame = cap.read()

        if not success:
            break

        frame = cv2.resize(frame, (900, 600))

        h, w = frame.shape[:2]

        if running:

            frame_count += 1

            left_eye, right_eye, mouth, face_rect, pose = detector.get_landmarks(frame)

            if left_eye and right_eye and mouth and face_rect:

                face_detected = True

                head_pose = pose

                l_ear = eye_aspect_ratio(left_eye)
                r_ear = eye_aspect_ratio(right_eye)

                raw_ear = (l_ear + r_ear) / 2.0

                current_mar = mouth_aspect_ratio(mouth)

                recent_ear_values.append(raw_ear)

                if len(recent_ear_values) > 10:
                    recent_ear_values.pop(0)

                current_ear = sum(recent_ear_values) / len(recent_ear_values)

                update_history(current_ear, current_mar)

                if is_calibrating:

                    calibration_frames += 1

                    if calibration_frames == 1:
                        base_ear = current_ear
                    else:
                        base_ear = (
                            (base_ear * (calibration_frames - 1) + current_ear)
                            / calibration_frames
                        )

                    if calibration_frames > 100:
                        is_calibrating = False
                        log_event("INFO", f"Calibration complete. Base EAR: {base_ear:.3f}")
                        calibration_frames = 0

                approx_blink_rate = blink_count / (frame_count / 20 + 1)

                fatigue_status, _ = fatigue_predictor.predict([
                    current_ear,
                    current_mar,
                    approx_blink_rate,
                    head_pose[0],
                    head_pose[1],
                    head_pose[2]
                ])

                fatigue_score = calculate_fatigue_score(
                    current_ear,
                    current_mar,
                    approx_blink_rate,
                    head_pose[0],
                    head_pose[1],
                    head_pose[2],
                    total_yawns
                )

                x1, y1, x2, y2 = face_rect

                color = (0, 255, 0)

                if fatigue_status == "Sleepy" or fatigue_score > 40:
                    color = (0, 255, 255)

                if fatigue_status == "Highly Fatigued" or fatigue_score > 70:
                    color = (0, 0, 255)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                for p in left_eye + right_eye:
                    cv2.circle(frame, p, 2, (0, 255, 0), -1)

                for p in mouth:
                    cv2.circle(frame, p, 2, (255, 0, 0), -1)

                # DROWSINESS
                if current_ear < EAR_THRESHOLD:
                    closed_count += 1
                else:

                    if closed_count >= 2 and closed_count < CLOSED_FRAMES:
                        with metrics_lock:
                            blink_count += 1

                    closed_count = 0
                    drowsy = False

                    stop_alarm()
                    recorder.stop_recording()

                if closed_count >= CLOSED_FRAMES:

                    drowsy = True

                    if not recorder.is_recording and recording_enabled:

                        recorder.start_recording((900, 600))

                        with metrics_lock:
                            total_alerts += 1

                        alert_history.append(datetime.now().strftime("%H:%M:%S"))

                        log_event("ALERT", "Drowsiness detected")

                        if alarm_enabled:
                            play_alarm()

                        if voice_enabled:
                            play_voice_alert(
                                "Warning! Driver appears drowsy. Please wake up!"
                            )

                # YAWNING
                if current_mar > MAR_THRESHOLD:

                    yawn_count += 1

                    if yawn_count >= 5:
                        yawning = True

                    if yawn_count >= YAWN_FRAMES:

                        current_time = time.time()

                        if current_time - last_yawn_time > 6.0:

                            with metrics_lock:

                                total_yawns += 1

                                log_event(
                                    "INFO",
                                    f"Yawning detected (Total: {total_yawns})"
                                )

                                if voice_enabled:

                                    if total_yawns == 3:
                                        play_voice_alert(
                                            "Alert! You have yawned 3 times."
                                        )

                                    elif total_yawns >= 5:
                                        play_voice_alert(
                                            "Critical Warning! Please stop and rest immediately."
                                        )

                else:
                    yawn_count = 0
                    yawning = False

                cv2.putText(
                    frame,
                    f"Fatigue: {fatigue_status} ({fatigue_score}%)",
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    color,
                    2
                )

                cv2.putText(
                    frame,
                    f"EAR: {current_ear:.2f} MAR: {current_mar:.2f}",
                    (30, 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    1
                )

                if drowsy:
                    cv2.putText(
                        frame,
                        "!!! DROWSY !!!",
                        (w // 2 - 100, h // 2),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1.5,
                        (0, 0, 255),
                        3
                    )

                if yawning:
                    cv2.putText(
                        frame,
                        "Yawning...",
                        (w // 2 - 80, h // 2 + 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 255),
                        2
                    )

            else:

                face_detected = False
                drowsy = False
                yawning = False

                closed_count = 0
                yawn_count = 0

                stop_alarm()
                recorder.stop_recording()

                cv2.putText(
                    frame,
                    "No Face Detected",
                    (30, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 0, 255),
                    2
                )

        else:

            face_detected = False
            drowsy = False
            yawning = False

            stop_alarm()
            recorder.stop_recording()

            cv2.putText(
                frame,
                "System Standby",
                (30, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )

        ret, buffer = cv2.imencode(".jpg", frame)

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/start", methods=["POST"])
def start():

    global running, start_time, cap, detector

    running = True
    start_time = time.time()

    # FIXED FOR RENDER
    if cap is None:
        cap = cv2.VideoCapture(0)

    if detector is None:
        detector = FaceLandmarkDetector()

    log_event("SYSTEM", "Monitoring started")

    return jsonify({"success": True})


@app.route("/stop", methods=["POST"])
def stop():

    global running

    running = False

    log_event("SYSTEM", "Monitoring stopped")

    return jsonify({"success": True})


@app.route("/status")
def status():

    session_duration = 0

    if start_time and running:
        session_duration = int(time.time() - start_time)

    return jsonify({
        "running": running,
        "face_detected": face_detected,
        "drowsy": drowsy,
        "yawning": yawning,
        "fatigue_score": fatigue_score,
        "fatigue_status": fatigue_status,
        "current_ear": current_ear,
        "current_mar": current_mar,
        "total_alerts": total_alerts,
        "total_yawns": total_yawns,
        "session_duration": session_duration,
        "ear_history": ear_history,
        "mar_history": mar_history,
        "alert_history": alert_history[-5:],
        "alarm_enabled": alarm_enabled,
        "voice_enabled": voice_enabled,
        "recording_enabled": recording_enabled,
        "logs": get_logs()
    })


@app.route("/settings", methods=["POST"])
def update_settings():

    global alarm_enabled, voice_enabled, recording_enabled

    data = request.json

    alarm_enabled = data.get("alarm", alarm_enabled)
    voice_enabled = data.get("voice", voice_enabled)
    recording_enabled = data.get("recording", recording_enabled)

    return jsonify({"success": True})


@app.route("/calibrate", methods=["POST"])
def calibrate():

    global is_calibrating, calibration_frames

    is_calibrating = True
    calibration_frames = 0

    return jsonify({"success": True})


@app.route("/recordings")
def get_recordings():

    recordings_dir = "recordings"

    if not os.path.exists(recordings_dir):
        return jsonify([])

    files = os.listdir(recordings_dir)

    video_files = [
        f for f in files
        if f.endswith((".avi", ".mp4"))
    ]

    video_files.sort(
        key=lambda x: os.path.getmtime(os.path.join(recordings_dir, x)),
        reverse=True
    )

    return jsonify(video_files)


@app.route("/recordings/<filename>")
def download_recording(filename):
    return send_from_directory("recordings", filename)


@app.route("/analytics")
def analytics():

    avg_ear = sum(ear_history) / len(ear_history) if ear_history else 0
    avg_mar = sum(mar_history) / len(mar_history) if mar_history else 0

    return jsonify({
        "total_alerts": total_alerts,
        "total_yawns": total_yawns,
        "avg_ear": round(avg_ear, 3),
        "avg_mar": round(avg_mar, 3),
        "fatigue_score": fatigue_score,
        "session_duration": int(time.time() - start_time) if start_time else 0
    })


@app.route("/logs")
def logs_api():
    return jsonify({"logs": get_logs()})


@app.route("/clear_logs", methods=["POST"])
def clear_logs():

    if os.path.exists(LOG_FILE):

        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [SYSTEM] Logs cleared\n"
            )

    return jsonify({"success": True})


@app.route("/reset", methods=["POST"])
def reset_metrics():

    global total_yawns, total_alerts, blink_count
    global ear_history, mar_history, alert_history

    with metrics_lock:

        total_yawns = 0
        total_alerts = 0
        blink_count = 0

        ear_history = []
        mar_history = []
        alert_history = []

    return jsonify({"success": True})


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)