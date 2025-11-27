
import serial
import time

# ---------------------------
#  Utility Functions
# ---------------------------

def open_uart(port="/dev/ttyUSB0", baud=115200):
    """Open UART interface."""
    ser = serial.Serial(
        port=port,
        baudrate=baud,
        timeout=1,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )
    print(f"[INFO] Opened {port} at {baud} baud")
    return ser


def send_hci(ser, hex_string):
    """
    Send an HCI command given a space-separated hex string, e.g. "01 03 0C 00".
    """
    data = bytes.fromhex(hex_string)
    print(f"[TX] {hex_string}")
    ser.write(data)
    time.sleep(0.05)

    # Optional: attempt to read the event response
    resp = ser.read(64)
    if resp:
        print("[RX]", resp.hex(" ").upper())
    else:
        print("[RX] (no response)")


# ---------------------------
#  HCI Command Wrappers
# ---------------------------

def hci_reset(ser):
    send_hci(ser, "01 03 0C 00")


def hci_le_transmitter_test(ser, channel, payload_type):
    """
    channel: 0–39
    payload_type:
        00 = PRBS9
        01 = 11110000 repeating
        02 = 10101010 repeating
    """
    hex_str = f"01 1E 20 03 {channel:02X} 25 {payload_type:02X}"
    send_hci(ser, hex_str)


def hci_le_receiver_test(ser, channel):
    """
    channel: 0–39
    """
    hex_str = f"01 1D 20 01 {channel:02X}"
    send_hci(ser, hex_str)


def hci_le_test_end(ser):
    send_hci(ser, "01 1F 20 00")


# ---------------------------
#  Example Usage
# ---------------------------

if __name__ == "__main__":
    ser = open_uart("/dev/ttyUSB0", 115200)

    # Example: Reset EUT
    hci_reset(ser)
    time.sleep(1)

    # Example: Transmitter Test on channel 20 with PRBS9 pattern
    hci_le_transmitter_test(ser, channel=20, payload_type=0x00)
    time.sleep(5)

    # Example: End test
    hci_le_test_end(ser)

    ser.close()
    print("[INFO] Closed UART")
