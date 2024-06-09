import json
import datetime
import warnings
import sys
import argparse
import os
import logging

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
    nargs='+',
    help='Recording file dash (-) means stdin'
  )
  parser.add_argument('-d', '--device', default='cpu')
  return parser

def format_timestamp(ts):
  if ts is None:
    return "END"

  return str(datetime.timedelta(seconds=round(ts)))

def silence_loggers_in_transformers():
  # They say very useful things if only I understood wtf that means, for now
  # it's just noise in my output.

  loggers_to_be_silenced = [
    'transformers.models.whisper.generation_whisper',
    'transformers.tokenization_utils_base'
  ]

  for facility in loggers_to_be_silenced:
    logger = logging.getLogger(facility)
    logger.level = logging.ERROR

def mock_load_model():
  return lambda x: {
    'text': ' the whole text output here, ignored',
    'chunks': [
      {
        'timestamp': (0.0, 7.08),
        'text': ' An output, this is just for formatting purposes so we get something'
      },
      {
        'timestamp': (7.08, 9.00),
        'text': ' to test the display without running the model, is very slow'
      }
    ]
  }

def format_chunks_text(chunks):
  response = ""
  for chunk in chunks:
    ts = ' - '.join(map(format_timestamp, chunk["timestamp"]))
    response = response + '[{0}]'.format(ts)
    response = response + "\n" + chunk['text'].strip()
    response = response + "\n\n"
  return response

def load_model():
  # delay the side effects of importing this to the very end
  from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
  silence_loggers_in_transformers()

  model = AutoModelForSpeechSeq2Seq.from_pretrained(
    MODEL_ID,
    # torch_dtype=torch_dtype,
    low_cpu_mem_usage=True,
    use_safetensors=True
  )
  model.to(DEVICE)

  processor = AutoProcessor.from_pretrained(MODEL_ID)

  return pipeline(
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

def run_model(filelist):
  pipe = load_model()

  for file in filelist:
    if file == '-':
      file = '/dev/stdin'

    with open(file, 'rb') as audio_in:
      result = pipe(audio_in.read())  
    
    result["processed_at"] = datetime.datetime.utcnow().strftime("%F-%R")
    result["filename"] = file

    for row in result["chunks"]:
      row["timestamp"] = list(map(format_timestamp, row["timestamp"]))

    print(json.dumps(result, indent=2))

def main():
  parser = argparser()
  opts = parser.parse_args(sys.argv[1:])
  DEVICE = opts.device

  if not opts.filename:
    parser.print_help()
    return

  with warnings.catch_warnings(record=True):
    run_model(opts.filename)

if __name__ == '__main__':
  main()

