import serial
import struct
import time


comPort = 'com15'
# comPort = '/dev/ttyUSB1'

count = 1

packet = {'tlv':[]}

totalFrameBitcount = 0
frameBitCount = 0


def checkIfValidPacketStart(header):
    magicWord = ['02', '01', '04', '03', '06', '05', '08', '07']
    for i in range(0, 8):
        if(magicWord[i] != header[i]):
            return False

    return True

def concatenate_strings(string_list):
    # Use the join method to concatenate all strings in the list
    concatenated_string = ''.join(string_list)
    return concatenated_string

def hex_to_float(hex_string):
    # Convert hex string to bytes
    bytes_value = bytes.fromhex(hex_string)

    # Unpack bytes to a float (assuming IEEE 754 format for float32)
    float_value = struct.unpack('!f', bytes_value)[0]
    return float_value

def serialConfig():

    configFileName = 'config.txt'
    global CLIport

    CLIport = serial.Serial('com14', 115200)
    # CLIport = serial.Serial('/dev/ttyUSB0', 115200)

    config = [line.rstrip('\r\n') for line in open(configFileName)]
    for i in config:
        CLIport.write((i+'\n').encode())
        time.sleep(0.01)

    print('-------------------Configuration is done-------------------')


serialConfig()
time.sleep(0.5)
ser = serial.Serial(comPort, 921600)

while True:
    while count:
        byteCount = ser.inWaiting()
        if(byteCount > 0):
            s = ser.read(byteCount)
            inHex = s.hex()

            headLst = []
            tlvLst = []

            if(totalFrameBitcount == 0):
                for i in range(0,len(inHex[:80]),2):
                    headLst.append(inHex[i]+''+inHex[i+1])
                for i in range(80,len(inHex),2):
                    tlvLst.append(inHex[i]+''+inHex[i+1])

                if(checkIfValidPacketStart(headLst) == False):
                    continue

                packet['header'] = headLst
                packet['tlv'] = tlvLst
                sub_array = headLst[12:16]
                sub_array.reverse()
                combined_hex = ''.join(sub_array)
                totalFrameBitcount = int(combined_hex, 16)
                frameBitCount = len(s)
            else:
                tlvLst = packet['tlv']
                for i in range(0,len(inHex),2):
                    tlvLst.append(inHex[i]+''+inHex[i+1])

                packet['tlv'] = tlvLst
                frameBitCount += len(s)

            if(totalFrameBitcount <= frameBitCount):
                count = 0

    print(packet['tlv'][:4])

    tlv = packet['tlv']

    xPos = tlv[8:12]
    yPos = tlv[12:16]
    zPos = tlv[16:20]
    velo = tlv[20:24]

    xPos.reverse()
    yPos.reverse()
    zPos.reverse()
    velo.reverse()

    xPosVal = concatenate_strings(xPos)
    yPosVal = concatenate_strings(yPos)
    zPosVal = concatenate_strings(zPos)
    veloVal = concatenate_strings(velo)

    xPosM = hex_to_float(xPosVal)
    yPosM = hex_to_float(yPosVal)
    zPosM = hex_to_float(zPosVal)
    veloM = hex_to_float(veloVal)


    # print(veloM)
    # print(str(xPosM) +','+ str(yPosM) +','+ str(zPosM))
    print((xPosM**2 + yPosM**2 + zPosM**2)**(0.5))
    # print(packet['tlv'])
    totalFrameBitcount = 0
    frameBitCount = 0
    count = 1
    packet['tlv'] = []

