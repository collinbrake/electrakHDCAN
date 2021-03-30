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
        self.backdrive = False
        self.parameter = False
        self.saturation = False
        self.fatalError = False
        pass
    
    def getPGN(self, canID):
        bits = canID
        bits = bits >> 8 # 8 for source address
        bits = (bits & 0x3FF00) # mask out the last 8 bits because they form the PDU specific, the destination address in peer-to-peer
        # see line in benkfra/j1939 in notify function
        #print(bin(bits), len(bin(bits)))
        self.PGN = int(bits)

    def getBits(self, data1, data2, start, length):
        
        # Get the complete set of input bits reverse bit order to account for CAN protocol
        data = reverse_bit(data1)
        dataLength = 8
        if data2 != None:
            data = data << 8 | reverse_bit(data2)
            dataLength = 16

        offset = dataLength - (start + length) # offset from right
        mask = 0
        for i in range(0, length):
            mask |= 1 << i
        mask <<= offset
    
        bits = reverse_bit((data & mask) >> offset) # this line is to account for reverse bit order specified in electrak manual
        print(bin(data), bin(mask), bin(bits), int(bits))
        #bits = reverse_bit(bits)
        return bits

    
    def getPosition(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, start, length)
        bitRange = float(2**14)
        valRange = float(400) # mm
        self.position = float(bits) / bitRange * valRange / 10 / 2.54 # inches
        
    def getCurrent(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, start, length)
        bitRange = float(2**9)
        valRange = 51.1 # Amps
        self.current = float(bits) / bitRange * valRange # Amps
        
    def getSpeed(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, start, length)
        bitRange = float(2**5)
        valRange = 1 # 100% duty cycle
        self.speed = float(bits) / bitRange * valRange # Amps
        
    def getVoltageError(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, start, length)
        self.voltageError = int(bits)   
        
    def getTempError(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, start, length)
        self.tempError = int(bits)
       
    def getMotion(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, start, length)
        self.motion = bool(bits)
        
    def getOverload(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, start, length)
        self.overload = bool(bits)
        
    def getBackdrive(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, start, length)
        self.backdrive = bool(bits)
        
    def getParameter(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, start, length)
        self.parameter = bool(bits)

    def getSaturation(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, start, length)
        self.saturation = bool(bits)

    def getFatalError(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, start, length)
        self.fatalError = bool(bits)
        

def main():
    msg = RecvMsg()
    while(True):
        bus = can.interface.Bus('can0', bustype='socketcan')
        message = bus.recv()
        #print(message)
        for datai in message.data:
            print(bin(datai))

        msg.getPGN(message.arbitration_id)
        if msg.PGN == 126720:
            msg.getPosition(message.data[0], message.data[1], 0, 14)
            msg.getCurrent(message.data[1], message.data[2], 6, 9)
            msg.getSpeed(message.data[2], message.data[3], 7, 5)
            msg.getVoltageError(message.data[3], None, 4, 2)
            msg.getTempError(message.data[3], None, 6, 2)
            msg.getMotion(message.data[4], None, 0, 1)
            msg.getOverload(message.data[4], None, 1, 1)
            msg.getBackdrive(message.data[4], None, 2, 1)
            msg.getParameter(message.data[4], None, 3, 1)
            msg.getSaturation(message.data[4], None, 4, 1)
            msg.getFatalError(message.data[4], None, 5, 1)
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
