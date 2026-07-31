import os
from dotenv import load_dotenv
from pyannote.audio import Pipeline

load_dotenv()

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=os.getenv("HF_TOKEN"),
)

print("Pipeline loaded successfully!")