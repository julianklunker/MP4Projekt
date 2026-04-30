import serial
from time import time, sleep

class Encoder(serial.Serial):
    def __init__(self, port, *args, **kwargs):
        super().__init__(port, baudrate=115200, timeout=2, *args, **kwargs)

        self.write("avg\n".encode("utf-8"))

        self.encoder_update_interval = 5  # seconds

        self.speed = 0
        self.last_update = 0

    def get_speed(self):
        print(f"{__name__}\tStart reading")
        for i in range(5):
            self.reset_input_buffer()
            self.write("avg\n".encode("utf-8"))
            line = self.readline().decode("utf-8").strip()

            if line.startswith("wait"):
                print(f"{__name__}\tBuffer not ready({i}): {line}")
                sleep(1)
                continue
            elif line == "":
                print(f"{__name__}\tArduino not ready ({i}), retrying...")
                continue
            else:
                try:
                    self.speed = int(line)
                    self.last_update = time()
                    print(f"{__name__}\tGot a reading")
                    return self.speed
                except:
                    print(f"{__name__}\tUnexpected response: '{line}', retrying...")
                    sleep(0.5)
                    continue

        print(f"{__name__}\tWARNING: Could not get a valid speed reading.")
        return False


