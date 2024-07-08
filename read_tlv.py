import serial
import struct
import logging
import time
import math
import os
import sys

# delete the log file if it exists
if os.path.exists("radar_data.log"):
    os.remove("radar_data.log")

# Configure logging
logging.basicConfig(
    filename="radar_data.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Constants
MAGIC_WORD = b"\x02\x01\x04\03\x06\x05\x08\x07"
FRAME_HEADER_LENGTH = 40
TLV_HEADER_LENGTH = 8

config_ser = None
data_ser = None


def send_config():
    global config_ser
    with open("config.txt", "r") as file:
        for line in file:
            data_bytes = line.encode("utf-8")
            config_ser.write(data_bytes)
            time.sleep(0.01)
            data = config_ser.read_until("\r".encode("utf-8"))
            data = data.strip(b"\n\r").decode()
            print(data)  # Print the response from the device for debugging purposes

    # Send the final command
    data_bytes = "configDataPort 921600 1".encode("utf-8")
    config_ser.write(data_bytes)
    print("Configuration complete.")


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
        header = struct.unpack("<8sIIIIIIII", data[:FRAME_HEADER_LENGTH])
        return {
            "magic_word": header[0],
            "version": header[1],
            "total_packet_length": header[2],
            "platform": header[3],
            "frame_number": header[4],
            "time_cpu_cycles": header[5],
            "num_detected_obj": header[6],
            "num_tlvs": header[7],
            "subframe_number": header[8],
        }
    except struct.error as e:
        logging.error(f"Error unpacking frame header: {e}")
        logging.debug(f"Received data: {data.hex()}")
        return None


def parse_tlv_header(data):
    if len(data) < TLV_HEADER_LENGTH:
        logging.error(
            f"Insufficient data for TLV header. Expected {TLV_HEADER_LENGTH} bytes, got {len(data)} bytes."
        )
        return None

    try:
        return struct.unpack("<II", data[:TLV_HEADER_LENGTH])
    except struct.error as e:
        logging.error(f"Error unpacking TLV header: {e}")
        return None


def parse_detected_points(data, num_points):
    points = []
    for i in range(num_points):
        point_data = data[i * 16 : (i + 1) * 16]
        try:
            x, y, z, velocity = struct.unpack("<ffff", point_data)
            # Convert x, y, z from meters to centimeters
            x, y, z = x * 100, y * 100, z * 100
            distance = math.sqrt(x**2 + y**2 + z**2)
            points.append(
                {"x": x, "y": y, "z": z, "velocity": velocity, "distance": distance}
            )
        except struct.error as e:
            pass
            # logging.error(f"Error unpacking point data: {e}")
    return points


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


def print_detected_points(points):
    logging.info("-----------------------Detected Points ---------------------------:")
    for i, point in enumerate(points):
        logging.info(
            f"  Point {i+1}: X: {point['x']:.2f} cm, Y: {point['y']:.2f} cm, Z: {point['z']:.2f} cm, "
            f"Velocity: {point['velocity']:.2f}, Distance: {point['distance']:.2f} cm"
        )
    logging.info(
        "-----------------------End Detected Points ---------------------------:"
    )


def read_data():
    global data_ser
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

                            # Process TLVs
                            tlv_start = start_index + FRAME_HEADER_LENGTH
                            for _ in range(frame_header["num_tlvs"]):
                                if len(buffer) >= tlv_start + TLV_HEADER_LENGTH:
                                    tlv_type, tlv_length = parse_tlv_header(
                                        buffer[
                                            tlv_start : tlv_start + TLV_HEADER_LENGTH
                                        ]
                                    )
                                    tlv_start += TLV_HEADER_LENGTH

                                    # log tlv_type
                                    logging.info(f"TLV Type: {tlv_type}")

                                    if tlv_type == 1:  # Detected Points
                                        points_data = buffer[
                                            tlv_start : tlv_start + tlv_length
                                        ]
                                        num_points = frame_header["num_detected_obj"]
                                        detected_points = parse_detected_points(
                                            points_data, num_points
                                        )
                                        print_detected_points(detected_points)

                                    tlv_start += tlv_length
                                else:
                                    break

                            buffer = buffer[
                                start_index + frame_header["total_packet_length"] :
                            ]
                        else:
                            buffer = buffer[start_index + len(MAGIC_WORD) :]
                    else:
                        break
                else:
                    buffer = buffer[1:]


def main():
    global config_ser, data_ser
    try:
        if len(sys.argv) < 2 or sys.argv[1] not in ["aop", "aopcb"]:
            print("Usage: python read_tlv.py [aop|aopcb]")
            return

        if sys.argv[1] == "aop":
            port1, port2 = "11", "12"
            # port1, port2 = "16", "17"
        else:
            port1, port2 = "13", "14"

        config_ser = serial.Serial(f"COM{port1}", 115200)
        data_ser = serial.Serial(f"COM{port2}", 921600)

        logging.info("Sending configuration to radar...")
        send_config()
        logging.info("Starting to read radar data...")
        read_data()
    except KeyboardInterrupt:
        logging.info("Program interrupted by user.")
    except Exception as e:
        logging.exception("An error occurred: " + str(e))
    finally:
        if config_ser:
            config_ser.write("sensorStop\n".encode("utf-8"))
            config_ser.close()
        if data_ser:
            data_ser.close()
        logging.info("Serial ports closed.")


if __name__ == "__main__":
    main()
