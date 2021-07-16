import argparse
import time
from datetime import datetime
import signal
import sys
import os
import math

import electrak

def main():
    
    ecu = electrak.ActuatorManager()
    ecu.bringupCAN(port=args.port)

    def signalHandler(sig, frame):
        ecu.saveLogs()
        sys.exit(0)

    signal.signal(signal.SIGINT, signalHandler)
    
    t_0 = datetime.now()

    while(True):

        t = (datetime.now() - t_0).total_seconds() # time in seconds since start
        T = 20 # period, seconds
        omega = 1/T *2 * math.pi # frequency, radians per second
        pos = 150*math.sin(omega * t) + 175

        valueLogEntry = ecu.interface(electrak.ACM(pos, args.speed))
        os.system("clear")
        print("RECIEVING---------\n", valueLogEntry)
        #time.sleep(0.1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=str)
    parser.add_argument("-s", "--speed", type=int, default=50)
    args = parser.parse_args()
    
    main()
 
        
        

