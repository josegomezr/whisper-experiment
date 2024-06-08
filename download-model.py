from huggingface_hub import snapshot_download
from pathlib import Path
import sys

model_id, path = sys.argv[1:] # "openai/whisper-tiny"
path = Path(path) # Path("./example")

snapshot_download(repo_id=model_id, local_dir=path, allow_patterns=["*.json", "*.txt", "*.safetensors"])
