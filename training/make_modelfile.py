"""Import the trained GGUF into Ollama, reusing llama3.2's chat/tool template.

Usage:  python training/make_modelfile.py C:\\path\\to\\smart-llama-q4_k_m.gguf [model-name]
Then:   python agent/main.py --text --model smart-llama
"""
import subprocess
import sys
from pathlib import Path

if len(sys.argv) < 2:
    sys.exit(__doc__)
gguf = Path(sys.argv[1]).resolve()
name = sys.argv[2] if len(sys.argv) > 2 else "smart-llama"
if not gguf.exists():
    sys.exit(f"not found: {gguf}")

base = subprocess.run(["ollama", "show", "llama3.2:3b", "--modelfile"],
                      capture_output=True, text=True, check=True).stdout
out, replaced = [], False
for line in base.splitlines():
    if line.startswith("FROM ") and not replaced:
        out.append(f"FROM {gguf}")
        replaced = True
    else:
        out.append(line)
mf = Path(__file__).resolve().parent / "Modelfile"
mf.write_text("\n".join(out) + "\n", encoding="utf-8")
subprocess.run(["ollama", "create", name, "-f", str(mf)], check=True)
print(f"created '{name}'. Test it with: python training/eval_ollama.py --model {name}")
