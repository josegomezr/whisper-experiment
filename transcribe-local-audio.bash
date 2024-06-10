#!bin/bash

function run_model() {
  filename=${1??"ENTER FILENAME"}

  python run_model.py -f - < $filename \
    | jq -Mcr \
    | tee $filename.json \
    | jq -Mcr '.chunks[] | [(.timestamp | join(" - ")), .text] | join("\n  ")' \
    | sed 's/000\+/0/g' > $filename.txt
}

JQ_OUT_STREAM=$(cat <<EOF
.[]
    | select(
      .type == "PipeWire:Interface:Node"
      and .info.state == "running"
      and .info.props["stream.is-live"] == true
      and (.info.props["stream.monitor"] // false) == false
    )
    | {
      id: .id,
      application: .info.props["application.name"],
      media: .info.props["media.name"],
      node: .info.props["node.name"]
    }
    | [
      .id,
      (
        [
          .application,
          .media,
          .node
        ] | map ( . // empty) | join(" - ")
      )
    ] | join("|")
EOF
)

JQ_INPUT_STREAM=$(cat <<EOF
.[]
    | select(
        .type == "PipeWire:Interface:Node"
        and .info.props["device.api"] == "alsa"
        and .info.props["api.alsa.pcm.stream"] == "capture"
    )
    | {
        id: .id,
        name: .info.props["api.alsa.card.longname"],
        profile_description: .info.props["device.profile.description"]
    }
    | [
        .id,
        .name,
        .profile_description
      ] | join("|")
EOF
)

SKIP_OUT=
SKIP_IN=

if [[ -z "$OUT_STREAM" ]]; then
  echo "= Select stream to record [firefox, or your favourite app] ="

  while IFS="|" read -r id name; do 
    printf "  %4s - %s\n" "$id" "$name"
  done <<< $(pw-dump | jq -Mcr "$JQ_OUT_STREAM")

  echo "---"
  echo "Type the ID from the list and press ENTER [empty = skip]"
  echo -n "-> "
  read -r OUT_STREAM

  OUT_STREAM=$(echo "${OUT_STREAM}" | xargs)
  if [[ -z "$OUT_STREAM" ]]; then
    echo "SKIPPING OUT"
    SKIP_OUT=1
  fi
fi


if [[ -z "$IN_STREAM" ]]; then
  echo "= Select input card to record [your mic] ="

  while IFS="|" read -r id name; do 
    printf "  %4s - %s\n" "$id" "$name"
  done <<< $(pw-dump | jq -Mcr "$JQ_INPUT_STREAM")

  echo "---"
  echo "Type the ID from the list and press ENTER [empty = skip]"
  echo -n "-> "
  read -r IN_STREAM

  IN_STREAM=$(echo "${IN_STREAM}" | xargs)
  if [[ -z "$IN_STREAM" ]]; then
    echo "SKIPPING IN"
    SKIP_IN=1
  fi
fi


if [[ "$SKIP_IN" -eq "1" && "$SKIP_OUT" -eq "1" ]]; then
  echo "= SKIPPING ALL="
  exit 0
fi

declare -a pids=();

if [[ -z "$SKIP_IN" ]]; then
  # Important, { stream.capture.sink=true } will only capture the sink (where
  # the audio being streamed ends up) and not the input source.
  echo "SELECTED IN STREAM ID=$IN_STREAM"
  echo pw-record --target "$IN_STREAM" ./in-stream.flac
  pw-record --target "$IN_STREAM" ./in-stream.flac &
  pids[1]=$!
fi

if [[ -z "$SKIP_OUT" ]]; then
  echo "SELECTED OUT STREAM ID=$OUT_STREAM"
  echo pw-record -P '{ stream.capture.sink=true }' --target "$OUT_STREAM" ./out-stream.flac
  pw-record -P '{ stream.capture.sink=true }' --target "$OUT_STREAM" ./out-stream.flac &
  pids[2]=$!
fi


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
  run_model "./in-stream.flac"
  cat ./in-stream.flac.txt
fi

if [[ -z "$SKIP_OUT" ]]; then
  echo "= Processing OUT-Stream"
  run_model "./out-stream.flac"
  cat ./out-stream.flac.txt
fi
