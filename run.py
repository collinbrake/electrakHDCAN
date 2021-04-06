import can
import os
import argparse
import math
import time

import electrak

def main():
    bus = can.interface.Bus('can0', bustype='socketcan')
    afm = electrak.AFM()
    acm = electrak.ACM(args.position, args.speed)
    
    os.system("clear")
    
    bus.send(can.Message(arbitration_id = acm.id(), is_extended_id=True, data=acm.getBytes()))

    while(True):

        feedback = bus.recv()
            
        os.system("clear")
        logEntry = afm.get(feedback)
        print(logEntry)
        print("\n")
        
        bus.send(can.Message(arbitration_id = acm.id(), is_extended_id=True, data=acm.getBytes()))
        print(acm.getBytes())
        pdu, logEntry = acm.log()
        print(pdu+":\n")
        print(logEntry)
        time.sleep(0.1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--speed", type=int)

    parser.add_argument("-p", "--position", type=int)
    args = parser.parse_args()
    
    main()
