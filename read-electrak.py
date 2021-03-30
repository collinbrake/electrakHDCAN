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
        bits = (bits & 0x3FF00) # mask out the last 8 bits because they form the PDU specific, the destination address in peer-to-peer
        # see line in benkfra/j1939 in notify function
        #print(bin(bits), len(bin(bits)))
        self.PGN = int(bits)

    def getBits(self, data, dataLength, start, length):
        offset = dataLength - (start + length) # offset from right
        mask = 0
        for i in range(0, length):
            mask |= 1 << i
        mask <<= offset
        bits = (data & mask) >> offset
        bits = reverse_bit(bits)
        print(bin(data), bin(mask), bin(bits), int(bits))
        return bits

    
    def getPosition(self, data, dataLength, start, length):
        bits = self.getBits(data, dataLength, start, length)
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
        self.motion = bool(bits)
        
    def getOverloadFlag(self, data):
        bits = (data[4] >> 6) & 1
        self.overload = bool(bits)
        

def main():
    msg = RecvMsg()
    while(True):
        bus = can.interface.Bus('can0', bustype='socketcan')
        message = bus.recv()
        #print(message)

        msg.getPGN(message.arbitration_id)
        if msg.PGN == 126720:
            msg.getPosition(message.data[0] << 8 | message.data[1], 16, 0, 14)
            msg.getCurrent(message.data)
            msg.getSpeed(message.data)
            msg.getVoltageError(message.data)
            msg.getTempError(message.data)
            msg.getMotionFlag(message.data)
            msg.getOverloadFlag(message.data)
            #print(bin(message.data[0]),bin(message.data[1]))
            #print(bin(msg.position), hex(msg.position), msg.position)
        print("PGN:", msg.PGN, "POS:", msg.position, "Amp:", msg.current, "SPD:", msg.speed)
        print("VOE:", msg.voltageError, "TPE:", msg.tempError, "MTN:", msg.motion, "OVL:", msg.overload)

        

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
