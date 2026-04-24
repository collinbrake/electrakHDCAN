import time
from datetime import datetime
import can
import os
import subprocess
from pandas import DataFrame

from util import reverse_bit

# Thomson Linear Electrac HD CAN J1939 Actuator Feedback Message Decoder
class AFM:
    def __init__(self):
        self.id = []
        self.data = [0, 0, 0, 0, 0, 0, 0, 0]
        self.reset()
        
    def reset(self):
        self.PGN = 0
        self.valid = False
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
        self.id = []
        self.data = [0, 0, 0, 0, 0, 0, 0, 0]
        
    def get(self, message):
        self.id = message.arbitration_id
        self.data = message.data
        self.getPGN(message.arbitration_id)
        if self.PGN == 126720:
            self.getPosition(message.data[0], message.data[1], 14)
            self.getCurrent(message.data[1], message.data[2], 9)
            self.getSpeed(message.data[2], message.data[3], 5)
            self.getBackdrive(message.data[4], None, 1)
            self.getParameter(message.data[4], None, 1)
            self.getSaturation(message.data[4], None, 1)
            self.getFatalError(message.data[4], None, 1)
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
        if data2 is not None:
            data = data << 8 | reverse_bit(data2, 8)

        bits = reverse_bit((data >> shft) & mask, length) # this line is to account for reverse bit order specified in electrak manual
        return bits
    
    def getPosition(self, data1, data2, length):
        bits = self.getBits(data1, data2, 2, 0x3FFF, length)
        self.position = bits * 0.1 # 0.1mm/bit
        
    def getCurrent(self, data1, data2, length):
        bits = self.getBits(data1, data2, 1, 0x1FF, length)
        self.current = bits * 0.1 # 0.1A/bit
        
    def getSpeed(self, data1, data2, length):
        bits = self.getBits(data1, data2, 4, 0x1F, length)
        self.speed = bits * 5 # 5%/bit
        
    def getVoltageError(self, data1, data2, length):
        bits = self.getBits(data1, data2, 2, 0x3, length)
        self.voltageError = int(bits)   
        
    def getTempError(self, data1, data2, length):
        bits = self.getBits(data1, data2, 0, 0x3, length)
        self.tempError = int(bits)
       
    def getMotion(self, data1, data2, length):
        bits = self.getBits(data1, data2, 7, 1, length)
        self.motion = bool(bits)
        
    def getOverload(self, data1, data2, length):
        bits = self.getBits(data1, data2, 6, 1, length)
        self.overload = bool(bits)
        
    def getBackdrive(self, data1, data2, length):
        bits = self.getBits(data1, data2, 5, 1, length)
        self.backdrive = bool(bits)
        
    def getParameter(self, data1, data2, length):
        bits = self.getBits(data1, data2, 4, 1, length)
        self.parameter = bool(bits)

    def getSaturation(self, data1, data2, length):
        bits = self.getBits(data1, data2, 3, 1, length)
        self.saturation = bool(bits)

    def getFatalError(self, data1, data2, length):
        bits = self.getBits(data1, data2, 2, 1, length)
        self.fatalError = bool(bits)
        
# Thomson Linear Electrac HD CAN J1939 Actuator Control Message Encoder
class ACM:
    def __init__(self, pos, speed):
        
        # ID
        self.pgn = 61184
        self.destAddr = 35
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
        pos = self.positionScaled()     # 14-bit, starts at bit 0
        cur = self.currentLimScaled()   #  9-bit, starts at bit 14
        spd = self.speedScaled()        #  5-bit, starts at bit 23
        mot = self.motionEnInt()        #  1-bit, starts at bit 28

        # Pack fields as a plain little-endian 32-bit word.
        combined = (pos & 0x3FFF) | ((cur & 0x1FF) << 14) | ((spd & 0x1F) << 23) | (mot << 28)

        data[0] = (combined) & 0xFF
        data[1] = (combined >> 8) & 0xFF
        data[2] = (combined >> 16) & 0xFF
        data[3] = (combined >> 24) & 0xFF
        
        # TODO set all other to 255?

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
                                }, columns = ["C ID",
                                              "C B1",
                                              "C B2",
                                              "C B3",
                                              "C B4",
                                              "C B5",
                                              "C B6",
                                              "C B7",
                                              "C B8",
                                              
                                              "F ID",
                                              "F B1",
                                              "F B2",
                                              "F B3",
                                              "F B4",
                                              "F B5",
                                              "F B6",
                                              "F B7",
                                              "F B8",
                                              ], dtype=str)
            
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
        
    def bringupCAN(self, port=None, iface="can0", interface="socketcan", bringup=None):
        self.port = port
        self.iface = iface
        self.interfaceType = interface

        if bringup is None:
            bringup = port is not None
        
        if bringup:
            if port is None:
                raise ValueError("A serial CAN adapter port is required when bringup=True")

            subprocess.run(["sudo", "slcand", "-o", "-c", "-s5", port, iface], check=True)
            subprocess.run(["sudo", "ip", "link", "set", iface, "up"], check=True)
            subprocess.run(["sudo", "ip", "link", "set", iface, "txqueuelen", "1000"], check=True)

        self.bus = can.Bus(interface=interface, channel=iface)
        
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
                                        
                                        "F ID" : [self.afm.id],
                                        "F B1" : [self.afm.data[0]],
                                        "F B2" : [self.afm.data[1]],
                                        "F B3" : [self.afm.data[2]],
                                        "F B4" : [self.afm.data[3]],
                                        "F B5" : [self.afm.data[4]],
                                        "F B6" : [self.afm.data[5]],
                                        "F B7" : [self.afm.data[6]],
                                        "F B8" : [self.afm.data[7]],

                                }, columns = ["C ID",
                                              "C B1",
                                              "C B2",
                                              "C B3",
                                              "C B4",
                                              "C B5",
                                              "C B6",
                                              "C B7",
                                              "C B8",
                                              
                                              "F ID",
                                              "F B1",
                                              "F B2",
                                              "F B3",
                                              "F B4",
                                              "F B5",
                                              "F B6",
                                              "F B7",
                                              "F B8",
                                              ], dtype=str)

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
            
        if self.logEn:
            self.valueLog.loc[len(self.valueLog)] = valueLogEntry.iloc[0].to_dict()
            self.binaryLog.loc[len(self.binaryLog)] = binaryLogEntry.iloc[0].to_dict()
        
        return valueLogEntry
        
    def saveLogs(self):
        if self.logEn:
            if not os.path.exists("log/"):
                os.system("mkdir log/")
            self.valueLog.to_csv("log/" + self.valueLogPath)
            self.binaryLog.to_csv("log/" + self.binaryLogPath)

    def shutdown(self):
        if hasattr(self, "bus"):
            self.bus.shutdown()