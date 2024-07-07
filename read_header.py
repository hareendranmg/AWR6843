import serial
import struct
import logging
import time

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
            print(data)  # Print the response from the device for debugging purposes

    # Send the final command
    data_bytes = "configDataPort 921600 1".encode("utf-8")
    config_ser.write(data_bytes)
    print("Configuration complete.")


# Configure logging

logging.basicConfig(
    filename="app.log",
    filemode="w",
    format="%(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG,
)


# Constants
MAGIC_WORD = b"\x02\x01\x04\x03\x06\x05\x08\x07"
FRAME_HEADER_LENGTH = 40


def decode_version(version):
    major = (version >> 24) & 0xFF
    minor = (version >> 16) & 0xFF
    bugfix = (version >> 8) & 0xFF
    build = version & 0xFF
    return f"{major:02d}.{minor:02d}.{bugfix:02d}.{build:02d}"


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


def print_frame_header(header):
    logging.info(
        "-----------------------Start Frame Header ---------------------------:"
    )
    logging.info(f"  Magic Word: {header['magic_word'].hex()}")
    decoded_version = decode_version(header["version"])
    logging.info(f"  Version: {header['version']} (decoded: {decoded_version})")
    logging.info(f"  Total Packet Length: {header['total_packet_length']} bytes")
    logging.info(f"  Platform: 0x{header['platform']:X}")
    logging.info(f"  Frame Number: {header['frame_number']}")
    logging.info(f"  Time [CPU Cycles]: {header['time_cpu_cycles']}")
    logging.info(f"  Number of Detected Objects: {header['num_detected_obj']}")
    logging.info(f"  Number of TLVs: {header['num_tlvs']}")
    logging.info(f"  Subframe Number: {header['subframe_number']}")
    logging.info(
        "-----------------------End Frame Header -----------------------------:"
    )


def read_data():
    buffer = b""
    while True:
        byte_count = data_ser.inWaiting()
        if byte_count > 0:
            new_data = data_ser.read(byte_count)
            buffer += new_data
            while len(buffer) >= len(MAGIC_WORD):
                start_index = buffer.find(MAGIC_WORD)
                if start_index != -1:
                    if len(buffer) >= start_index + FRAME_HEADER_LENGTH:
                        header_data = buffer[
                            start_index : start_index + FRAME_HEADER_LENGTH
                        ]
                        frame_header = parse_frame_header(header_data)
                        if frame_header:
                            print_frame_header(frame_header)
                        buffer = buffer[start_index + FRAME_HEADER_LENGTH :]
                    else:
                        break
                else:
                    buffer = buffer[1:]


if __name__ == "__main__":
    try:
        logging.info("Starting to read frame headers...")
        read_data()
    except KeyboardInterrupt:
        logging.info("Program interrupted by user.")
    except Exception as e:
        logging.exception("An error occurred:")
    finally:
        data_ser.close()
        logging.info("Serial port closed.")
