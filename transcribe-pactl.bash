#!/bin/bash

function run_model() {
  filename=${1??"ENTER FILENAME"}

  python run_model.py -f - < $filename \
    | jq -Mcr \
    | tee $filename.json \
    | jq -Mcr '.chunks[] | [(.timestamp | join(" - ")), .text] | join("\n  ")' \
    | sed 's/000\+/0/g' > $filename.txt
}

if [[ -z "$DEF_SOURCE" ]]; then
  DEF_SOURCE=$(pactl info | sed -En '/Default Source: (.+)/ { s/.+: (.+)/\1/;p}')
fi

if [[ -z "$DEF_SINK" ]]; then
  DEF_SINK=$(pactl info | sed -En '/Default Sink: (.+)/ { s/.+: (.+)/\1/;p}').monitor
fi

echo "Recording from input: $DEF_SOURCE"
echo "Recording from stream: $DEF_SINK"

declare -a pids=();

parecord -d "$DEF_SOURCE" --file-format=wav -r in-stream.wav &
pids[1]=$!
parecord -d "$DEF_SINK" --file-format=wav -r out-stream.wav &
pids[2]=$!

echo "RECORDING PIDS: ${pids[@]}"
echo ""
echo "PRESS ENTER TO STOP RECORDING"
read -r STOP;

echo "Stopping..."
for pid in ${pids[*]}; do
  kill -SIGTERM $pid
done

echo "Waiting..."
for pid in ${pids[*]}; do
  wait $pid
done

if [[ -z "$SKIP_IN" ]]; then
  echo "= Processing IN-Stream"
  run_model "./in-stream.wav"
  cat ./in-stream.wav.txt
fi

if [[ -z "$SKIP_OUT" ]]; then
  echo "= Processing OUT-Stream"
  run_model "./out-stream.wav"
  cat ./out-stream.wav.txt
fi
