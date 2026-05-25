import threading
import time
import platform

alarm_running = False

if platform.system() == "Windows":
    import winsound


def play_alarm():
    global alarm_running

    if alarm_running:
        return

    alarm_running = True

    def run():
        global alarm_running

        while alarm_running:
            try:
                if platform.system() == "Windows":
                    winsound.Beep(1200, 700)

                time.sleep(0.5)

            except:
                break

    threading.Thread(target=run, daemon=True).start()


def stop_alarm():
    global alarm_running
    alarm_running = False