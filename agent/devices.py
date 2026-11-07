"""Device layer: one class per transport, same interface (read / set)."""
import json
import re
import threading
import time

import requests


class DeviceError(Exception):
    pass


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


class Device:
    def __init__(self, name: str, cfg: dict):
        self.name = name
        self.cfg = cfg
        self.channels = cfg.get("channels", {})
        self.names = {norm(name)} | {norm(a) for a in cfg.get("aliases", [])}

    def read(self) -> dict:
        raise NotImplementedError

    def _send_set(self, channel: str, value: int) -> str:
        raise NotImplementedError

    def set(self, channel: str, value) -> str:
        """Validate against the whitelist in config.yaml, then send."""
        ch = self.channels.get(channel)
        if not ch or ch.get("kind") != "output":
            allowed = [c for c, v in self.channels.items() if v.get("kind") == "output"]
            raise DeviceError(f"'{channel}' is not an allowed output on {self.name}. Allowed: {allowed}")
        if ch.get("type") == "digital":
            v = str(value).strip().lower()
            if v in ("1", "on", "true", "high", "yes"):
                value = 1
            elif v in ("0", "off", "false", "low", "no"):
                value = 0
            else:
                raise DeviceError(f"digital output needs on/off, got {value!r}")
        else:
            lo, hi = ch.get("min", 0), ch.get("max", 255)
            value = max(lo, min(hi, int(float(value))))
        return self._send_set(channel, value)


class HttpDevice(Device):
    def __init__(self, name, cfg):
        super().__init__(name, cfg)
        self.addr = cfg["address"].rstrip("/")

    def _get(self, path, **params):
        try:
            r = requests.get(self.addr + path, params=params, timeout=3)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            raise DeviceError(f"{self.name} unreachable at {self.addr}: {e}")

    def read(self):
        return self._get("/read").json()

    def _send_set(self, channel, value):
        return self._get("/set", name=channel, value=value).text.strip()


class SerialDevice(Device):
    def __init__(self, name, cfg):
        super().__init__(name, cfg)
        self.ser = None
        self.lock = threading.Lock()

    def _ensure(self):
        if self.ser and self.ser.is_open:
            return
        import serial
        try:
            self.ser = serial.Serial(self.cfg["port"], self.cfg.get("baud", 115200), timeout=2)
        except serial.SerialException as e:
            raise DeviceError(f"{self.name}: cannot open {self.cfg['port']}: {e}")
        time.sleep(2)  # Arduino resets when the port opens
        self.ser.reset_input_buffer()

    def _xfer(self, line: str) -> str:
        with self.lock:
            self._ensure()
            self.ser.write((line + "\n").encode())
            resp = self.ser.readline().decode(errors="ignore").strip()
        if not resp:
            raise DeviceError(f"{self.name}: no response (is the firmware flashed?)")
        return resp

    def read(self):
        return json.loads(self._xfer("READ"))

    def _send_set(self, channel, value):
        return self._xfer(f"SET {channel} {value}")


class MockDevice(Device):
    """Simulated board for testing without hardware (--mock)."""

    def __init__(self, name, cfg):
        super().__init__(name, cfg)
        self.state = {c: 0 for c, v in self.channels.items() if v.get("kind") == "output"}

    def read(self):
        import random
        return {"mock": True, "temp_c": round(random.uniform(22, 26), 1),
                "a0": random.randint(0, 1023), "uptime_s": int(time.time()) % 100000,
                **{f"{k}_state": v for k, v in self.state.items()}}

    def _send_set(self, channel, value):
        self.state[channel] = value
        return f"OK (mock) {channel}={value}"


def load_devices(cfg: dict, mock: bool = False) -> dict:
    out = {}
    for name, c in cfg.items():
        t = "mock" if mock else c.get("transport")
        if t == "mock":
            out[name] = MockDevice(name, c)
        elif t == "http":
            out[name] = HttpDevice(name, c)
        elif t == "serial":
            out[name] = SerialDevice(name, c)
        else:
            raise ValueError(f"device {name}: unknown transport {t!r}")
    return out
