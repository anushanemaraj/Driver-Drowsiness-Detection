import subprocess
import threading
import sys
import os

def speak_subprocess(text):
    # Use a small inline python script to handle speech in a separate process
    # This avoids COM/threading issues with pyttsx3 in Flask
    code = f"""
import pyttsx3
try:
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 1.0)
    engine.say({repr(text)})
    engine.runAndWait()
except Exception as e:
    print(e)
"""
    try:
        # Run the speech in a separate process
        subprocess.Popen([sys.executable, "-c", code], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Subprocess voice error: {e}")

class VoiceAlert:
    def __init__(self):
        self.last_speech_time = 0
        self.cooldown = 2.0 # Seconds between alerts to prevent overlap

    def speak(self, text):
        # Subprocess handles its own lifecycle, so we just fire and forget
        # but we add a small cooldown to avoid launching 50 processes
        import time
        current_time = time.time()
        if current_time - self.last_speech_time > self.cooldown:
            print(f"DEBUG: Launching voice subprocess: {text}")
            threading.Thread(target=speak_subprocess, args=(text,), daemon=True).start()
            self.last_speech_time = current_time

voice_alert = VoiceAlert()

def play_voice_alert(text="Warning! Driver appears drowsy."):
    voice_alert.speak(text)
