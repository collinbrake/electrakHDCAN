import time
from datetime import datetime
import can
import os
import argparse
import math
from pandas import DataFrame

from util import reverse_bit

# Thomson Linear Electrac HD CAN J1939 Actuator Feedback Message Decoder
class AFM:
    def __init__(self):
        
        # ID
        self.PGN = 0 # assume there are other ECU's on the bus, no real filtering implimented yet
        
        # Flag stating that this entry is valid
        self.valid = False

        # Data
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
        
    def reset(self):
        self = AFM()
        
    def get(self, message):
        self.getPGN(message.arbitration_id)
        if self.PGN == 126720:
            self.getPosition(message.data[0], message.data[1], 0, 14)
            self.getCurrent(message.data[1], message.data[2], 6, 9)
            self.getBackdrive(message.data[4], None, 2, 1)
            self.getParameter(message.data[4], None, 3, 1)
            self.getSaturation(message.data[4], None, 4, 1)
            self.getFatalError(message.data[4], None, 5, 1)
        else:
            self.reset()
            
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
        
# Thomson Linear Electrac HD CAN J1939 Actuator Control Message Encoder
class ACM:
    def __init__(self, pos, speed):
        
        # ID
        self.pgn = 61184
        self.destAddr = 19
        self.srcAddr = 0 # random

        # Data
        self.position = pos
        self.currentLim = 10
        self.speed = speed
        self.motionEn = True
        
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
        
        data[0] = data0 & 0xFF
        data[1] = data1 & 0xFF
        data[2] = data2 & 0xFF
        data[3] = data3 & 0xFF

        return data
class ActuatorManager:
    def __init__(self, logEn=True):
        self.logEn = logEn

        if self.logEn:
            self.binaryLog = DataFrame({"C ID" : [],
                                        "C B1" : [],
                                        "C B2" : [],
                                        "C B3" : [],
                                        "C B4" : [],
                                        "C B5" : [],
                                        "C B6" : [],
                                        "C B7" : [],
                                        "C B8" : [],

                                        "F ID" : [],
                                        "F B1" : [],
                                        "F B2" : [],
                                        "F B3" : [],
                                        "F B4" : [],
                                        "F B5" : [],
                                        "F B6" : [],
                                        "F B7" : [],
                                        "F B8" : [],
                                }, dtype=str)
            self.valueLog = DataFrame({ "time" : [],
                                    "C position" : [],
                                    "C speed" : [],
                                    "C current max" : [],
                                    
                                    "F position" : [],
                                    "F speed" : [],
                                    "F current" : [],
                                    "F voltage err" : [],
                                    "F temp err" : [],
                                    "F motion" : [],
                                    "F overload" : [],
                                    "F backdrive" : [],
                                    "F backdrive" : [],
                                    "F parameter" : [],
                                    "F saturation" : [],
                                    "F fatal err" : [],
                            }, columns = ["time",
                                    "C position",
                                    "C speed",
                                    "C current max",
                                    "F position",
                                    "F speed",
                                    "F current",
                                    "F voltage err",
                                    "F temp err",
                                    "F motion",
                                    "F overload",
                                    "F backdrive",
                                    "F parameter",
                                    "F saturation",
                                    "F fatal err"], dtype=str)
        
            timeStr = time.strftime("%Y-%m-%d_%Hh%Mm%Ss", time.gmtime()) 
            self.valueLogPath = "electrakhd_can_data_fields_" + timeStr + ".csv"
            self.binaryLogPath = "electrakhd_can_bytes_" + timeStr + ".csv"

        self.afm = AFM()
        self.acm = ACM(0, 0)
        self.t_0 = datetime.now()
        
    def bringupCAN(self, port="/dev/ttyACM0", iface="can0"):
        self.port = port
        self.iface = iface
        
        # Bringup can interface
        # TODO add exceptions and perhaps retry
        os.system("sudo slcand -o -c -s5 " + port + " " + iface)
        os.system("sudo ifconfig can0 up")
        os.system("sudo ifconfig can0 txqueuelen 1000")
        self.bus = can.interface.Bus(iface, bustype='socketcan')
        
    # interface is responsible for sending and recieving exactly one message with the
    # actuator. The value log is returned. The sent message is given as a function arguments.
    # If logging is enabled it will log the messages both in binary and decoded form.
    def interface(self, acm):
        
        feedback = self.bus.recv(0.1)
        if feedback:
            self.afm.get(feedback)
        else:
            self.afm.reset()

        self.acm = acm
        data = self.acm.getBytes()
        self.bus.send(can.Message(arbitration_id=self.acm.id(), is_extended_id=True, data=data))
        
        binaryLogEntry = DataFrame({"C ID" : [self.acm.id()],
                                        "C B1" : [data[0]],
                                        "C B2" : [data[1]],
                                        "C B3" : [data[2]],
                                        "C B4" : [data[3]],
                                        "C B5" : [data[4]],
                                        "C B6" : [data[5]],
                                        "C B7" : [data[6]],
                                        "C B8" : [data[7]],
                                }, dtype=str)

        valueLogEntry = DataFrame({ "time" : [(datetime.now() - self.t_0).total_seconds()],
                                    "C position" : [self.acm.position],
                                    "C speed" : [self.acm.speed],
                                    "C current max" : [self.acm.currentLim],
                                    
                                    "F position" :  [self.afm.position],
                                    "F speed" :     [self.afm.speed],
                                    "F current" :   [self.afm.current],
                                    "F voltage err" : [self.afm.voltageError],
                                    "F temp err" : [self.afm.tempError],
                                    "F motion" : [self.afm.motion],
                                    "F overload" : [self.afm.overload],
                                    "F backdrive" : [self.afm.backdrive],
                                    "F parameter" : [self.afm.parameter],
                                    "F saturation" : [self.afm.saturation],
                                    "F fatal err" : [self.afm.fatalError],
                            }, columns = ["time",
                                    "C position",
                                    "C speed",
                                    "C current max",
                                    "F position",
                                    "F speed",
                                    "F current",
                                    "F voltage err",
                                    "F temp err",
                                    "F motion",
                                    "F overload",
                                    "F backdrive",
                                    "F parameter",
                                    "F saturation",
                                    "F fatal err"], dtype=str)
            
        self.valueLog = self.valueLog.append(valueLogEntry, ignore_index=True)
        self.binaryLog = self.binaryLog.append(binaryLogEntry, ignore_index=True)
        
        return valueLogEntry
        
    def saveLogs(self):
        if self.logEn:
            if not os.path.exists("log/"):
                os.system("mkdir log/")
            self.valueLog.to_csv("log/" + self.valueLogPath)
            self.binaryLog.to_csv("log/" + self.binaryLogPath)