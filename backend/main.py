from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from transcribe_utils import transcribe_audio, translate_text
import os

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure uploads folder exists
os.makedirs("uploads", exist_ok=True)

@app.get("/")
def home():
    return {"message": "Backend running successfully!"}

# Upload + transcribe + translate
@app.post("/process-media")
async def process_media(file: UploadFile = File(...)):
    file_path = f"uploads/{file.filename}"

    # Save file
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Step 1 → Transcribe
    transcription = transcribe_audio(file_path)

    # Step 2 → Translate to Hindi
    translation = translate_text(transcription, "hi")

    return {
        "transcription": transcription,
        "translation": translation
    }
