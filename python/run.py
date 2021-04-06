import can
import os
import argparse
import math
import time

import electrak

def main():
    bus = can.interface.Bus('can0', bustype='socketcan')
    afm = electrak.AFM(args.log)
    acm = electrak.ACM(args.position, args.speed, args.log)
    
    os.system("clear")
    
    bus.send(can.Message(arbitration_id = acm.id(), is_extended_id=True, data=acm.getBytes()))

    while(True):

        feedback = bus.recv()
            
        os.system("clear")
        logEntry = afm.get(feedback)
        print("RECIEVING --------------------\n", logEntry, "\n")
        
        bus.send(can.Message(arbitration_id = acm.id(), is_extended_id=True, data=acm.getBytes()))
        pdu, logEntry = acm.log()
        print("SENDING:", pdu, "--------------------\n", logEntry)
        time.sleep(0.1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--speed", type=int)
    parser.add_argument("-p", "--position", type=int)
    parser.add_argument("-l", "--log", type=bool)
    args = parser.parse_args()
    
    
    main()
