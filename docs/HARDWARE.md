# Hardware guide

| Board | Link | Sketch | Core / board package |
|---|---|---|---|
| ESP32 | Wi-Fi, HTTP | `firmware/esp32_http/esp32_http.ino` | "esp32" by Espressif |
| ESP-01S | Wi-Fi, HTTP | `firmware/esp01s_http/esp01s_http.ino` | "esp8266" by ESP8266 Community |
| Arduino (Uno/Nano) | USB serial | `firmware/serial_node/serial_node.ino` | built in |
| RP2040 (Pico) | USB serial | `firmware/serial_node/serial_node.ino` | "Raspberry Pi Pico/RP2040" by Earle Philhower (arduino-pico) |

Install the board packages in the Arduino IDE (Boards Manager) before flashing.

## Flashing the Wi-Fi boards (ESP32, ESP-01S)

1. Open the sketch and set `WIFI_SSID` and `WIFI_PASS`. Do not commit your real credentials.
2. Upload, then open the serial monitor at 115200 baud.
3. Copy the printed `IP address` into `address:` for that device in the config (e.g. `http://192.168.1.50`).
   Give the board a fixed IP (DHCP reservation in your router) so it does not change.
4. The PC and the board must be on the same network.

ESP-01S needs a USB-to-serial adapter. To flash it, pull GPIO0 LOW at power-up. For normal running GPIO0
and GPIO2 must be HIGH at boot, so do not hold them LOW.

## Pins and behaviour

| Board | LED | Relay | Sensors reported by `read` |
|---|---|---|---|
| ESP32 | GPIO 2 | GPIO 26 | `chip_temp_c` (internal), `adc34`, `rssi`, `uptime_s` |
| ESP-01S | GPIO 2 (active LOW) | GPIO 0 (active LOW) | `rssi`, `free_heap`, `uptime_s` |
| Arduino / RP2040 | `LED_BUILTIN` | pin 7 | `a0`, `a1`, `uptime_s`; PWM on pin 9 |

- The ESP32 temperature is the chip's internal temperature, not the room.
- Relays start OFF. Set `RELAY_ACTIVE_LOW` in the sketch to match your relay module.
- Change the pin `#define`s at the top of each sketch to match your wiring.
- Do not switch mains voltage from a breadboard. Use a proper relay module and enclosure.

## Protocols

HTTP (ESP32, ESP-01S):

```
GET /read                       -> {"rssi":-61,"uptime_s":120,...}
GET /set?name=led&value=1       -> OK
```

Serial, 115200 baud, newline-terminated (Arduino, RP2040):

```
READ                            -> {"a0":123,"a1":456,"uptime_s":12}
SET led 1                       -> OK
SET pwm 128                     -> OK
```

Test a board without the agent: `curl http://192.168.1.50/read` (HTTP), or the Arduino IDE serial monitor
with "Newline" line ending (serial). Close the serial monitor before running the agent.

## Serial ports

- Windows: `COM3`, `COM5` (Device Manager > Ports).
- Linux: `/dev/ttyACM0` (Uno, Pico) or `/dev/ttyUSB0` (CH340 clones). You need the `uucp` group on Arch, `dialout` on Debian/Ubuntu.

## Adding a sensor

1. Firmware: add a field to the JSON in `/read` (HTTP sketches) or `handleRead()` (serial sketch).
2. The agent shows every field to the model automatically. No agent change is needed.
3. To make the model answer natural questions about it ("what is the humidity?"), add examples to
   `training/generate_dataset.py` (the `sensors()`, `READ_BASE` and `read_answer()` parts) and retrain.

## Adding an output

1. Firmware: add a branch for the new name in the set handler (`handleSet`).
2. Config: add it under the device's `channels` (`kind: output`, `type: digital` or `pwm`).
   Anything not listed is rejected by the agent, even if the model asks for it.
3. Add the spoken name in `CHS` and examples in `training/generate_dataset.py` if you retrain.

## Adding a new board

Add a device block to the config with a `transport` (`http` or `serial`), `channels`, and `aliases`.
Use the same HTTP or serial protocol as above in its firmware. For another transport (MQTT, BLE), add a
class next to `HttpDevice` and `SerialDevice` in `agent/devices.py` with `read()` and `_send_set()`.
