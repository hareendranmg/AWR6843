import serial
import time
import codecs



config_ser = serial.Serial('/dev/ttyUSB0', 115200)
data_ser = serial.Serial('/dev/ttyUSB1', 921600)


def send_config():
    with open('config.txt', 'r') as file:
        for line in file:
            data_bytes = line.encode('utf-8')
            config_ser.write(data_bytes)
            time.sleep(0.1)
            data  = config_ser.read_until("\r".encode('utf-8'))
            data = data.strip(b'\n\r').decode()

        data_bytes = 'configDataPort 921600 1'.encode('utf-8')
        config_ser.write(data_bytes)


def read_data():
    while True:
        # data  = data_ser.read_until("\r".encode('utf-8'))
        data  = data_ser.readline()
        decoded_data = ''
        try:
            decoded_data = data.decode('utf-8')
        except UnicodeDecodeError:
            # If the UTF-8 codec fails, try using the ASCII codec
            try:
                decoded_data = data.decode('ascii')
            except UnicodeDecodeError:
                # If the ASCII codec also fails, try using the UTF-16 codec
                try:
                    decoded_data = data.decode('utf-16')
                except UnicodeDecodeError:
                    # If all codecs fail, print an error message
                    print('Error: unable to decode byte string')

        print(decoded_data)

        time.sleep(0.1)



send_config()
print('send config done')
read_data()