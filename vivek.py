import serial
import struct
import time

count = 1

packet = {"tlv": []}

totalFrameBitcount = 0
frameBitCount = 0


def checkIfValidPacketStart(header):
    magicWord = ["02", "01", "04", "03", "06", "05", "08", "07"]
    for i in range(0, 8):
        if magicWord[i] != header[i]:
            return False

    return True


def concatenate_strings(string_list):
    # Use the join method to concatenate all strings in the list
    concatenated_string = "".join(string_list)
    return concatenated_string


def hex_to_float(hex_string):
    # Convert hex string to bytes
    bytes_value = bytes.fromhex(hex_string)

    # Unpack bytes to a float (assuming IEEE 754 format for float32)
    float_value = struct.unpack("!f", bytes_value)[0]
    return float_value


config_ser = serial.Serial("com11", 115200)
data_ser = serial.Serial("com12", 921600)


def send_config():
    with open("vivek_config.txt", "r") as file:
        for line in file:
            data_bytes = line.encode("utf-8")
            config_ser.write(data_bytes)
            time.sleep(0.1)
            data = config_ser.read_until("\r".encode("utf-8"))
            data = data.strip(b"\n\r").decode()
            print(data)  # Print the response from the device for debugging purposes

    # Send the final command
    data_bytes = "configDataPort 921600 1".encode("utf-8")
    config_ser.write(data_bytes)
    print("Configuration complete.")


send_config()
time.sleep(0.5)

try:
    while True:
        while count:
            byteCount = data_ser.inWaiting()
            if byteCount > 0:
                s = data_ser.read(byteCount)
                inHex = s.hex()

                print(inHex)

                headLst = []
                tlvLst = []

                if totalFrameBitcount == 0:
                    for i in range(0, len(inHex[:80]), 2):
                        headLst.append(inHex[i] + "" + inHex[i + 1])
                    for i in range(80, len(inHex), 2):
                        tlvLst.append(inHex[i] + "" + inHex[i + 1])

                    if checkIfValidPacketStart(headLst) == False:
                        continue

                    packet["header"] = headLst
                    packet["tlv"] = tlvLst
                    sub_array = headLst[12:16]
                    sub_array.reverse()
                    combined_hex = "".join(sub_array)
                    totalFrameBitcount = int(combined_hex, 16)
                    frameBitCount = len(s)
                else:
                    tlvLst = packet["tlv"]
                    for i in range(0, len(inHex), 2):
                        tlvLst.append(inHex[i] + "" + inHex[i + 1])

                    packet["tlv"] = tlvLst
                    frameBitCount += len(s)

                if totalFrameBitcount <= frameBitCount:
                    count = 0

        # print(packet['tlv'][:4])

        tlv = packet["tlv"]

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
        print((xPosM**2 + yPosM**2 + zPosM**2) ** (0.5))
        # print(packet['tlv'])
        totalFrameBitcount = 0
        frameBitCount = 0
        count = 1
        packet["tlv"] = []
except Exception as e:
    print(e)
    data_ser.close()
    config_ser.close()
    print("Port Closed")
    pass
