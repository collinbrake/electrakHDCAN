import argparse
import time
import signal
import sys
import os

import electrak

def main():
    
    ecu = electrak.ActuatorManager()
    ecu.bringupCAN(port=args.port)

    def signalHandler(sig, frame):
        ecu.saveLogs()
        sys.exit(0)

    signal.signal(signal.SIGINT, signalHandler)
    
    while(True):
        valueLogEntry = ecu.interface(electrak.ACM(args.position, args.speed))
        os.system("clear")
        print("RECIEVING---------\n", valueLogEntry)
        time.sleep(0.1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=str)
    parser.add_argument("-s", "--speed", type=int, default=50)
    parser.add_argument("-l", "--position", type=int, default=50)
    args = parser.parse_args()
    
    main()
