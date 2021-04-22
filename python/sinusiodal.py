import can
import os
import argparse
import math
import time
from datetime import datetime
from pandas import DataFrame

import electrak

def main():
    bus = can.interface.Bus('can0', bustype='socketcan')
    afm = electrak.AFM()
    acm = electrak.ACM(0, args.speed)
    t_0 = datetime.now()
    fileNameTime = time.gmtime()
    
    record = 
    
    os.system("clear")
    
    bus.send(can.Message(arbitration_id = acm.id(), is_extended_id=True, data=acm.getBytes()))
    t_last_send = datetime.now() # don't send out for 1 second

    while(True):
        
        t = (datetime.now() - t_0).total_seconds() # time in seconds since start

        T = 12 # period, seconds
        omega = 1/T *2 * math.pi # frequency, radians per second
        
        pos = 100*math.sin(omega * t) + 100

        
        
        

