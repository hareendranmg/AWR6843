import serial
import time

# Serial port configurations
config_ser = serial.Serial("com11", 115200)
data_ser = serial.Serial("com12", 921600)
# config_ser = serial.Serial("com14", 115200)
# data_ser = serial.Serial("com15", 921600)

# Frame storage
frames = []


def send_config():
    with open("config.txt", "r") as file:
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


def read_data():
    buffer = b""
    frame_start = (
        b"\x02\x01\x04\x03\x06\x05\x08\x07"  # Example frame start, adjust as necessary
    )
    frame_length = 512  # Example frame length, adjust as necessary

    while True:
        byteCount = data_ser.inWaiting()
        if byteCount > 0:
            buffer += data_ser.read(byteCount)

            while len(buffer) >= frame_length:
                # Check for the frame start
                start_index = buffer.find(frame_start)
                if start_index != -1:
                    # Check if the full frame is available
                    if len(buffer) >= start_index + frame_length:
                        # Extract the frame
                        frame = buffer[start_index : start_index + frame_length]
                        frames.append(frame)
                        print("Frame received and stored.")
                        # Remove the processed frame from the buffer
                        buffer = buffer[start_index + frame_length :]
                    else:
                        break
                else:
                    # No valid frame start found, discard part of the buffer
                    buffer = buffer[-len(frame_start) :]


if __name__ == "__main__":
    try:
        print("Sending configuration to radar sensor...")
        send_config()
        print("Starting to read data...")
        read_data()
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    finally:
        config_ser.close()
        data_ser.close()
        print("Serial ports closed.")
        print(f"Total frames received: {len(frames)}")
        # print frames for debugging purposes
        for frame in frames:
            print(frame.hex())
            print(
                "---------------------------------------------------------------------------------"
            )
