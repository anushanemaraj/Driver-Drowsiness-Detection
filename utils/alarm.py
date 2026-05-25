import pygame
import os

pygame.mixer.init()
alarm_running = False


def play_alarm():
    global alarm_running

    if alarm_running:
        return

    sound_path = os.path.join("assets", "sound1.mp3")

    if os.path.exists(sound_path):
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play(-1)  # loop continuously
        alarm_running = True


def stop_alarm():
    global alarm_running

    if alarm_running:
        pygame.mixer.music.stop()
        alarm_running = False