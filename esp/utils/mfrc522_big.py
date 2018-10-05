from machine import Pin, SPI
import time


class MFRC522(object):
    MI_OK = 0
    MI_NOTAGERR = 1
    MI_ERR = 2

    MAX_LEN = 16
    serNum = []

    def __init__(self):
        self.sck = Pin(0, Pin.OUT)
        self.mosi = Pin(2, Pin.OUT)
        self.miso = Pin(4)
        self.rst = Pin(5, Pin.OUT)
        self.cs = Pin(14, Pin.OUT)

        self.cs.value(1)
        self.rst.value(0)

        self.spi = SPI(baudrate=1000000, polarity=0, phase=0, sck=self.sck, mosi=self.mosi, miso=self.miso, firstbit=SPI.MSB)
        self.MFRC522_Init()

    def Write_MFRC522(self, addr, val):
        data = bytearray(2)
        data[0] = (addr << 1) & 0x7E
        data[1] = val
        self.cs.value(0)
        self.spi.write(data)
        self.cs.value(1)

    def Read_MFRC522(self, addr):
        data = bytearray(2)
        buf = bytearray(2)
        data[0] = ((addr << 1) & 0x7E) | 0x80
        data[1] = 0x00
        self.cs.value(0)
        self.spi.write_readinto(data, buf)
        self.cs.value(1)
        return buf[1]

    def MFRC522_Reset(self):
        self.Write_MFRC522(0x01, 0x0F)

    def SetBitMask(self, reg, mask):
        tmp = self.Read_MFRC522(reg)
        self.Write_MFRC522(reg, tmp | mask)

    def ClearBitMask(self, reg, mask):
        tmp = self.Read_MFRC522(reg)
        self.Write_MFRC522(reg, tmp & (~mask))

    def AntennaOn(self):
        temp = self.Read_MFRC522(0x14)
        if (~(temp & 0x03)):
            self.SetBitMask(0x14, 0x03)

    def AntennaOff(self):
        self.ClearBitMask(0x14, 0x03)

    def MFRC522_ToCard(self, command, sendData):
        backData = []
        backLen = 0
        status = self.MI_ERR
        irqEn = 0x00
        waitIRq = 0x00
        lastBits = None
        n = 0
        i = 0
        if command == 0x0E:
            irqEn = 0x12
            waitIRq = 0x10
        if command == 0x0C:
            irqEn = 0x77
            waitIRq = 0x30
        self.Write_MFRC522(0x02, irqEn | 0x80)
        self.ClearBitMask(0x04, 0x80)
        self.SetBitMask(0x0A, 0x80)
        self.Write_MFRC522(0x01, 0x00)
        while (i < len(sendData)):
            self.Write_MFRC522(0x09, sendData[i])
            i = i + 1
        self.Write_MFRC522(0x01, command)
        if command == 0x0C:
            self.SetBitMask(0x0D, 0x80)
        i = 2000
        while True:
            n = self.Read_MFRC522(0x04)
            i = i - 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & waitIRq)):
                break
        self.ClearBitMask(0x0D, 0x80)
        if i != 0:
            if (self.Read_MFRC522(0x06) & 0x1B) == 0x00:
                status = self.MI_OK
                if n & irqEn & 0x01:
                    status = self.MI_NOTAGERR
                if command == 0x0C:
                    n = self.Read_MFRC522(0x0A)
                    lastBits = self.Read_MFRC522(0x0C) & 0x07
                    if lastBits != 0:
                        backLen = (n - 1) * 8 + lastBits
                    else:
                        backLen = n * 8
                    if n == 0:
                        n = 1
                    if n > self.MAX_LEN:
                        n = self.MAX_LEN
                    i = 0
                    while i < n:
                        backData.append(self.Read_MFRC522(0x09))
                        i = i + 1
            else:
                status = self.MI_ERR
        return (status, backData, backLen)

    def MFRC522_Request(self, reqMode):
        status = None
        backBits = None
        TagType = []
        self.Write_MFRC522(0x0D, 0x07)
        TagType.append(reqMode)
        (status, backData, backBits) = self.MFRC522_ToCard(0x0C, TagType)
        if ((status != self.MI_OK) | (backBits != 0x10)):
            status = self.MI_ERR
        return (status, backBits)

    def MFRC522_Anticoll(self):
        backData = []
        serNumCheck = 0
        serNum = []
        self.Write_MFRC522(0x0D, 0x00)
        serNum.append(0x93)
        serNum.append(0x20)
        (status, backData, backBits) = self.MFRC522_ToCard(0x0C, serNum)
        if (status == self.MI_OK):
            i = 0
            if len(backData) == 5:
                while i < 4:
                    serNumCheck = serNumCheck ^ backData[i]
                    i = i + 1
                if serNumCheck != backData[i]:
                    status = self.MI_ERR
            else:
                status = self.MI_ERR
        return (status, backData)

    def CalulateCRC(self, pIndata):
        self.ClearBitMask(0x05, 0x04)
        self.SetBitMask(0x0A, 0x80)
        i = 0
        while i < len(pIndata):
            self.Write_MFRC522(0x09, pIndata[i])
            i = i + 1
        self.Write_MFRC522(0x01, 0x03)
        i = 0xFF
        while True:
            n = self.Read_MFRC522(0x05)
            i = i - 1
            if not ((i != 0) and not (n & 0x04)):
                break
        pOutData = []
        pOutData.append(self.Read_MFRC522(0x22))
        pOutData.append(self.Read_MFRC522(0x21))
        return pOutData

    def MFRC522_SelectTag(self, serNum):
        backData = []
        buf = []
        buf.append(0x93)
        buf.append(0x70)
        i = 0
        while i < 5:
            buf.append(serNum[i])
            i = i + 1
        pOut = self.CalulateCRC(buf)
        buf.append(pOut[0])
        buf.append(pOut[1])
        (status, backData, backLen) = self.MFRC522_ToCard(0x0C, buf)
        if (status == self.MI_OK) and (backLen == 0x18):
            print("Size: " + str(backData[0]))
            return backData[0]
        else:
            return 0

    def MFRC522_Auth(self, authMode, BlockAddr, Sectorkey, serNum):
        buff = []
        buff.append(authMode)
        buff.append(BlockAddr)
        i = 0
        while (i < len(Sectorkey)):
            buff.append(Sectorkey[i])
            i = i + 1
        i = 0
        while (i < 4):
            buff.append(serNum[i])
            i = i + 1
        (status, backData, backLen) = self.MFRC522_ToCard(0x0E, buff)
        if not (status == self.MI_OK):
            print("AUTH ERROR!!")
        if not (self.Read_MFRC522(0x08) & 0x08) != 0:
            print("AUTH ERROR(status2reg & 0x08) != 0")
        return status

    def MFRC522_Read(self, blockAddr):
        recvData = []
        recvData.append(0x30)
        recvData.append(blockAddr)
        pOut = self.CalulateCRC(recvData)
        recvData.append(pOut[0])
        recvData.append(pOut[1])
        (status, backData, backLen) = self.MFRC522_ToCard(0x0C, recvData)
        if not (status == self.MI_OK):
            print("Error while reading!")
        i = 0
        if len(backData) == 16:
            print("Sector " + str(blockAddr) + " " + str(backData))

    def MFRC522_Write(self, blockAddr, writeData):
        buff = []
        buff.append(0xA0)
        buff.append(blockAddr)
        crc = self.CalulateCRC(buff)
        buff.append(crc[0])
        buff.append(crc[1])
        (status, backData, backLen) = self.MFRC522_ToCard(0x0C, buff)
        if not (status == self.MI_OK) or not (backLen == 4) or not ((backData[0] & 0x0F) == 0x0A):
            status = self.MI_ERR
        print(str(backLen) + " backdata &0x0F == 0x0A " + str(backData[0] & 0x0F))
        if status == self.MI_OK:
            i = 0
            buf = []
            while i < 16:
                buf.append(writeData[i])
                i = i + 1
            crc = self.CalulateCRC(buf)
            buf.append(crc[0])
            buf.append(crc[1])
            (status, backData, backLen) = self.MFRC522_ToCard(0x0C, buf)
            if not (status == self.MI_OK) or not (backLen == 4) or not ((backData[0] & 0x0F) == 0x0A):
                print("Error while writing")
            if status == self.MI_OK:
                print("Data written")

    def MFRC522_Init(self):
        self.rst.value(1)
        self.MFRC522_Reset()
        time.sleep_ms(500)

        self.Write_MFRC522(0x2A, 0x8D)
        self.Write_MFRC522(0x2B, 0x3E)
        self.Write_MFRC522(0x2D, 30)
        self.Write_MFRC522(0x2C, 0)
        self.Write_MFRC522(0x15, 0x40)
        self.Write_MFRC522(0x11, 0x3D)

        self.AntennaOn()

    def MFRC522_DeInit(self):
        self.AntennaOff()

        self.cs.value(1)
        self.rst.value(0)
        self.spi.deinit()
