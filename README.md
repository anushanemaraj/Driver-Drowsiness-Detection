# Advanced AI Driver Monitoring System

A professional, real-time driver safety and fatigue monitoring dashboard powered by Computer Vision and AI.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Latest-green?style=for-the-badge)
![Flask](https://img.shields.io/badge/Flask-Web%20App-lightgrey?style=for-the-badge&logo=flask)

## 🚀 Overview
This system utilizes high-precision facial landmark detection (MediaPipe Face Mesh) to monitor driver alertness in real-time. It features a modern, cyberpunk-inspired web dashboard for live telemetry, automated incident recording, and a multi-tiered voice alert system.

### Key Features
- **Fatigue Scoring Engine**: Dynamic calculation of fatigue levels (0-100%) based on EAR, MAR, head pose, and blink patterns.
- **Yawn Detection**: High-precision MAR monitoring with debounce logic to prevent double counting.
- **Tiered Alerts**: 
  - **Drowsiness**: Immediate loud alarm + Voice warning.
  - **Yawning**: Progressive voice warnings (at 3 yawns and 5+ yawns).
- **Incident Recording**: Automatically records `.avi` video clips when drowsiness is detected.
- **Head Pose Estimation**: Tracks Pitch, Yaw, and Roll to detect when the driver is not looking at the road.
- **Live Dashboard**: Real-time Chart.js telemetry for EAR/MAR, session statistics, and event logs.
- **Dynamic Calibration**: Calibrates to the specific driver's facial features upon startup.

## 📁 Project Structure
- `app.py`: Core Flask application and monitoring state machine.
- `utils/`:
  - `detector.py`: MediaPipe 468-point landmark processing & 3D Head Pose.
  - `ear.py`: Geometric EAR and MAR calculations.
  - `voice.py`: Subprocess-based `pyttsx3` for isolated voice synthesis.
  - `recorder.py`: OpenCV VideoWriter logic for incident capture.
  - `model.py`: Rule-based AI classifier for fatigue state prediction.
- `static/`: Frontend assets (Tailwind CSS, Chart.js, custom JS).
- `templates/`: Modern Dashboard UI (HTML5).

## 🛠️ Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Drowsiness-Detection.git
   cd "Drowsiness Detection"
   ```

2. **Setup Virtual Environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## 🚦 Getting Started

1. **Run the Application**
   ```bash
   python app.py
   ```
2. **Access the Dashboard**
   Open your browser and navigate to `http://127.0.0.1:5000`.
3. **Initialize System**
   Click **"START SYSTEM"** on the sidebar.
4. **Calibrate**
   Use the **"RE-CALIBRATE"** button in settings or the dashboard to set your baseline neutral expression for higher accuracy.

## ⚙️ Configuration
- **EAR Threshold**: 0.22 (Drowsiness detection limit)
- **MAR Threshold**: 0.50 (Yawning detection limit)
- **Debounce**: 6 seconds (Prevents double-counting a single yawn)

## 🛡️ Safety Note
This software is intended for educational and monitoring purposes only. It should not be used as a primary safety device in a vehicle. Always ensure you are well-rested before driving.

---
*Developed as an Advanced AI Driver Monitoring Solution.*

## Note
This project uses webcam-based real-time drowsiness detection.
Live deployment is hosted on Render for demonstration purposes.
For full webcam functionality, run locally using:

python app.py
