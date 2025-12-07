import openai
from config import OPENAI_API_KEY
from pydub import AudioSegment
import os

openai.api_key = OPENAI_API_KEY

# Convert to WAV for Whisper
def convert_to_wav(input_path):
    output_path = "uploads/converted.wav"
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format="wav")
    return output_path

# Transcribe audio using OpenAI Whisper
def transcribe_audio(filepath):
    wav_path = convert_to_wav(filepath)

    with open(wav_path, "rb") as f:
        transcript = openai.audio.transcriptions.create(
            file=f,
            model="whisper-1"
        )

    return transcript["text"]

# Translate text using GPT-4o-mini
def translate_text(text, target_lang="hi"):
    result = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Translate this to {target_lang}: {text}"
        }]
    )
    return result.choices[0].message.content
