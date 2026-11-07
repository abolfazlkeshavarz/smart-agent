"""Generate the hardware fine-tuning dataset (chat + tool calls) as JSONL.

Run:  python training/generate_dataset.py
Out:  training/hardware_train.jsonl, training/hardware_eval.jsonl

Each line: {"messages": [...], "tools": [...]}   ("tools" is omitted for general-chat rows,
because at run time tools are only offered for hardware-sounding requests).
The system prompt and tool schema come from agent/main.py so the data matches runtime exactly.
Tool-result messages use {"role": "tool", "name": ..., "content": ...} (HF chat-template style).
"""
import json
import random
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
from main import Agent, TOOLS  # noqa: E402

cfg = yaml.safe_load(open(ROOT / "config.yaml", encoding="utf-8"))
agent = Agent(cfg, "office", mock=True)
DEVCFG = cfg["devices"]
DEVS = list(DEVCFG)
SPOKEN = {"esp32": "ESP32", "esp01s": "ESP-01S", "arduino": "Arduino", "rp2040": "RP2040"}
CHS = {"led": "LED", "relay": "relay", "pwm": "PWM"}
UNKNOWN_DEVICES = ["esp8266", "nodemcu", "teensy", "stm32", "raspberry pi", "arduino mega", "esp32 cam"]
UNKNOWN_THINGS = ["fan", "motor", "buzzer", "heater", "servo", "speaker", "pump"]
rng = random.Random(42)


# ---------- helpers ----------
def outs(d):
    return [c for c, v in DEVCFG[d]["channels"].items() if v.get("kind") == "output"]


def join_outs(chs):
    names = [CHS[c] for c in chs]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def names(d):
    return [SPOKEN[d], SPOKEN[d].lower(), d] + DEVCFG[d].get("aliases", [])


def nm(d):
    return rng.choice(names(d))


def cap(s):
    return s[0].upper() + s[1:]


def styl(t):
    """Randomly mimic typed-lowercase vs. speech-to-text capitalisation/punctuation."""
    k = rng.choice(["raw", "raw", "cap", "cap"])
    if k == "raw":
        return t
    q = t.split()[0].lower() in {"what", "who", "where", "which", "how", "is", "can", "do", "does", "why", "when"}
    return cap(t) + ("?" if q else ".")


def sysmsg(active):
    agent.active = active
    return {"role": "system", "content": agent.system_prompt()}


def exchange(user, calls, reply):
    """calls = [(tool_name, args, result_text)]; empty list = direct answer."""
    msgs = [{"role": "user", "content": user}]
    if calls:
        msgs.append({"role": "assistant", "content": "", "tool_calls": [
            {"type": "function", "function": {"name": n, "arguments": a}} for n, a, _ in calls]})
        msgs += [{"role": "tool", "name": n, "content": r} for n, _, r in calls]
    msgs.append({"role": "assistant", "content": reply})
    return msgs


def with_dev(base, d):
    s = rng.randrange(4)
    if s == 0:
        return f"{base} on the {d}"
    if s == 1:
        return f"{base} on {d}"
    if s == 2:
        return f"On the {d}, {base[0].lower() + base[1:]}"
    return f"{base} for the {d}"


def pick_target():
    """Return (active, dev, explicit). Implicit only when dev is the active device."""
    active = rng.choice(DEVS)
    if rng.random() < 0.5:
        return active, active, rng.random() < 0.35
    return active, rng.choice([d for d in DEVS if d != active]), True


def fmt_up(s):
    h, m = s // 3600, (s % 3600) // 60
    parts = []
    if h:
        parts.append(f"{h} hour{'s' if h != 1 else ''}")
    if m:
        parts.append(f"{m} minute{'s' if m != 1 else ''}")
    return " and ".join(parts) or "under a minute"


def error_case(dev, path):
    """(tool result text, spoken reply) for a transport failure."""
    D = SPOKEN[dev]
    c = DEVCFG[dev]
    if c["transport"] == "http":
        addr = c["address"]
        host = addr.split("//")[1]
        res = (f"ERROR: {dev} unreachable at {addr}: HTTPConnectionPool(host='{host}', port=80): "
               f"Max retries exceeded with url: {path} (Caused by ConnectTimeoutError('Connection to {host} "
               f"timed out. (connect timeout=3)'))")
        return res, f"I can't reach the {D}. Check that it's powered on and connected to Wi-Fi."
    port = c["port"]
    k = rng.choice(["missing", "busy", "silent"])
    if k == "missing":
        res = (f"ERROR: {dev}: cannot open {port}: could not open port '{port}': FileNotFoundError(2, "
               f"'The system cannot find the file specified.', None, 2)")
        return res, f"I can't find the {D} on {port}. Check that the USB cable is plugged in."
    if k == "busy":
        res = (f"ERROR: {dev}: cannot open {port}: could not open port '{port}': PermissionError(13, "
               f"'Access is denied.', None, 5)")
        return res, f"I can't open the {D}'s serial port. Close any other program using it, like the serial monitor."
    return (f"ERROR: {dev}: no response (is the firmware flashed?)",
            f"The {D} isn't responding. Make sure its firmware is flashed and the baud rate is 115200.")


# ---------- scenario generators: each returns (active, messages, with_tools) ----------
V_ON = ["turn on the {c}", "switch on the {c}", "turn the {c} on", "switch the {c} on", "enable the {c}",
        "please turn on the {c}", "can you turn on the {c}", "{c} on", "activate the {c}"]
V_OFF = ["turn off the {c}", "switch off the {c}", "turn the {c} off", "switch the {c} off", "disable the {c}",
         "please turn off the {c}", "can you turn off the {c}", "{c} off", "deactivate the {c}"]


def spoken_ch(ch):
    return rng.choice(["LED", "led"]) if ch == "led" else ch


def digital():
    active, dev, explicit = pick_target()
    ch = rng.choice([c for c in outs(dev) if c in ("led", "relay")])
    state = rng.choice(["on", "off"])
    base = rng.choice(V_ON if state == "on" else V_OFF).format(c=spoken_ch(ch))
    user = styl(with_dev(base, nm(dev)) if explicit else base)
    args = {"channel": ch, "value": state}
    if explicit:
        args["device"] = dev
    D, c = SPOKEN[dev], CHS[ch]
    if rng.random() < 0.1:
        res, reply = error_case(dev, f"/set?name={ch}&value={1 if state == 'on' else 0}")
    else:
        res = f"{dev}: OK"
        reply = cap(rng.choice([f"the {c} on the {D} is now {state}.", f"done. The {D} {c} is {state}.",
                                f"I turned the {c} {state} on the {D}.", f"okay, {D} {c} {state}."]))
    return active, exchange(user, [("set_output", args, res)], reply), True


def pwm():
    pool = [d for d in DEVS if "pwm" in outs(d)]
    active = rng.choice(DEVS)
    dev = active if active in pool and rng.random() < 0.5 else rng.choice([d for d in pool if d != active])
    explicit = dev != active or rng.random() < 0.35
    D = SPOKEN[dev]
    kind = rng.choice(["n", "n", "n", "pct", "word", "high", "neg"])
    if kind == "n":
        n = rng.randint(0, 255)
        base = rng.choice(["set pwm to {n}", "set the pwm to {n}", "pwm {n}", "set the brightness to {n}",
                           "set pwm value to {n}"]).format(n=n)
        val, reply = str(n), f"PWM on the {D} is set to {n}."
    elif kind == "pct":
        p = rng.choice([0, 10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90, 100])
        val = str(round(p * 255 / 100))
        base = rng.choice(["set pwm to {p} percent", "set the brightness to {p} percent", "pwm {p} percent"]).format(p=p)
        reply = f"PWM on the {D} is set to {p} percent, which is {val} out of 255."
    elif kind == "word":
        w, v = rng.choice([("half", 128), ("a quarter", 64), ("full", 255), ("max", 255), ("maximum", 255),
                           ("zero", 0), ("minimum", 0)])
        base = rng.choice(["set pwm to {w}", "set the brightness to {w}", "pwm {w}"]).format(w=w)
        val, reply = str(v), f"PWM on the {D} is set to {v}."
    elif kind == "high":
        n = rng.choice([256, 300, 500, 999, 1023, 1287, 4095, 5000])
        base = f"set pwm to {n}"
        val, reply = "255", f"PWM only goes up to 255, so I set the {D} to 255."
    else:
        n = rng.choice([1, 5, 20, 100])
        base = f"set pwm to minus {n}"
        val, reply = "0", f"PWM can't go below 0, so I set the {D} to 0."
    user = styl(with_dev(base, nm(dev)) if explicit else base)
    args = {"channel": "pwm", "value": val}
    if explicit:
        args["device"] = dev
    res = f"{dev}: OK"
    if rng.random() < 0.08:
        res, reply = error_case(dev, "")
    return active, exchange(user, [("set_output", args, res)], reply), True


def pwm_off():
    pool = [d for d in DEVS if "pwm" in outs(d)]
    active = rng.choice(pool)
    base = rng.choice(["turn off the pwm", "turn the pwm off", "switch off the pwm"])
    return active, exchange(styl(base), [("set_output", {"channel": "pwm", "value": "0"}, f"{active}: OK")],
                            f"PWM on the {SPOKEN[active]} is off."), True


def pwm_unsupported():
    pool = [d for d in DEVS if "pwm" not in outs(d)]
    active = rng.choice(DEVS)
    dev = active if active in pool and rng.random() < 0.6 else rng.choice([d for d in pool if d != active])
    explicit = dev != active or rng.random() < 0.35
    n = rng.randint(0, 255)
    base = f"set pwm to {n}"
    user = styl(with_dev(base, nm(dev)) if explicit else base)
    args = {"channel": "pwm", "value": str(n)}
    if explicit:
        args["device"] = dev
    res = f"ERROR: 'pwm' is not an allowed output on {dev}. Allowed: {outs(dev)}"
    reply = f"The {SPOKEN[dev]} doesn't have a PWM output. It only has {join_outs(outs(dev))}."
    return active, exchange(user, [("set_output", args, res)], reply), True


def sensors(dev):
    up = rng.randint(20, 400000)
    if dev == "esp32":
        return {"chip_temp_c": round(rng.uniform(30, 58), 1), "adc34": rng.randint(0, 4095),
                "rssi": rng.randint(-85, -40), "uptime_s": up}
    if dev == "esp01s":
        return {"rssi": rng.randint(-85, -40), "free_heap": rng.randint(20000, 45000), "uptime_s": up}
    return {"a0": rng.randint(0, 1023), "a1": rng.randint(0, 1023), "uptime_s": up}


READ_BASE = {
    "all": ["read the sensors", "what are the sensor readings", "get the readings", "show me the sensor values",
            "read sensors", "give me the sensor readings"],
    "temp": ["read the temperature", "what is the temperature reading", "get the temperature"],
    "wifi": ["read the wifi signal", "what is the wifi signal reading", "get the signal strength reading"],
    "uptime": ["read the uptime", "what does the uptime reading say", "get the uptime reading"],
    "analog": ["read the analog input", "what is the analog reading", "read a0"],
    "memory": ["read the free memory", "what is the memory reading"],
}


def read_answer(dev, kind, d):
    """Return (needs_tool_call, reply)."""
    D, http = SPOKEN[dev], DEVCFG[dev]["transport"] == "http"
    if kind == "all":
        if dev == "esp32":
            return True, (f"{D}: chip temperature {d['chip_temp_c']} degrees Celsius, ADC reading {d['adc34']}, "
                          f"Wi-Fi signal {d['rssi']} dBm, uptime {fmt_up(d['uptime_s'])}.")
        if dev == "esp01s":
            return True, (f"{D}: Wi-Fi signal {d['rssi']} dBm, {d['free_heap']} bytes of free memory, "
                          f"uptime {fmt_up(d['uptime_s'])}.")
        return True, f"{D}: A0 is {d['a0']}, A1 is {d['a1']}, uptime {fmt_up(d['uptime_s'])}."
    if kind == "temp":
        if dev == "esp32":
            return True, f"The {D}'s chip temperature is {d['chip_temp_c']} degrees Celsius."
        if dev == "esp01s":
            return True, f"The {D} has no temperature sensor. Its Wi-Fi signal is {d['rssi']} dBm."
        return True, f"The {D} has no temperature sensor. Analog A0 reads {d['a0']} and A1 reads {d['a1']}."
    if kind == "wifi":
        if http:
            return True, f"The {D}'s Wi-Fi signal is {d['rssi']} dBm."
        return False, f"The {D} has no Wi-Fi. It connects over USB serial."
    if kind == "uptime":
        return True, f"The {D} has been running for {fmt_up(d['uptime_s'])}."
    if kind == "analog":
        if dev == "esp32":
            return True, f"The {D}'s ADC on pin 34 reads {d['adc34']}."
        if dev == "esp01s":
            return False, f"The {D} doesn't report an analog input."
        return True, f"On the {D}, A0 reads {d['a0']} and A1 reads {d['a1']}."
    if dev == "esp01s":  # memory
        return True, f"The {D} has {d['free_heap']} bytes of free memory."
    return False, f"The {D} doesn't report free memory."


def read():
    active, dev, explicit = pick_target()
    kind = rng.choice(["all", "all", "all", "temp", "temp", "wifi", "uptime", "analog", "memory"])
    d = sensors(dev)
    needs, reply = read_answer(dev, kind, d)
    base = rng.choice(READ_BASE[kind])
    if explicit:
        base = rng.choice([f"{base} from the {nm(dev)}", f"{base} on the {nm(dev)}", f"On the {nm(dev)}, {base}"])
    user = styl(base)
    if not needs:
        return active, exchange(user, [], reply), True
    args = {"device": dev} if explicit else {}
    res = json.dumps({"device": dev, **d})
    if rng.random() < 0.08:
        res, reply = error_case(dev, "/read")
    return active, exchange(user, [("read_sensors", args, res)], reply), True


def select():
    active = rng.choice(DEVS)
    dev = rng.choice(DEVS)
    base = rng.choice(["switch to the {d}", "use the {d}", "select the {d}", "change to the {d}",
                       "let's use the {d}", "switch to {d}", "I want to use the {d}"]).format(d=nm(dev))
    D = SPOKEN[dev]
    reply = rng.choice([f"Switched to the {D}.", f"Okay, using the {D} now.", f"The {D} is now active."])
    return active, exchange(styl(base), [("select_device", {"device": dev}, f"Active device is now {dev}.")], reply), True


def combo():
    active = rng.choice(DEVS)
    dev = rng.choice(DEVS)
    D = SPOKEN[dev]
    if "pwm" in outs(dev) and rng.random() < 0.35:
        n = rng.randint(0, 255)
        args, act, user_act = {"channel": "pwm", "value": str(n)}, f"set PWM to {n}", f"set pwm to {n}"
    else:
        ch = rng.choice([c for c in outs(dev) if c in ("led", "relay")])
        state = rng.choice(["on", "off"])
        args, act = {"channel": ch, "value": state}, f"turned the {CHS[ch]} {state}"
        user_act = f"turn the {spoken_ch(ch)} {state}"
    user = styl(rng.choice([f"switch to the {nm(dev)} and {user_act}", f"use the {nm(dev)} and {user_act}",
                            f"switch to {nm(dev)}, then {user_act}"]))
    calls = [("select_device", {"device": dev}, f"Active device is now {dev}."),
             ("set_output", args, f"{dev}: OK")]
    if "set PWM" in act:
        reply = f"Switched to the {D} and set PWM to {args['value']}."
    else:
        reply = f"Switched to the {D} and {act}."
    return active, exchange(user, calls, reply), True


def followup():
    active, dev, explicit = pick_target()
    ch = rng.choice([c for c in outs(dev) if c in ("led", "relay")])
    s1 = rng.choice(["on", "off"])
    s2 = "off" if s1 == "on" else "on"
    D, c = SPOKEN[dev], CHS[ch]
    base1 = rng.choice(V_ON if s1 == "on" else V_OFF).format(c=spoken_ch(ch))
    u1 = styl(with_dev(base1, nm(dev)) if explicit else base1)
    a1 = {"channel": ch, "value": s1}
    a2 = {"channel": ch, "value": s2}
    if explicit:
        a1["device"] = dev
        a2["device"] = dev
    u2 = styl(rng.choice([f"now turn it {s2}", f"turn it {s2} again", f"okay, switch it {s2}"]))
    m = exchange(u1, [("set_output", a1, f"{dev}: OK")], f"The {c} on the {D} is now {s1}.")
    m += exchange(u2, [("set_output", a2, f"{dev}: OK")], f"The {c} on the {D} is now {s2}.")
    return active, m, True


def unknown_device():
    active = rng.choice(DEVS)
    bad = rng.choice(UNKNOWN_DEVICES)
    ch, state = rng.choice(["led", "relay"]), rng.choice(["on", "off"])
    base = rng.choice(V_ON if state == "on" else V_OFF).format(c=spoken_ch(ch))
    user = styl(with_dev(base, bad))
    res = f"ERROR: Unknown device '{bad}'. Known: {DEVS}"
    reply = f"I don't have a device called {bad}. I can use the ESP32, ESP-01S, Arduino or RP2040."
    return active, exchange(user, [("set_output", {"channel": ch, "value": state, "device": bad}, res)], reply), True


def unknown_channel():
    active, dev, explicit = pick_target()
    thing = rng.choice(UNKNOWN_THINGS)
    state = rng.choice(["on", "off"])
    base = rng.choice(V_ON if state == "on" else V_OFF).format(c=thing)
    user = styl(with_dev(base, nm(dev)) if explicit else base)
    reply = f"The {SPOKEN[dev]} only has {join_outs(outs(dev))}. I can't control a {thing}."
    return active, exchange(user, [], reply), True


def meta():
    active = rng.choice(DEVS)
    A = SPOKEN[active]
    allnames = "ESP32, ESP-01S, Arduino and RP2040"
    opts = [
        (rng.choice(["list the devices", "which devices do you have", "what devices are connected",
                     "what devices can you control"]),
         f"I can control the {allnames}."),
        (rng.choice(["what is the active device", "which device am I using", "which device is active"]),
         f"The active device is the {A}."),
    ]
    dev = rng.choice(DEVS)
    opts.append((rng.choice([f"what outputs does the {nm(dev)} have", f"what can the {nm(dev)} control"]),
                 f"The {SPOKEN[dev]} has {join_outs(outs(dev))}."))
    u, r = rng.choice(opts)
    return active, exchange(styl(u), [], r), True


# ---------- general chat (no tools offered) ----------
GREET = [
    ("hello", "Hello! How can I help?"), ("hi", "Hi! What can I do for you?"),
    ("hey there", "Hey! What do you need?"), ("good morning", "Good morning! How can I help?"),
    ("good evening", "Good evening! What can I do for you?"),
    ("how are you", "I'm doing well, thanks. What can I do for you?"),
    ("thank you", "You're welcome."), ("thanks", "You're welcome."),
    ("never mind", "Okay."), ("stop", "Okay."),
    ("who are you", "I'm your voice assistant. I can control your microcontrollers and answer general questions."),
    ("what is your name", "I'm your voice assistant. I don't have a special name."),
    ("what can you do", "I can control your ESP32, ESP-01S, Arduino and RP2040, read their sensors, and answer general questions."),
    ("who developed you", "I'm a local assistant running on a small language model, so I don't know who built me."),
    ("what time is it", "I can't see a clock or the internet, so I don't know the current time."),
    ("what is the date today", "I can't see a calendar or the internet, so I don't know today's date."),
    ("what is the weather today", "I have no internet access, so I can't check the weather."),
    ("tell me the news", "I have no internet access, so I can't read the news."),
]
FACTS = [
    ("what is the capital of France", "The capital of France is Paris."),
    ("what is the capital of Iran", "The capital of Iran is Tehran."),
    ("what is the capital of Italy", "The capital of Italy is Rome."),
    ("what is the capital of Japan", "The capital of Japan is Tokyo."),
    ("what is the capital of Germany", "The capital of Germany is Berlin."),
    ("what is the capital of Spain", "The capital of Spain is Madrid."),
    ("what is the capital of Canada", "The capital of Canada is Ottawa."),
    ("what is the capital of Egypt", "The capital of Egypt is Cairo."),
    ("what is the capital of Turkey", "The capital of Turkey is Ankara."),
    ("what is the capital of Australia", "The capital of Australia is Canberra."),
    ("what is the capital of Brazil", "The capital of Brazil is Brasilia."),
    ("where is Genoa", "Genoa is a port city in northwest Italy."),
    ("what is the largest planet", "Jupiter is the largest planet in our solar system."),
    ("which planet is closest to the sun", "Mercury is the closest planet to the sun."),
    ("how many planets are in the solar system", "There are eight planets in the solar system."),
    ("how many continents are there", "There are seven continents."),
    ("what is the largest ocean", "The Pacific Ocean is the largest ocean."),
    ("who wrote Romeo and Juliet", "William Shakespeare wrote Romeo and Juliet."),
    ("who painted the Mona Lisa", "Leonardo da Vinci painted the Mona Lisa."),
    ("what is the boiling point of water", "Water boils at 100 degrees Celsius at sea level."),
    ("at what temperature does water freeze", "Water freezes at 0 degrees Celsius."),
    ("how many days are in a year", "A year has 365 days, or 366 in a leap year."),
    ("what is the chemical symbol for gold", "The chemical symbol for gold is Au."),
    ("what is the chemical formula of water", "The chemical formula of water is H2O."),
    ("how fast is the speed of light", "Light travels at about 299,792 kilometers per second."),
    ("how many sides does a hexagon have", "A hexagon has six sides."),
    ("what is 12 times 12", "12 times 12 is 144."),
    ("what is 7 times 8", "7 times 8 is 56."),
    ("what is the square root of 81", "The square root of 81 is 9."),
    ("what is 15 percent of 200", "15 percent of 200 is 30."),
    ("what does LED stand for", "LED stands for light emitting diode."),
    ("what is Python", "Python is a popular programming language known for being easy to read."),
    ("what is an ESP32", "The ESP32 is a low-cost microcontroller with built-in Wi-Fi and Bluetooth, made by Espressif."),
    ("what is an Arduino", "Arduino is an open-source electronics platform built around easy-to-use microcontroller boards."),
    ("what is the RP2040", "The RP2040 is a microcontroller chip made by Raspberry Pi, used on the Pico board."),
    ("what is PWM", "Pulse width modulation switches a pin on and off quickly to control things like LED brightness or motor speed."),
    ("what is a relay", "A relay is an electrically controlled switch used to turn higher-power devices on and off."),
    ("what is a microcontroller", "A microcontroller is a small computer on a single chip that controls electronic devices."),
    ("what is GPIO", "GPIO stands for general-purpose input output. It is a pin you can use as a digital input or output."),
    ("what is I2C", "I2C is a two-wire serial bus for connecting chips such as sensors to a microcontroller."),
    ("what is Ohm's law", "Ohm's law says voltage equals current times resistance."),
    ("what voltage does USB use", "USB normally supplies 5 volts."),
]


def general():
    active = rng.choice(DEVS)
    if rng.random() < 0.3:
        q, a = rng.choice(GREET)
        user = styl(q)
    else:
        q, a = rng.choice(FACTS)
        user = styl(rng.choice(["", "", "hey, ", "quick question, ", "tell me, ", "um, "]) + q)
    return active, exchange(user, [], a), False


# ---------- build ----------
PLAN = [(digital, 470), (pwm, 200), (pwm_off, 20), (pwm_unsupported, 50), (read, 280), (select, 80),
        (combo, 90), (followup, 90), (unknown_device, 40), (unknown_channel, 50), (meta, 40), (general, 300)]


def main():
    rows, seen, stats = [], set(), {}
    for fn, n in PLAN:
        made = tries = 0
        while made < n and tries < n * 30:
            tries += 1
            active, msgs, use_tools = fn()
            key = (active, json.dumps(msgs, sort_keys=True))
            if key in seen:
                continue
            seen.add(key)
            row = {"messages": [sysmsg(active)] + msgs}
            if use_tools:
                row["tools"] = TOOLS
            rows.append(row)
            made += 1
        stats[fn.__name__] = made
    rng.shuffle(rows)
    cut = len(rows) // 10
    out = ROOT / "training"
    for name, part in (("hardware_eval.jsonl", rows[:cut]), ("hardware_train.jsonl", rows[cut:])):
        with open(out / name, "w", encoding="utf-8") as f:
            for r in part:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(stats)
    print(f"train={len(rows) - cut} eval={cut}")


if __name__ == "__main__":
    main()
