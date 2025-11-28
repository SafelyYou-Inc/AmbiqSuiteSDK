
import serial
import time
import argparse

# ---------------------------
#  Utility Functions
# ---------------------------

def open_uart(port, baud):
    """Open UART interface."""
    ser = serial.Serial(
        port=port,
        baudrate=baud,
        timeout=1,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )
    print(f"[INFO] Opened {port}")
    return ser


def send_hci(ser, hex_string, print_uart=False):
    """
    Send an HCI command given a space-separated hex string, e.g. "01 03 0C 00".
    """
    data = bytes.fromhex(hex_string)
    if print_uart:
        print(f"[TX] {hex_string}")
    ser.write(data)
    time.sleep(0.05)

    # Optional: attempt to read the event response
    resp = ser.read(64)
    if print_uart:
        if resp:
            print("[RX]", resp.hex(" ").upper())
        else:
            print("[RX] (no response)")

# ---------------------------
#  HCI Command Wrappers
# ---------------------------

def hci_reset(ser, print_uart=False):
    send_hci(ser, "01 03 0C 00", print_uart)


def hci_le_transmitter_test(ser, channel, payload_type, print_uart=False):
    """
    channel: 0–39
    payload_type:
        00 = LE test packets with PRBS9 in payload
        01 = LE test packets with repeated '11110000' sequence in payload
        02 = LE test packets with repeated '10101010' sequence in payload
        08 = Continuous carrier wave mode at center frequency
        09 = Continuous modulation transmit mode with duty cycle = 100%
    """
    hex_str = f"01 1E 20 03 {channel:02X} 25 {payload_type:02X}"
    send_hci(ser, hex_str, print_uart)


def hci_le_receiver_test(ser, channel, print_uart=False):
    """
    channel: 0–39
    """
    hex_str = f"01 1D 20 01 {channel:02X}"
    send_hci(ser, hex_str, print_uart)


def hci_le_test_end(ser, print_uart=False):
    send_hci(ser, "01 1F 20 00", print_uart)


# ---------------------------
#  Main CLI Tool
# ---------------------------
if __name__ == "__main__":
    command_help = """
    Command information:
        LE_PRBS9      : LE transmitter test with PRBS9 payload
        LE_11110000   : LE transmitter test with repeated '11110000' sequence
        LE_10101010   : LE transmitter test with repeated '10101010' sequence
        cont_carrier  : Continuous carrier wave mode at center frequency
        cont_mod      : Continuous modulation transmit mode, duty cycle 100%
        rx_test       : LE receiver test"""
    parser = argparse.ArgumentParser(description="HCI UART CLI Tool", exit_on_error=False)
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0", help="UART port - Example: \"COM1\" (Windows) or \"/dev/ttyUSB0\" (Linux/macOS), default: /dev/ttyUSB0")
    parser.add_argument("--cmd", type=str, choices=["LE_PRBS9", "LE_11110000", "LE_10101010", "cont_carrier", "cont_mod", "rx_test"], required=True, help="Command to execute (required)")
    parser.add_argument("--channel", type=int, choices=range(0, 40), required=True, help="Channel number: 0-39 for TX or RX tests (required)")
    parser.add_argument("--duration_ms", type=int, default=5000, help="Test duration in milliseconds - default: 5000 ms")
    parser.add_argument("--print_uart", action="store_true", help="Print UART TX/RX data")

    try:
        args = parser.parse_args()
    # Handle -h/--help manually to show command extra information
    except SystemExit:
        print(command_help)
        exit(0)
    # Handle errors manually to show command extra information
    except argparse.ArgumentError:
        print("Invalid/missing arguments...")
        parser.print_help()
        print(command_help)
        exit(1)

    # Open UART
    ser = open_uart(args.port, 115200)

    # Reset EUT
    print("Resetting device...")
    hci_reset(ser, args.print_uart)
    time.sleep(0.25)

    print(f"Running {args.cmd} on channel {args.channel} for {args.duration_ms} ms")
    if args.cmd == "rx_test":
        hci_le_receiver_test(ser, args.channel, args.print_uart)
    else:
        cmd_payload_map = {
            "LE_PRBS9": 0x00,
            "LE_11110000": 0x01,
            "LE_10101010": 0x02,
            "cont_carrier": 0x08,
            "cont_mod": 0x09
        }
        hci_le_transmitter_test(ser, args.channel, cmd_payload_map.get(args.cmd), args.print_uart)
    time.sleep(args.duration_ms / 1000)

    # End test
    print("Ending test...")
    hci_le_test_end(ser, args.print_uart)

    ser.close()
