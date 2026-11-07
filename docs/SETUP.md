# Setup

## Requirements

- Python 3.10 or newer
- [Ollama](https://ollama.com) with `llama3.2:3b`
- A microphone and speakers for voice mode (not needed with `--text`)
- A GPU is optional. CPU-only works, with replies taking a few seconds. A 4 GB GPU (GTX 1650) fits the 3B model.

## Windows

1. Install Ollama from ollama.com, open it, then in PowerShell:
   ```
   ollama pull llama3.2:3b
   ```
2. In the project folder:
   ```
   python -m venv .venv
   ```
   ```
   .venv\Scripts\activate
   ```
   ```
   pip install -r requirements.txt
   ```
3. Test:
   ```
   python agent/main.py --text --mock
   ```
4. Serial ports are `COM3`, `COM5`, ... Check them in Device Manager > Ports, then edit `config.yaml`.
   Close the Arduino IDE serial monitor before running the agent: it locks the port.

## Arch Linux (home laptop with GTX 1650)

Arch blocks system-wide `pip install`, so use a virtual environment.

1. Packages (`ollama-cuda` needs the NVIDIA driver, `nvidia` or `nvidia-open`):
   ```
   sudo pacman -S python espeak-ng portaudio ollama-cuda
   ```
   ```
   sudo systemctl enable --now ollama
   ```
   ```
   ollama pull llama3.2:3b
   ```
2. Python environment:
   ```
   python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
   ```
3. Serial access: on Arch the group is `uucp`. Log out and in again afterwards.
   ```
   sudo usermod -aG uucp $USER
   ```
4. Find each board's port with only that board plugged in:
   ```
   ls /dev/ttyACM* /dev/ttyUSB*
   ```
   Put the ports in `config.home.yaml` (Uno and Pico are usually `/dev/ttyACM*`, CH340 clones `/dev/ttyUSB*`).
5. Run:
   ```
   python agent/main.py --config config.home.yaml --text
   ```

## Model profiles

`profile:` in the config picks the model and Whisper size. Defaults:

| Profile | LLM | Whisper |
|---|---|---|
| `office` (CPU) | `llama3.2:3b` | `base.en` |
| `home` (GTX 1650) | `llama3.2:3b` | `small.en` |

Switch with `--profile home`, or override the model with `--model NAME`.
Voice mode downloads the Whisper model on first run (about a minute).

## First-run checklist

1. `ollama list` shows `llama3.2:3b`.
2. `python agent/main.py --text --mock` answers "hello" and "turn on the led".
3. A flashed board answers (see [HARDWARE.md](HARDWARE.md)).
4. Voice mode: press Enter, speak, stop; it ends recording after about one second of silence.
