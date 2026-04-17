from pathlib import Path
import sys
import time

from gpiozero import Button
from ADCDevice import *

sys.path.insert(0, str(Path(__file__).resolve().parent / "python"))
import electrak


Z_Pin = 18
SPEED_PERCENT = 30

button = Button(Z_Pin)
adc = ADCDevice()
ecu = None


def setup():
    global adc
    global ecu

    if adc.detectI2C(0x48):
        adc = PCF8591()
    elif adc.detectI2C(0x4B):
        adc = ADS7830()
    else:
        print("No correct I2C address found")
        raise SystemExit(-1)

    ecu = electrak.ActuatorManager()
    ecu.bringupCAN(iface="can0")


def map_value(x, in_min=0, in_max=255, out_min=0, out_max=250):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)


def loop():
    last_position = -1

    while True:
        val_X = adc.analogRead(1)

        # Map X to actuator position (0-250 mm)
        position = map_value(val_X)

        # Only send command if position changes enough.
        if abs(position - last_position) > 2:
            print(f"Target Position: {position} mm | Speed: {SPEED_PERCENT}%")
            ecu.interface(electrak.ACM(position, SPEED_PERCENT))
            last_position = position

        time.sleep(0.05)


def destroy():
    adc.close()
    button.close()
    if ecu is not None:
        ecu.shutdown()


if __name__ == "__main__":
    print("Program is starting ...")
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        destroy()
        print("Ending program")