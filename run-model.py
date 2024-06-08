import json
import datetime
import sys
import argparse
import os

MODEL_ID = os.getenv("DA_MODEL", './model/')
DEVICE = "cpu"
# device = "cuda:0" if torch.cuda.is_available() else "cpu"

def argparser():
  parser = argparse.ArgumentParser(
    prog='run-model.py',
    description='Mah Whisper wrapper',
    epilog='---'
  )

  parser.add_argument('-f', '--file',
    dest='filename',
    nargs=1,
    help='Recording file dash (-) means stdin'
  )
  parser.add_argument('-d', '--device', default='cpu')
  return parser

def run_model(audio_in):
  # delay the side effects of importing this to the very end
  from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
  model = AutoModelForSpeechSeq2Seq.from_pretrained(
    MODEL_ID,
    # torch_dtype=torch_dtype,
    low_cpu_mem_usage=True,
    use_safetensors=True
  )
  model.to(DEVICE)

  processor = AutoProcessor.from_pretrained(MODEL_ID)

  pipe = pipeline(
    "automatic-speech-recognition",
    model=model,
    tokenizer=processor.tokenizer,
    feature_extractor=processor.feature_extractor,
    max_new_tokens=128,
    chunk_length_s=30,
    batch_size=16,
    return_timestamps=True,
    # torch_dtype=torch_dtype,
    device=DEVICE,
  )

  dt_transform = lambda z: str(datetime.timedelta(seconds = z)) if z else z

  result = pipe(audio_in)
  for row in result["chunks"]:
    try:
      row["timestamp"] = list(map(dt_transform, row["timestamp"]))
    except TypeError:
      pass
  print(json.dumps(result["chunks"], indent=2))

def main():
  parser = argparser()
  opts = parser.parse_args(sys.argv[1:])
  DEVICE = opts.device

  if not opts.filename:
    parser.print_help()
    return
  file = opts.filename[0]

  if file == '-':
    return run_model(sys.stdin.buffer.read())
  with open(file, 'rb') as f:
    main(f.read())

if __name__ == '__main__':
  main()

