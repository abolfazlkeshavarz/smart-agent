# Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `LLM error: ... connection refused` | Ollama is not running. Open the Ollama app (Windows) or `sudo systemctl start ollama` (Linux). |
| `model 'llama3.2:3b' not found` | Run `ollama pull llama3.2:3b`. Check names with `ollama list`. |
| `cannot open COM3` / `/dev/ttyACM0` | Wrong port, board unplugged, or another program (serial monitor) holds it. On Linux also check group membership (`uucp` on Arch, `dialout` on Debian/Ubuntu). |
| `Permission denied: '/dev/ttyACM0'` | Add yourself to the serial group, then log out and in. |
| `no response (is the firmware flashed?)` | Firmware missing, wrong baud (must be 115200), or the board is still resetting. Re-run the command. |
| `unreachable at http://...` | Wrong IP in the config, board offline, or PC on a different network. Test with `curl http://IP/read`. |
| Replies say it did something but there is no `[tool]` line | The model skipped the tool. Rephrase directly ("set the LED on") or use the fine-tuned model. |
| Model calls tools for "hello" or general questions | The agent only offers tools for hardware-sounding messages. If it still happens, use a stronger or fine-tuned model. |
| Model answers raw JSON text | A tool call came out as plain text. Retry; small models do this occasionally. |
| `gemma3` does nothing with boards | Ollama's gemma3 has no tool-calling support. Use `llama3.2:3b`. |
| Whisper hears nothing | Wrong default microphone, or the room is too quiet or noisy. Adjust `threshold` in `Listener.record` (`agent/voice.py`). |
| No spoken reply on Linux | Install `espeak-ng`. Use `--no-tts` to disable speech. |
| `pip install` fails with "externally-managed-environment" (Arch) | Use a virtual environment (see SETUP.md). |
| Colab: unsloth or CUDA errors | Make sure the runtime is a **T4 GPU**, not TPU or CPU. Paste the error for help; versions change. |
| Colab disconnected mid-training | Reconnect and run all cells from the top; training resumes from the Drive checkpoint. |
| Slow replies on the office PC | CPU-only inference. Use a smaller prompt, or run at home with the GPU. Pass `--no-tts` and `--text` to save time. |
