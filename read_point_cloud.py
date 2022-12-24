import serial
import time

ser = serial.Serial('/dev/ttyUSB0', 115200)

with open('config.txt', 'r') as file:
    for line in file:
        print("_______________")
        print(line)
        data_bytes = line.encode('utf-8')
        ser.write(data_bytes)
        time.sleep(0.1)
        data  = ser.read_until("\r".encode('utf-8'))
        data = data.strip(b'\n\r').decode()
        print(data)
        print("_______________")



# while True:
    # try:
        # data = ser.readline()
        # print(data)
    # except Exception as e:
        # print(e)
