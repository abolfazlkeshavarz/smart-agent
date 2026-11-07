# Fine-tuning guide

Goal: make the model call the right tool with the right arguments, answer chat directly, and know facts
about you. Method: LoRA on `Llama-3.2-3B-Instruct` with Unsloth, trained on a free Google Colab T4, then
imported into Ollama.

Use fine-tuning for **behaviour** (tool calls, style). It is a poor way to store exact facts (grades,
dates): a 3B model will misremember them. For reliable facts, retrieval (RAG) is the better tool.

## 1. Build the dataset

```
python training/build_dataset.py
```

This runs both generators and writes `training/all_train.jsonl` and `training/all_eval.jsonl`
(about 2,170 and 240 rows). The output is deterministic.

| File | Content |
|---|---|
| `generate_dataset.py` | Hardware commands for all boards and channels, PWM edge cases, sensor reads, device switching, follow-ups, errors, unknown devices/outputs, and general chat. It imports the real system prompt and tool schema from `agent/main.py`, so the data matches run time. |
| `generate_personal.py` | Personal knowledge facts. Edit the `FACTS` list to add or correct anything. |

If you change `config.yaml` (devices or channels) or the tools in `agent/main.py`, rebuild the dataset.
The eval rows are never trained on.

## 2. Baseline (optional)

```
python training/eval_ollama.py --model llama3.2:3b
```

Scores the model on held-out rows: correct tool and arguments, no tool when none is needed, and numbers
in fact answers. Options: `--n 20` (fewer rows, faster), `--show` (print every reply).

## 3. Train on Colab

1. Open colab.research.google.com, then File > Upload notebook, and pick `training/train_colab.ipynb`.
2. Runtime > Change runtime type > **T4 GPU**. (TPU runtimes will not work: Unsloth needs an NVIDIA GPU.)
3. Run all cells from the top. Allow Drive access; upload `all_train.jsonl` and `all_eval.jsonl` on the
   first run. They are stored in `MyDrive/smart-agent`.
4. Training takes roughly 1.5 hours for 3 epochs. Checkpoints are saved to Drive every 100 steps.
5. **If Colab disconnects**, reconnect and re-run every cell from the top. Training resumes from the last
   checkpoint.
6. The test cell prints tool-call accuracy on held-out rows and the first failures. The live cell lets you
   ask questions. Only after these look good, run the last cell to export the LoRA adapters and a
   `smart-llama-q4_k_m.gguf` (about 2 GB) to Drive.

Loss falling is not proof of quality: the hardware examples are repetitive. Judge by the test cell and by step 5.

## 4. Import into Ollama

Download the `.gguf` from Drive, make sure `llama3.2:3b` is pulled (its chat template is reused), then:

```
python training/make_modelfile.py /path/to/smart-llama-q4_k_m.gguf
```

This creates the Ollama model `smart-llama`. Use it:

```
python agent/main.py --text --model smart-llama
```

## 5. Evaluate

```
python training/eval_ollama.py --model smart-llama
```

Compare with the baseline. Training worked if tool-call accuracy and the number checks go up.

## Notes and risks

- The notebook trains with the Hugging Face Llama chat template, while Ollama uses its own. They are
  close, but if the Colab test is good and the Ollama score is much worse, the template mismatch is the
  first suspect.
- Rows with two tool calls in one message are split into one call per turn for training, matching how the
  agent loop works.
- Keep the personal data private (see the README).
- Retraining after changes: rebuild the dataset, upload the new `all_*.jsonl` (delete the old copies in
  Drive and the `checkpoints` folder so it starts fresh), and run the notebook again.
