import cv2
import mediapipe as mp
import numpy as np


class FaceLandmarkDetector:
    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # FaceMesh eye landmark indices
        self.LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144]
        self.RIGHT_EYE_IDX = [362, 385, 387, 263, 373, 380]
        # Mouth landmark indices for MAR
        self.MOUTH_IDX = [78, 308, 13, 14, 82, 312, 87, 317]
        # Nose and chin for head pose
        self.HEAD_POSE_IDX = [1, 33, 263, 61, 291, 199]  # Nose, L Eye, R Eye, L Mouth, R Mouth, Chin

    def get_landmarks(self, frame):
        h, w = frame.shape[:2]
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.face_mesh.process(rgb_frame)

        if not results.multi_face_landmarks:
            return None, None, None, None, None

        face_landmarks = results.multi_face_landmarks[0]

        left_eye = []
        right_eye = []
        mouth = []
        head_pose_pts = []

        for idx in self.LEFT_EYE_IDX:
            x = int(face_landmarks.landmark[idx].x * w)
            y = int(face_landmarks.landmark[idx].y * h)
            left_eye.append((x, y))

        for idx in self.RIGHT_EYE_IDX:
            x = int(face_landmarks.landmark[idx].x * w)
            y = int(face_landmarks.landmark[idx].y * h)
            right_eye.append((x, y))

        for idx in self.MOUTH_IDX:
            x = int(face_landmarks.landmark[idx].x * w)
            y = int(face_landmarks.landmark[idx].y * h)
            mouth.append((x, y))

        for idx in self.HEAD_POSE_IDX:
            x = int(face_landmarks.landmark[idx].x * w)
            y = int(face_landmarks.landmark[idx].y * h)
            head_pose_pts.append((x, y))

        # simple face rectangle from all landmarks
        xs = [int(lm.x * w) for lm in face_landmarks.landmark]
        ys = [int(lm.y * h) for lm in face_landmarks.landmark]

        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        face_rect = (x_min, y_min, x_max, y_max)

        # Estimate head pose
        head_pose = self.estimate_head_pose(head_pose_pts, w, h)

        return left_eye, right_eye, mouth, face_rect, head_pose

    def estimate_head_pose(self, points, w, h):
        # 3D model points (generic face model)
        model_points = np.array([
            (0.0, 0.0, 0.0),             # Nose tip
            (-225.0, 170.0, -135.0),     # Left eye left corner
            (225.0, 170.0, -135.0),      # Right eye right corner
            (-150.0, -150.0, -125.0),    # Left Mouth corner
            (150.0, -150.0, -125.0),     # Right mouth corner
            (0.0, -330.0, -65.0)         # Chin
        ])

        # 2D image points
        image_points = np.array(points, dtype="double")

        # Camera matrix
        focal_length = w
        center = (w / 2, h / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype="double")

        # Dist coeffs
        dist_coeffs = np.zeros((4, 1))

        # Solve PnP
        (success, rotation_vector, translation_vector) = cv2.solvePnP(
            model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
        )

        # Rotation matrix
        rmat, _ = cv2.Rodrigues(rotation_vector)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

        # angles: [pitch, yaw, roll]
        return angles

    def close(self):
        self.face_mesh.close()