import can
import time
import argparse
from util import reverse_bit
from pandas import DataFrame

class SendMsg:
    def __init__(self, pos, spd):
        self.pgn = 61184
        self.position = int(pos)
        self.currentLim = 10
        self.speed = int(spd)
        self.motionEn = True
    
    def id(self):
        return (0b110 << 26) | (self.pgn << 8) | 0xFF
    
    def positionScaled(self):
        return int(self.position / 0.1)
    
    def currentLimScaled(self):
        return int(self.currentLim / 0.1)
    
    def speedScaled(self):
        return int(round(self.speed / 5))
    
    def motionEnInt(self):
        return int(self.motionEn)
    
    def getMessageBits(self):
        data = bytearray([0, 0, 0, 0, 0, 0, 0, 0])
        data0 = reverse_bit(self.positionScaled(), 14) >> 6
        data1 = reverse_bit(self.positionScaled(), 14) << 2 | reverse_bit(self.currentLimScaled(), 9) >> 7
        data2 = reverse_bit(self.currentLimScaled(), 9) << 1 | reverse_bit(self.speedScaled(), 5) >> 4
        data3 = reverse_bit(self.speedScaled(), 5) << 4 | reverse_bit(self.motionEnInt(), 1) << 3
        
        data[0] = data0 & 0xFF
        data[1] = data1 & 0xFF
        data[2] = data2 & 0xFF
        data[3] = data3 & 0xFF

        return data

def main():
    bus = can.interface.Bus('can0', bustype='socketcan')
    
    sender = SendMsg(200, 5)
    
    sender.getMessageBits()

    while(True):
        msg = can.Message(arbitration_id = sender.id(), is_extended_id=True, data=sender.getMessageBits())
        
        bus.send(msg)
        
        time.sleep(0.1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="Bag file to read" +
                        ", excluding extention. Name of output avi file."+
                        " and corresponding CSV file.")

    parser.add_argument("-o", "--outputNumber", type=str, help="copy number " +
                        "of output to write to" +
                        "so it doesn't overwrite previous output.")
    args = parser.parse_args()
    main()
