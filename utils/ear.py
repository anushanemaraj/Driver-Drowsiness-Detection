from math import dist


def eye_aspect_ratio(eye):
    # eye should contain 6 points
    # p1, p2, p3, p4, p5, p6
    A = dist(eye[1], eye[5])
    B = dist(eye[2], eye[4])
    C = dist(eye[0], eye[3])

    if C == 0:
        return 0.0

    ear = (A + B) / (2.0 * C)
    return ear


def mouth_aspect_ratio(mouth):
    # mouth points: [78, 308, 13, 14, 82, 312, 87, 317]
    # left_corner = mouth[0]
    # right_corner = mouth[1]
    # top_mid = mouth[2]
    # bottom_mid = mouth[3]
    # top_left = mouth[4]
    # top_right = mouth[5]
    # bottom_left = mouth[6]
    # bottom_right = mouth[7]

    # Vertical distances
    A = dist(mouth[2], mouth[3])  # Center
    B = dist(mouth[4], mouth[7])  # Left side
    C = dist(mouth[5], mouth[6])  # Right side

    # Horizontal distance
    D = dist(mouth[0], mouth[1])

    if D == 0:
        return 0.0

    mar = (A + B + C) / (2.0 * D)
    return mar