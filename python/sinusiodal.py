import argparse
import time
from datetime import datetime
import signal
import sys
import os
import math

import electrak

def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", type=str)
    parser.add_argument("-c", "--channel", type=str, default="can0")
    parser.add_argument("-i", "--interface", type=str, default="socketcan")
    parser.add_argument("-s", "--speed", type=int, default=50)
    parser.add_argument("--count", type=int, default=0)
    parser.add_argument("--interval", type=float, default=0.1)
    parser.add_argument("--no-clear", dest="clear", action="store_false")
    parser.set_defaults(clear=True)
    return parser


def main(args):
    
    ecu = electrak.ActuatorManager()
    ecu.bringupCAN(
        port=args.port,
        iface=args.channel,
        interface=args.interface,
        bringup=bool(args.port),
    )

    def signalHandler(sig, frame):
        ecu.saveLogs()
        ecu.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signalHandler)
    
    t_0 = datetime.now()

    iterations = 0

    while True:

        t = (datetime.now() - t_0).total_seconds() # time in seconds since start
        T = 20 # period, seconds
        omega = 1/T *2 * math.pi # frequency, radians per second
        pos = 150*math.sin(omega * t) + 175

        valueLogEntry = ecu.interface(electrak.ACM(pos, args.speed))
        if args.clear:
            os.system("clear")
        print("RECIEVING---------\n", valueLogEntry)
        iterations += 1
        if args.count and iterations >= args.count:
            ecu.saveLogs()
            ecu.shutdown()
            return
        time.sleep(args.interval)

if __name__ == "__main__":
    main(build_parser().parse_args())
 
        
        

