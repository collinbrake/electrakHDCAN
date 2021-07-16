import argparse
import time
import serial as s
from datetime import datetime
import signal
import sys
import os
import math

import electrak

class Read_Linear_Encoder:

    def __init__(self, transducer_min, transducer_max):
        self.min = transducer_min
        self.max = transducer_max
        self.range = transducer_max - transducer_min

        # Initialize the toolbar position at midpoint of range
        self.position = self.range/2 + self.min
        self.serial_init = False

    def init_serial(self, serial):
        self.serial_init = True
        self.serial = serial

    def get(self):
        self.serial.write(("Keep interface open").encode())
        if self.serial_init:
            line = self.serial.readline()
            line_decoded = line.decode('ascii')

            # Filter out non-integers comming
            # from micro controller. This enables
            # debugging messages to be sent from
            # the micro controller along with the
            # transducer readings
            try:
                self.position = int(line_decoded)
            except ValueError:
                pass

def main():
    
    port = '/dev/ttyACM2'
    baud = 9600
    #serial = s.Serial(port, baud, timeout=.1)
    #serial.write(("Start signal").encode())
    position = Read_Linear_Encoder(130, 972)
    #position.init_serial(serial)

    ecu = electrak.ActuatorManager(position_checker=position)
    ecu.bringupCAN(port=args.port)

    def signalHandler(sig, frame):
        ecu.saveLogs()
        sys.exit(0)

    signal.signal(signal.SIGINT, signalHandler)

    t_0 = datetime.now()
    t = (datetime.now() - t_0).total_seconds() # time in seconds since start

    while(True):

        #if (datetime.now() - t_0).total_seconds() - t >= 0.1:
        t = (datetime.now() - t_0).total_seconds() # time in seconds since start
        T = 20 # period, seconds
        omega = 1/T *2 * math.pi # frequency, radians per second
        pos = 100*math.sin(omega * t) + 150

        valueLogEntry = ecu.interface(electrak.ACM(pos, args.speed))
        os.system("clear")
        print("RECIEVING---------\n", valueLogEntry)
        #position.get()
        #print(position.position)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=str)
    parser.add_argument("-s", "--speed", type=int, default=50)
    args = parser.parse_args()
    
    main()
 
        
        

