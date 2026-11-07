"""Rebuild the full training set: hardware + personal -> all_train.jsonl / all_eval.jsonl.

Run from the repo root:  python training/build_dataset.py
Deterministic (fixed seeds), so the output is identical on every machine.
"""
import subprocess
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
for script in ("generate_dataset.py", "generate_personal.py"):
    subprocess.run([sys.executable, str(here / script)], check=True)

for split in ("train", "eval"):
    with open(here / f"all_{split}.jsonl", "w", encoding="utf-8", newline="\n") as out:
        for part in ("hardware", "personal"):
            out.write((here / f"{part}_{split}.jsonl").read_text(encoding="utf-8"))
    n = sum(1 for _ in open(here / f"all_{split}.jsonl", encoding="utf-8"))
    print(f"all_{split}.jsonl: {n} rows")
