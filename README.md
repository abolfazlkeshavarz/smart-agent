# Smart Agent

A local, offline voice assistant that controls microcontrollers. You speak (or type); a small
language model running in [Ollama](https://ollama.com) decides what to do and calls tools that
read sensors or switch outputs on an **ESP32, ESP-01S, Arduino or RP2040**. Replies are spoken back.
It also answers general questions, and it can be fine-tuned on your own data.

```
 mic -> faster-whisper (STT) -> Ollama LLM (llama3.2:3b) -> tools -> ESP32 / ESP-01S  (Wi-Fi, HTTP)
                                      ^                           -> Arduino / RP2040 (USB serial)
                                      '-- sensor data / results --'
 speaker <- pyttsx3 (TTS) <- reply text
```

## Features

- Choose which board to control: start flag, `/use <device>`, or just say "switch to the pico".
- Three tools for the model: `select_device`, `read_sensors`, `set_output`.
- Safety: only outputs listed in the config can be set, PWM is clamped to 0-255, relays boot OFF.
- `--mock` mode simulates all boards, so you can test with no hardware.
- Fully local: no cloud API, no internet needed at run time.
- Optional LoRA fine-tuning pipeline (dataset generators, Colab notebook, Ollama import, evaluation).

## Repository layout

| Path | What it is |
|---|---|
| `agent/main.py` | The agent: Ollama tool-calling loop, device selection, CLI |
| `agent/devices.py` | Device layer: HTTP, serial and mock transports, output whitelist |
| `agent/voice.py` | Speech-to-text (faster-whisper) and text-to-speech (pyttsx3) |
| `config.yaml` | Office/Windows config: model profiles, devices, channels |
| `config.home.yaml` | Home/Arch Linux config (Linux serial ports) |
| `firmware/` | Sketches: `esp32_http`, `esp01s_http`, `serial_node` (Arduino + RP2040) |
| `training/` | Dataset generators, Colab notebook, Ollama import and evaluation scripts |
| `docs/` | Setup, hardware, training and troubleshooting guides |

## Quick start

1. Install [Ollama](https://ollama.com) and pull the model:
   ```
   ollama pull llama3.2:3b
   ```
2. Create a Python environment and install dependencies (Python 3.10+):
   ```
   python -m venv .venv
   ```
   Activate it (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` on Linux), then:
   ```
   pip install -r requirements.txt
   ```
3. Try it with simulated boards (no hardware):
   ```
   python agent/main.py --text --mock
   ```
4. Flash a board and set its address in the config: see [docs/HARDWARE.md](docs/HARDWARE.md).
5. Run for real:
   ```
   python agent/main.py --text            # type commands
   python agent/main.py                   # voice: press Enter, then speak
   ```

Full per-OS instructions (Windows and Arch Linux): [docs/SETUP.md](docs/SETUP.md).

## Using it

Examples (typed or spoken):

- "Turn on the LED." / "Turn the relay off on the ESP32."
- "Switch to the Arduino and set PWM to 128." / "Set PWM to 50 percent."
- "What are the sensor readings on the pico?"
- General questions: "What is PWM?" (no tool is used)

Prompt commands: `/use <device>`, `/devices`, `/quit`.

| Flag | Meaning |
|---|---|
| `--text` | Type instead of speaking |
| `--mock` | Simulate all boards |
| `--device NAME` | Start with this board active |
| `--profile office\|home` | Pick model/whisper settings from the config |
| `--model NAME` | Override the Ollama model (e.g. a fine-tuned one) |
| `--config PATH` | Use another config file (e.g. `config.home.yaml`) |
| `--no-tts` | Do not speak replies |

## Configuration

`config.yaml` has three parts: `profiles` (LLM and Whisper model per machine), `tts`, and `devices`.
Each device has a `transport` (`http` with an `address`, or `serial` with a `port`), optional spoken
`aliases`, and `channels`. A channel is an allowed output (`kind: output`, `type: digital|pwm`).
Anything not listed is rejected before it reaches a board.

## Fine-tuning (optional)

The base `llama3.2:3b` sometimes misuses tools. This repo can generate about 2,400 training examples
(hardware commands, errors, general chat and personal facts), fine-tune with LoRA on a free Colab GPU,
and import the result back into Ollama. See [docs/TRAINING.md](docs/TRAINING.md).

## Privacy

The training data in `training/` (`generate_personal.py`, `all_*.jsonl`) contains personal information:
education details, grades, projects and preferences. **Keep this repository private**, or delete those
files and `generate_personal.py` before making it public. Wi-Fi credentials are never stored in the repo:
edit the `YOUR_WIFI` / `YOUR_PASSWORD` placeholders in the firmware locally and do not commit them.

## Known limitations

- Wake word is not implemented: press Enter, then speak.
- No rules/automation ("turn on the fan above 28 degrees"); the agent only acts on request.
- Small models make mistakes: do not use this to control anything dangerous, and add hard limits in firmware.
- Ollama's `gemma3` models do not support tool calling, so use `llama3.2:3b` (or `qwen2.5:3b`) for control.

## Documentation

- [docs/SETUP.md](docs/SETUP.md): install on Windows and Arch Linux
- [docs/HARDWARE.md](docs/HARDWARE.md): boards, wiring, firmware, protocols, adding sensors
- [docs/TRAINING.md](docs/TRAINING.md): dataset, Colab, import, evaluation
- [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md): common errors and fixes
