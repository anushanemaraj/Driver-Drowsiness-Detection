import cv2
import os
from datetime import datetime

class VideoRecorder:
    def __init__(self, output_dir="recordings"):
        self.output_dir = output_dir
        self.is_recording = False
        self.out = None
        os.makedirs(self.output_dir, exist_ok=True)

    def start_recording(self, frame_size):
        if self.is_recording:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"alert_{timestamp}.avi")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.out = cv2.VideoWriter(filename, fourcc, 20.0, frame_size)
        self.is_recording = True
        return filename

    def write_frame(self, frame):
        if self.is_recording and self.out and self.out.isOpened():
            try:
                # Ensure frame is the correct size
                if frame.shape[1] == 900 and frame.shape[0] == 600:
                    self.out.write(frame)
            except Exception as e:
                print(f"Recorder write error: {e}")
                self.stop_recording()

    def stop_recording(self):
        if not self.is_recording:
            return
        
        if self.out:
            self.out.release()
            self.out = None
        self.is_recording = False

recorder = VideoRecorder()
