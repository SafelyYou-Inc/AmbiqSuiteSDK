# UART to BLE bridge FW

## Getting Started
### Setup the build container
```bash
docker build -t ble-bridge-builder:latest -f Dockerfile .
```

## Compile firmware
```bash
TOP_LEVEL="$(git rev-parse --show-toplevel)"
docker run -it --rm -v "${TOP_LEVEL}:/${TOP_LEVEL}:Z" --workdir=$(pwd) ble-bridge-builder:latest make
```

Firmware will be `gcc/bin/uart_ble_bridge.bin`