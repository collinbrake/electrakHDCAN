import can
import argparse

def reverse_bit(num):
    result = 0
    while num:
        result = (result << 1) + (num & 1)
        num >>= 1
    return result

OFF_POSITION = 0
LEN_POSITION = 14

class RecvMsg:
    def __init__(self):
        self.PGN = 0
        self.position = 0
        self.current = 0
        self.speed = 0
        self.overload = 0
        self.voltageError = 0
        self.tempError = 0
        self.motion = False
        self.overload = False
        pass
    
    def getPGN(self, canID):
        bits = canID
        bits = bits >> 8 # 8 for source address
        bits = (bits & 0x3FFFF)
        #print(bin(bits), len(bin(bits)))
        self.PGN = int(bits)
    
    def getPosition(self, data):
        first = data[1]
        second = data[2]
        bits  = first << (14-8)
        bits = bits | second >> 2
        #bits = reverse_bit(bits)
        bitRange = float(2**14)
        valRange = float(400) # mm
        self.position = float(bits) / bitRange * valRange / 10 / 2.54 # inches
        
    def getCurrent(self, data):
        first = data[0]
        second = data[1]
        bits  = (first & 0x3) << 7
        bits = bits | second >> 1
        bits = reverse_bit(bits)
        bitRange = float(2**9)
        valRange = 51.1 # Amps
        self.current = float(bits) / bitRange * valRange # Amps
        
    def getSpeed(self, data):
        first = data[2]
        second = data[3]
        bits = ((first & 1) << 4) | (second & 0xF0)
        bits = reverse_bit(bits)
        bitRange = float(2**5)
        valRange = 1 # 100% duty cycle
        self.speed = float(bits) / bitRange * valRange # Amps
        
    def getVoltageError(self, data):
        bits = data[3] & 0x12
        bits = reverse_bit(bits)
        self.voltageError = int(bits)   
        
    def getTempError(self, data):
        bits = data[3] & 0x3
        bits = reverse_bit(bits)
        self.tempError = int(bits)
       
    def getMotionFlag(self, data):
        bits = (data[4] >> 7)
        self.motion = bits
        
    def getOverloadFlag(self, data):
        bits = (data[4] >> 6) & 1
        self.overload = bits
        

def main():
    while(True):
        bus = can.interface.Bus('can0', bustype='socketcan')
        message = bus.recv()
        print(message)

        msg = RecvMsg()
        msg.getPGN(message.arbitration_id)
        if msg.PGN == 126975:
            msg.getPosition(message.data)
            msg.getCurrent(message.data)
            msg.getSpeed(message.data)
            msg.getVoltageError(message.data)
            msg.getTempError(message.data)
            msg.getMotionFlag(message.data)
            msg.getOverloadFlag(message.data)
            #print(bin(message.data[0]),bin(message.data[1]))
            #print(bin(msg.position), hex(msg.position), msg.position)
        print(msg.PGN, msg.position, msg.current, msg.speed)
        print(msg.voltageError, msg.tempError, msg.motion, msg.overload)

        

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
