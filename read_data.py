import serial
import struct
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
MAGIC_WORD = b"\x02\x01\x04\x03\x06\x05\x08\x07"
FRAME_HEADER_LENGTH = 40
TLV_HEADER_LENGTH = 8

# Serial port configurations
config_ser = serial.Serial("com11", 115200)
data_ser = serial.Serial("com12", 921600)


def send_config():
    with open("config.txt", "r") as file:
        for line in file:
            data_bytes = line.encode("utf-8")
            config_ser.write(data_bytes)
            time.sleep(0.1)
            data = config_ser.read_until("\r".encode("utf-8"))
            data = data.strip(b"\n\r").decode()
            logging.debug(f"Config response: {data}")
    data_bytes = "configDataPort 921600 1".encode("utf-8")
    config_ser.write(data_bytes)
    # logging.info("Configuration complete.")


def parse_frame_header(data):
    if len(data) < FRAME_HEADER_LENGTH:
        logging.error(
            f"Insufficient data for frame header. Expected {FRAME_HEADER_LENGTH} bytes, got {len(data)} bytes."
        )
        return None

    try:
        magic_word = data[:8]
        version = struct.unpack("<I", data[8:12])[0]
        total_packet_length = struct.unpack("<I", data[12:16])[0]
        platform = struct.unpack("<I", data[16:20])[0]
        frame_number = struct.unpack("<I", data[20:24])[0]
        time_cpu_cycles = struct.unpack("<I", data[24:28])[0]
        num_detected_obj = struct.unpack("<I", data[28:32])[0]
        num_tlvs = struct.unpack("<I", data[32:36])[0]
        subframe_number = struct.unpack("<I", data[36:40])[0]
    except struct.error as e:
        logging.error(f"Error unpacking frame header: {e}")
        logging.debug(f"Received data: {data.hex()}")
        return None

    return {
        "magic_word": magic_word,
        "version": version,
        "total_packet_length": total_packet_length,
        "platform": platform,
        "frame_number": frame_number,
        "time_cpu_cycles": time_cpu_cycles,
        "num_detected_obj": num_detected_obj,
        "num_tlvs": num_tlvs,
        "subframe_number": subframe_number,
    }


def parse_tlv_header(data):
    if len(data) < TLV_HEADER_LENGTH:
        logging.error(
            f"Insufficient data for TLV header. Expected {TLV_HEADER_LENGTH} bytes, got {len(data)} bytes."
        )
        return None

    try:
        tlv_type, tlv_length = struct.unpack("<II", data[:TLV_HEADER_LENGTH])
    except struct.error as e:
        logging.error(f"Error unpacking TLV header: {e}")
        return None

    return {"type": tlv_type, "length": tlv_length}


def process_tlv(tlv_type, tlv_data):
    # logging.info(f"Processing TLV type {tlv_type}, length {len(tlv_data)} bytes")

    if tlv_type == 1:  # Detected objects
        num_objects = len(tlv_data) // 16  # Assuming each object is 16 bytes
        for i in range(num_objects):
            x, y, z, velocity = struct.unpack("<ffff", tlv_data[i * 16 : (i + 1) * 16])
            logging.info(
                f"Object {i}: X: {x:.2f}, Y: {y:.2f}, Z: {z:.2f}, Velocity: {velocity:.2f}"
            )

    elif tlv_type == 2:  # Range profile
        # Process range profile data
        pass

    elif tlv_type == 3:  # Noise profile
        # Process noise profile data
        pass

    elif tlv_type == 4:  # Azimuth static heat map
        # Process azimuth heat map data
        pass

    elif tlv_type == 5:  # Range-Doppler heat map
        # Process range-Doppler heat map data
        pass

    else:
        logging.warning(f"Unknown TLV type: {tlv_type}")


def process_frame(frame, frame_header):
    # logging.info(f"Processing frame {frame_header['frame_number']}")
    # logging.info(f"Number of detected objects: {frame_header['num_detected_obj']}")
    # logging.info(f"Number of TLVs: {frame_header['num_tlvs']}")

    offset = FRAME_HEADER_LENGTH
    for _ in range(frame_header["num_tlvs"]):
        if offset + TLV_HEADER_LENGTH > len(frame):
            logging.error("Insufficient data for TLV header")
            break

        tlv_header = parse_tlv_header(frame[offset:])
        if tlv_header is None:
            break

        offset += TLV_HEADER_LENGTH

        if offset + tlv_header["length"] > len(frame):
            logging.error("Insufficient data for TLV payload")
            break

        tlv_data = frame[offset : offset + tlv_header["length"]]
        process_tlv(tlv_header["type"], tlv_data)

        offset += tlv_header["length"]


def read_data():
    buffer = b""
    while True:
        byteCount = data_ser.inWaiting()
        if byteCount > 0:
            new_data = data_ser.read(byteCount)
            buffer += new_data
            while len(buffer) >= len(MAGIC_WORD):
                start_index = buffer.find(MAGIC_WORD)
                if start_index != -1:
                    if len(buffer) >= start_index + FRAME_HEADER_LENGTH:
                        header_data = buffer[
                            start_index : start_index + FRAME_HEADER_LENGTH
                        ]
                        frame_header = parse_frame_header(header_data)
                        if frame_header is None:
                            buffer = buffer[start_index + len(MAGIC_WORD) :]
                            continue

                        total_length = frame_header["total_packet_length"]

                        if len(buffer) >= start_index + total_length:
                            frame = buffer[start_index : start_index + total_length]
                            process_frame(frame, frame_header)
                            buffer = buffer[start_index + total_length :]
                        else:
                            break
                    else:
                        break
                else:
                    buffer = buffer[1:]


if __name__ == "__main__":
    try:
        # logging.info("Sending configuration to radar sensor...")
        send_config()
        # logging.info("Starting to read data...")
        read_data()
    except KeyboardInterrupt:
        logging.info("Program interrupted by user.")
    except Exception as e:
        logging.exception("An error occurred:")
    finally:
        config_ser.close()
        data_ser.close()
        # logging.info("Serial ports closed.")
