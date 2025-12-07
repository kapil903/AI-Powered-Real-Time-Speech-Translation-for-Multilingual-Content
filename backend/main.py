# main.py
import asyncio
from fastapi import FastAPI, WebSocket, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import time
import os
from transcribe_utils import (
    pcm16_bytes_to_float32_np,
    transcribe_numpy_audio,
    extract_audio_from_file,
    translate_text_openai_placeholder
)
import numpy as np
import tempfile

app = FastAPI()

# Config
SAMPLE_RATE = 16000
CHUNK_SECONDS = 0.8            # how long each chunk is (in seconds) before attempting transcription
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_SECONDS)
CHUNK_BYTES = CHUNK_SAMPLES * 2  # PCM16 => 2 bytes per sample


@app.websocket("/ws/live")
async def websocket_live(ws: WebSocket):
    """
    Expected: client sends raw PCM16 (little-endian) bytes via ws.send(pcmBuffer)
    Query params: source, target (optional)
    """
    await ws.accept()
    params = dict(ws.query_params)
    source_lang = params.get("source", None)
    target_lang = params.get("target", None)

    print("Client connected to /ws/live", params)
    buffer = bytearray()
    last_transcript = ""

    try:
        while True:
            data = await ws.receive_bytes()  # blocking await for next binary message
            if not data:
                continue

            # append incoming bytes
            buffer.extend(data)

            # if buffer has at least CHUNK_BYTES, process the last chunk
            while len(buffer) >= CHUNK_BYTES:
                # take CHUNK_BYTES from the front
                chunk = bytes(buffer[:CHUNK_BYTES])
                # remove from buffer
                del buffer[:CHUNK_BYTES]

                # Convert to float32 numpy
                audio_np = pcm16_bytes_to_float32_np(chunk)

                # Offload heavy work to threadpool so event loop remains responsive
                loop = asyncio.get_event_loop()
                transcription_result = await loop.run_in_executor(None, transcribe_numpy_audio, audio_np, SAMPLE_RATE, source_lang)

                transcript_text, _full = transcription_result
                transcript_text = transcript_text.strip()
                if transcript_text:
                    # Do translation (placeholder)
                    translated = translate_text_openai_placeholder(transcript_text, target_lang or "en")

                    payload = {"transcript": transcript_text, "translation": translated}
                    await ws.send_json(payload)
                    last_transcript = transcript_text

    except Exception as e:
        print("WebSocket closed or error:", e)
    finally:
        try:
            await ws.close()
        except:
            pass
        print("Connection closed.")


@app.post("/upload-process")
async def upload_process(file: UploadFile = File(...), source_lang: str = Form(None), target_lang: str = Form(None)):
    """
    Accept a file (video/audio). Extract audio, transcribe full audio, translate, return result.
    """
    # save temp file
    suffix = os.path.splitext(file.filename)[1] or ".tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tf:
        contents = await file.read()
        tf.write(contents)
        temp_path = tf.name

    try:
        # extract audio to WAV mono 16k
        wav_path = extract_audio_from_file(temp_path, target_sr=SAMPLE_RATE)

        # read wav as float32
        import soundfile as sf
        audio_np, sr = sf.read(wav_path, dtype="float32")
        if sr != SAMPLE_RATE:
            # ideally resample, but ffmpeg should have given target sr already
            pass

        # transcribe entire audio (offload to thread)
        loop = asyncio.get_event_loop()
        transcript_text, _ = await loop.run_in_executor(None, transcribe_numpy_audio, audio_np, SAMPLE_RATE, source_lang)

        # translate
        translated = translate_text_openai_placeholder(transcript_text, target_lang or "en")

        return JSONResponse({"transcription": transcript_text, "translation": translated})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.remove(temp_path)
        except:
            pass
        try:
            os.remove(wav_path)
        except:
            pass
