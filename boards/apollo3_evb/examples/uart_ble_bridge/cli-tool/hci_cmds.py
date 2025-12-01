
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


CMD_TO_PAYLOAD_VAL_MAP = {
    "LE_PRBS9": 0x00,
    "LE_11110000": 0x01,
    "LE_10101010": 0x02,
    "cont_carrier": 0x08,
    "cont_mod": 0x09
}

CHANNEL_TO_MHZ_MAP = {
    0: 2402,
    1: 2404,
    2: 2406,
    3: 2408,
    4: 2410,
    5: 2412,
    6: 2414,
    7: 2416,
    8: 2418,
    9: 2420,
    10: 2422,
    11: 2424,
    12: 2426,
    13: 2428,
    14: 2430,
    15: 2432,
    16: 2434,
    17: 2436,
    18: 2438,
    19: 2440,
    20: 2442,
    21: 2444,
    22: 2446,
    23: 2448,
    24: 2450,
    25: 2452,
    26: 2454,
    27: 2456,
    28: 2458,
    29: 2460,
    30: 2462,
    31: 2464,
    32: 2466,
    33: 2468,
    34: 2470,
    35: 2472,
    36: 2474,
    37: 2476,
    38: 2478,
    39: 2480
}

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
    parser.add_argument("--channel", type=int, choices=range(0, 40), help="Channel number: 0-39 for TX or RX tests")
    parser.add_argument("--channel_list", type=str, help="Comma separated list of channels for TX or RX tests (overrides --channel)")
    parser.add_argument("--channel_all", action="store_true", help="Uses all channels for TX or RX tests (overrides --channel and --channel_list)")
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

    # Process channel arguments
    if args.channel is None and args.channel_list is None and args.channel_all is None:
        print("Invalid/missing arguments...")
        parser.print_help()
        print(command_help)
        exit(1)

    if args.channel_all:
        channels = list(range(0, 40))
    elif args.channel_list:
        try:
            channels = [int(ch.strip()) for ch in args.channel_list.split(",") if 0 <= int(ch.strip()) <= 39]
            if not channels:
                raise ValueError
        except ValueError:
            print("Invalid channel list. Please provide a comma-separated list of integers between 0 and 39.")
            exit(1)
    else:
        channels = [args.channel]

    # Open UART
    ser = open_uart(args.port, 115200)

    print("[INFO] Test start")
    for ch in channels:
        # Reset BLE module before each test
        print("Sending reset to BLE module...")
        hci_reset(ser, args.print_uart)

        print(f"Running {args.cmd} on channel {ch} ({CHANNEL_TO_MHZ_MAP.get(ch)} MHz) for {args.duration_ms} ms")
        if args.cmd == "rx_test":
            hci_le_receiver_test(ser, ch, args.print_uart)
        else:
            hci_le_transmitter_test(ser, ch, CMD_TO_PAYLOAD_VAL_MAP.get(args.cmd), args.print_uart)

        # Run test for specified duration
        time.sleep(args.duration_ms / 1000)

        # End test (in case of continuous carrier, do not send reset as it crashes the BLE module)
        if(args.cmd != "cont_carrier"):
            hci_le_test_end(ser, args.print_uart)

    # Reset BLE module after all tests
    print("Sending final reset to BLE module...")
    hci_reset(ser, args.print_uart)

    print("[INFO] Test end")
    ser.close()
