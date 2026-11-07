"""Smart Agent: local LLM (Ollama) + STT/TTS controlling ESP32 / ESP-01S / Arduino / RP2040.

Usage:
  python agent/main.py --text            # keyboard instead of microphone
  python agent/main.py --text --mock     # simulated boards, no hardware needed
  python agent/main.py                   # voice: press Enter, then speak
  python agent/main.py --profile home    # GTX 1650 laptop settings
  python agent/main.py --device arduino  # start with a different active MCU

In the prompt you can also type:  /use <device>   /devices   /quit
"""
import argparse
import json
import re
from pathlib import Path

import ollama
import yaml

from devices import DeviceError, load_devices, norm

ROOT = Path(__file__).resolve().parent.parent

TOOLS = [
    {"type": "function", "function": {
        "name": "select_device",
        "description": "Choose which microcontroller later commands use by default.",
        "parameters": {"type": "object", "properties": {
            "device": {"type": "string", "description": "esp32, esp01s, arduino or rp2040"}},
            "required": ["device"]}}},
    {"type": "function", "function": {
        "name": "read_sensors",
        "description": "Read all sensor values from a microcontroller.",
        "parameters": {"type": "object", "properties": {
            "device": {"type": "string", "description": "Optional; defaults to the active device"}}}}},
    {"type": "function", "function": {
        "name": "set_output",
        "description": "Set an output on a microcontroller: turn led/relay on or off, or set pwm 0-255.",
        "parameters": {"type": "object", "properties": {
            "channel": {"type": "string", "description": "led, relay or pwm"},
            "value": {"type": "string", "description": "on/off for digital, 0-255 for pwm"},
            "device": {"type": "string", "description": "Optional; defaults to the active device"}},
            "required": ["channel", "value"]}}},
]


class Agent:
    HW_RE = re.compile(
        r"\b(turn|switch|set|read|sensors?|readings?|led|leds|relay|pwm|brightness|device|devices|"
        r"board|mcu|esp\w*|arduino|pico|rp2040|uno|nano|temperature|light|lights|fan|toggle)\b", re.I)

    def __init__(self, cfg, profile, start_device=None, mock=False):
        self.cfg = cfg
        self.model = cfg["profiles"][profile]["model"]
        self.devices = load_devices(cfg["devices"], mock)
        self.active = start_device or cfg.get("default_device") or next(iter(self.devices))
        self.history = []

    # ---- device resolution ----
    def resolve(self, name=None):
        if not name:
            return self.devices[self.active]
        n = norm(name)
        for d in self.devices.values():
            if n in d.names:
                return d
        raise DeviceError(f"Unknown device '{name}'. Known: {list(self.devices)}")

    # ---- tools ----
    def run_tool(self, name, args):
        try:
            if name == "select_device":
                d = self.resolve(args.get("device"))
                self.active = d.name
                return f"Active device is now {d.name}."
            if name == "read_sensors":
                d = self.resolve(args.get("device"))
                return json.dumps({"device": d.name, **d.read()})
            if name == "set_output":
                d = self.resolve(args.get("device"))
                return f"{d.name}: {d.set(args['channel'], args['value'])}"
            return f"Unknown tool {name}"
        except DeviceError as e:
            return f"ERROR: {e}"
        except Exception as e:  # bad args from the model, etc.
            return f"ERROR: {type(e).__name__}: {e}"

    def system_prompt(self):
        lines = []
        for d in self.devices.values():
            outs = [c for c, v in d.channels.items() if v.get("kind") == "output"]
            lines.append(f"- {d.name} ({d.cfg['transport']}): outputs {outs}")
        return (
            "You are a voice assistant that controls microcontrollers. Your replies are spoken aloud, "
            "so keep them to one or two short sentences with no markdown.\n"
            f"Active device: {self.active}. Devices:\n" + "\n".join(lines) + "\n"
            "For greetings and general-knowledge questions, answer directly from your own knowledge "
            "and do not use tools. Use the tools only to read sensors or change outputs. Never claim "
            "an action succeeded unless the tool result says so. If the user names a device, pass it "
            "as the device argument."
        )

    # ---- chat loop ----
    def ask(self, text):
        self.history.append({"role": "user", "content": text})
        self.history = self.history[-24:]
        # Small models call tools even for "hello"; only offer them for hardware-sounding requests.
        tools = TOOLS if self.HW_RE.search(text) else None
        for _ in range(4):  # max tool rounds
            msgs = [{"role": "system", "content": self.system_prompt()}] + self.history
            resp = ollama.chat(model=self.model, messages=msgs, tools=tools)
            m = resp.message
            self.history.append(m)
            if not m.tool_calls:
                return (m.content or "").strip()
            for call in m.tool_calls:
                fn = call.function
                result = self.run_tool(fn.name, dict(fn.arguments or {}))
                print(f"  [tool] {fn.name}({dict(fn.arguments or {})}) -> {result}")
                self.history.append({"role": "tool", "tool_name": fn.name, "content": result})
        return "Sorry, I could not finish that."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=str(ROOT / "config.yaml"))
    ap.add_argument("--profile", help="office or home (default from config.yaml)")
    ap.add_argument("--device", help="initial active MCU")
    ap.add_argument("--model", help="override the Ollama model")
    ap.add_argument("--text", action="store_true", help="type instead of speaking")
    ap.add_argument("--no-tts", action="store_true")
    ap.add_argument("--mock", action="store_true", help="simulate all boards (no hardware needed)")
    a = ap.parse_args()

    cfg = yaml.safe_load(open(a.config, encoding="utf-8"))
    profile = a.profile or cfg["profile"]
    agent = Agent(cfg, profile, a.device, a.mock)
    if a.model:
        agent.model = a.model

    listener = speaker = None
    if not a.text:
        from voice import Listener
        print("Loading speech model...")
        listener = Listener(cfg["profiles"][profile]["whisper"])
    if not a.no_tts:
        from voice import Speaker
        speaker = Speaker(cfg["tts"]["rate"])

    print(f"Profile: {profile} | model: {agent.model} | active device: {agent.active}")
    print("Commands: /use <device>, /devices, /quit")

    while True:
        try:
            if a.text:
                text = input("you> ").strip()
            else:
                input("[Enter] then speak...")
                print("listening...")
                text = listener.listen()
                print(f"you> {text}")
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text == "/quit":
            break
        if text == "/devices":
            print(", ".join(agent.devices), f"(active: {agent.active})")
            continue
        if text.startswith("/use "):
            try:
                agent.active = agent.resolve(text[5:].strip()).name
                print(f"active device: {agent.active}")
            except DeviceError as e:
                print(e)
            continue
        try:
            reply = agent.ask(text)
        except Exception as e:
            reply = f"LLM error: {e}"
        print(f"agent> {reply}")
        if speaker:
            speaker.say(reply)


if __name__ == "__main__":
    main()
