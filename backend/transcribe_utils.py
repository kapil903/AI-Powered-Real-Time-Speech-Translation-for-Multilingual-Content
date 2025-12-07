# transcribe_utils.py
import numpy as np
import whisper
import subprocess
import os
from pydub import AudioSegment
import tempfile
import requests
from typing import Optional

# Load Whisper model globally to avoid reloading per request
# Choose model based on available resources: "small", "medium", "large"
MODEL_NAME = os.getenv("WHISPER_MODEL", "small")
print("Loading Whisper model:", MODEL_NAME)
model = whisper.load_model(MODEL_NAME)


def pcm16_bytes_to_float32_np(pcm_bytes: bytes) -> np.ndarray:
    """
    Convert raw PCM16 (little-endian) bytes to float32 numpy array in range [-1,1].
    """
    arr = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    return arr


def transcribe_numpy_audio(audio_np: np.ndarray, sample_rate: int = 16000, language: Optional[str] = None):
    """
    Transcribe a float32 numpy array (mono) using whisper's transcribe.
    audio_np expected to be float32 (-1..1).
    """
    # Whisper expects either file path or audio as NumPy 16000Hz or sampling in file
    # We'll temporarily save to a WAV file and call model.transcribe for simplicity
    import soundfile as sf
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
        sf.write(tf.name, audio_np, sample_rate)
        tfname = tf.name

    try:
        opts = {"language": language} if language else {}
        result = model.transcribe(tfname, **opts)
        text = result.get("text", "").strip()
        return text, result
    finally:
        try: os.remove(tfname)
        except: pass


def extract_audio_from_file(file_path: str, target_sr: int = 16000) -> str:
    """
    Use ffmpeg to extract mono PCM16 WAV at target_sr.
    Returns path to temporary WAV file.
    """
    out_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    cmd = [
        "ffmpeg", "-y", "-i", file_path,
        "-vn",                      # no video
        "-ac", "1",                 # mono
        "-ar", str(target_sr),      # sample rate
        "-f", "wav",
        out_file
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return out_file


# --- Translation adapters (examples) ---
def translate_text_openai_placeholder(text: str, target_lang: str = "hi") -> str:
    """
    Placeholder: integrate your translation provider here (OpenAI, DeepL, Google).
    Example structure for calling a remote API.
    """
    # Example (pseudo): call your translation API here. For now return uppercase mock.
    return f"[{target_lang}] " + text  # mock translation


def translate_text_deepl(text: str, target_lang: str, api_key: str):
    """
    Example DeepL request (requires user account + API key).
    """
    url = "https://api-free.deepl.com/v2/translate"
    data = {"auth_key": api_key, "text": text, "target_lang": target_lang.upper()}
    resp = requests.post(url, data=data)
    if resp.status_code == 200:
        return resp.json()["translations"][0]["text"]
    else:
        raise RuntimeError(f"DeepL error: {resp.text}")

