import mediapipe as mp
import os

print(f"MediaPipe path: {mp.__file__}")
print(f"MediaPipe dir: {dir(mp)}")

try:
    from mediapipe.python.solutions import face_mesh
    print("Successfully imported face_mesh from python.solutions")
except Exception as e:
    print(f"Failed to import face_mesh: {e}")
