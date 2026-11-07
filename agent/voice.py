"""Offline STT (faster-whisper) and TTS (pyttsx3 / Windows SAPI)."""
import numpy as np

SR = 16000


class Listener:
    def __init__(self, model_name: str):
        from faster_whisper import WhisperModel
        self.model = WhisperModel(model_name, device="cpu", compute_type="int8")

    def record(self, max_s=15, silence_s=1.0, threshold=0.012) -> np.ndarray:
        """Record until ~1 s of silence after speech (simple energy VAD)."""
        import sounddevice as sd
        block = int(SR * 0.1)
        chunks, quiet, spoke = [], 0, False
        with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=block) as st:
            for _ in range(int(max_s / 0.1)):
                data, _ = st.read(block)
                data = data[:, 0]
                chunks.append(data)
                if np.sqrt(np.mean(data ** 2)) > threshold:
                    spoke, quiet = True, 0
                else:
                    quiet += 1
                    if spoke and quiet * 0.1 >= silence_s:
                        break
        return np.concatenate(chunks) if spoke else np.zeros(0, dtype="float32")

    def listen(self) -> str:
        audio = self.record()
        if audio.size == 0:
            return ""
        segs, _ = self.model.transcribe(audio, language="en", beam_size=1, vad_filter=True)
        return " ".join(s.text.strip() for s in segs).strip()


class Speaker:
    def __init__(self, rate=175):
        self.rate = rate

    def say(self, text: str):
        if not text:
            return
        import pyttsx3
        eng = pyttsx3.init()  # re-init each time: avoids a known pyttsx3 hang on Windows
        eng.setProperty("rate", self.rate)
        eng.say(text)
        eng.runAndWait()
