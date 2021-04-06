import time
from util import reverse_bit
from pandas import DataFrame

# Thomson Linear Electrac HD CAN J1939 Actuator Feedback Message Decoder
class AFM:
    def __init__(self):
        self.PGN = 0
        self.position = 0.0
        self.current = 0.0
        self.speed = 0
        self.voltageError = 0
        self.tempError = 0
        self.motion = False
        self.overload = False
        self.backdrive = False
        self.parameter = False
        self.saturation = False
        self.fatalError = False
        
        self.record = DataFrame({"position" : [],
                              "current" : [],
                              "speed" : [],
                              "voltage error" : [],
                              "temp error" : [],
                              "motion" : [],
                              "overload" : [],
                              "back drive" : [],
                              "parameter" : [],
                              "saturation" : [],
                              "fatal error" : [],
                     }, dtype=str)
        self.logPath = "electrakhd_can_recv" +time.strftime("%Y-%m-%d_%Hh%Mm%Ss", time.gmtime()) + ".csv"
        
    def get(self, message):
        self.getPGN(message.arbitration_id)
        if self.PGN == 126720:
            self.getPosition(message.data[0], message.data[1], 0, 14)
            self.getCurrent(message.data[1], message.data[2], 6, 9)
            self.getBackdrive(message.data[4], None, 2, 1)
            self.getParameter(message.data[4], None, 3, 1)
            self.getSaturation(message.data[4], None, 4, 1)
            self.getFatalError(message.data[4], None, 5, 1)
            
        return self.log()
    
    def getPGN(self, canID):
        bits = canID
        bits = bits >> 8
        bits = (bits & 0x3FF00) 
        self.PGN = int(bits)

    def getBits(self, data1, data2, shft, mask, length):
        
        # Get the complete set of input bits reverse bit order to account for CAN protocol
        data = reverse_bit(data1, 8)
        if data2 != None:
            data = data << 8 | reverse_bit(data2, 8)

        bits = reverse_bit((data >> shft) & mask, length) # this line is to account for reverse bit order specified in electrak manual
        return bits
    
    def getPosition(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, 2, 0x3FFF, length)
        self.position = bits * 0.1 # 0.1mm/bit
        
    def getCurrent(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, 1, 0x1FF, length)
        self.current = bits * 0.1 # 0.1A/bit
        
    def getSpeed(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, 4, 0x1F, length)
        self.speed = bits * 5 # 5%/bit
        
    def getVoltageError(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, 2, 0x3, length)
        self.voltageError = int(bits)   
        
    def getTempError(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, 0, 0x3, length)
        self.tempError = int(bits)
       
    def getMotion(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, 7, 1, length)
        self.motion = bool(bits)
        
    def getOverload(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, 6, 1, length)
        self.overload = bool(bits)
        
    def getBackdrive(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, 5, 1, length)
        self.backdrive = bool(bits)
        
    def getParameter(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, 4, 1, length)
        self.parameter = bool(bits)

    def getSaturation(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, 3, 1, length)
        self.saturation = bool(bits)

    def getFatalError(self, data1, data2, start, length):
        bits = self.getBits(data1, data2, 2, 1, length)
        self.fatalError = bool(bits)
        
    def log(self):
        entry = DataFrame({"position" : [self.position],
                              "current" : [self.current],
                              "speed" : [self.speed],
                              "voltage error" : [self.voltageError],
                              "temp error" : [self.tempError],
                              "motion" : [self.motion],
                              "overload" : [self.overload], 
                              "back drive" : [self.backdrive],
                              "parameter" : [self.parameter],
                              "saturation" : [self.saturation],
                              "fatal error" : [self.fatalError],
                     }, dtype=str)
            
        self.record = self.record.append(entry, ignore_index=False)
        return entry
        
# Thomson Linear Electrac HD CAN J1939 Actuator Control Message Encoder
class ACM:
    def __init__(self, pos, spd):
        
        # ID
        self.pgn = 61184
        self.destAddr = 19
        self.srcAddr = 0 # random

        # Data
        self.position = int(pos)
        self.currentLim = 10
        self.speed = int(spd)
        self.motionEn = True
        
        # Logging
        self.record = DataFrame({"position" : [],
                              "current limit" : [],
                              "speed" : [],
                              "motion enable" : [],
                     }, dtype=str)
        self.logPath = "electrakhd_can_send" +time.strftime("%Y-%m-%d_%Hh%Mm%Ss", time.gmtime())

        # Dump of raw PDU's
        self.dump = open(self.logPath + ".txt", "w")
    
    def id(self):
        return (6 << 26) | (self.pgn << 8) | self.destAddr << 8 | self.srcAddr
    
    def positionScaled(self):
        return int(self.position / 0.1)
    
    def currentLimScaled(self):
        return int(self.currentLim / 0.1)
    
    def speedScaled(self):
        return int(round(self.speed / 5))
    
    def motionEnInt(self):
        return int(self.motionEn)
    
    def getBytes(self):
        data = bytearray([0, 0, 0, 0, 0, 0, 0, 0])
        data0 = reverse_bit((reverse_bit(self.positionScaled(), 14) >> 6) & 0xFF, 8)
        data1 = reverse_bit((reverse_bit(self.positionScaled(), 14) << 2 | reverse_bit(self.currentLimScaled(), 9) >> 7) & 0xFF, 8)
        data2 = reverse_bit((reverse_bit(self.currentLimScaled(), 9) << 1 | reverse_bit(self.speedScaled(), 5) >> 4) & 0xFF, 8)
        data3 = reverse_bit((reverse_bit(self.speedScaled(), 5) << 4 | self.motionEnInt() << 3) & 0xFF, 8)
        print(bin(reverse_bit(data3, 8)))
        
        data[0] = data0 & 0xFF
        data[1] = data1 & 0xFF
        data[2] = data2 & 0xFF
        data[3] = data3 & 0xFF

        return data
    
    def log(self):

        bytesStr = ""
        data = self.getBytes()
        for b in data:
            bytesStr += hex(b)[2:] + " "

        pdu = str(hex(self.id()))[2:] + " [" + str(len(data)) + "] " +  bytesStr
        self.dump.write(pdu)
        
        entry = DataFrame({"position" : [self.position],
                              "current limit" : [self.currentLim],
                              "speed" : [self.speed],
                              "motion enable" : [self.motionEn],
                     }, dtype=str)
            
        self.record = self.record.append(entry, ignore_index=False)
        return pdu, entry

