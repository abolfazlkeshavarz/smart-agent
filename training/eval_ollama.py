"""Score a model in Ollama on the held-out rows, using the same tools as the agent.

Usage:
  python training/eval_ollama.py --model llama3.2:3b        # baseline
  python training/eval_ollama.py --model smart-llama        # your fine-tuned model
Options: --n 60 (rows to test), --show (print every reply)

Checks the first assistant decision of each row:
  call    : did it call the right tool with the right arguments?
  nocall  : when no tool is needed, did it answer without one?
  numbers : for fact answers, does the reply contain the same numbers as the expected answer?
"""
import argparse
import json
import random
import re
import sys
from pathlib import Path

import ollama

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agent"))
from main import TOOLS  # noqa: E402


def to_ollama(msgs):
    out = []
    for m in msgs:
        m = dict(m)
        if m["role"] == "tool":
            m["tool_name"] = m.pop("name", "")
        if m.get("tool_calls"):
            m["tool_calls"] = [{"function": {"name": c["function"]["name"],
                                             "arguments": c["function"]["arguments"]}} for c in m["tool_calls"]]
        out.append(m)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--file", default=str(ROOT / "training" / "all_eval.jsonl"))
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.file, encoding="utf-8")]
    random.Random(1).shuffle(rows)
    rows = rows[:a.n]
    stat = {"call": [0, 0], "nocall": [0, 0], "numbers": [0, 0]}
    bad = []
    for r in rows:
        msgs = r["messages"]
        i = next(k for k, m in enumerate(msgs) if m["role"] == "assistant")
        exp = msgs[i]
        resp = ollama.chat(model=a.model, messages=to_ollama(msgs[:i]),
                           tools=TOOLS if r.get("tools") else None, options={"temperature": 0})
        calls = resp.message.tool_calls or []
        reply = (resp.message.content or "").strip()
        got = (calls[0].function.name, {k: str(v) for k, v in dict(calls[0].function.arguments).items()}) if calls else None
        user = msgs[i - 1]["content"]
        if exp.get("tool_calls"):
            f = exp["tool_calls"][0]["function"]
            want = (f["name"], {k: str(v) for k, v in f["arguments"].items()})
            ok = got == want
            stat["call"][0] += ok
            stat["call"][1] += 1
        else:
            ok = got is None
            stat["nocall"][0] += ok
            stat["nocall"][1] += 1
            nums = re.findall(r"\d+(?:\.\d+)?", exp["content"])
            if nums and ok:
                n_ok = all(n in reply for n in nums)
                stat["numbers"][0] += n_ok
                stat["numbers"][1] += 1
                ok = ok and n_ok
        if a.show or not ok:
            bad.append((ok, user, exp.get("tool_calls") or exp["content"], got or reply))
    print(f"model: {a.model}  rows: {len(rows)}")
    for k, (x, y) in stat.items():
        if y:
            print(f"  {k:8s} {x}/{y} = {100 * x / y:.0f}%")
    for ok, u, want, got in bad[:15]:
        print(("\nOK   " if ok else "\nFAIL ") + f"USER: {u}\n  WANT: {want}\n  GOT : {got}")


if __name__ == "__main__":
    main()
