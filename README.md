Fetch dependencies
---

- ffmpeg-7
- The model, use `python download-model.py openai/whisper-base base-model/`
- `pip install -r requirements.txt`

Running
----

```bash
# if not given it'll try to find a model in ./model/
DA_MODEL=./base-model/ python3 run_model.py -f - < your-file
# or
DA_MODEL=./base-model/ python3 run_model.py -f your-file
```

Record your computer audio
---

```bash
# Make sure to have your venv enabled.
# if not given it'll try to find a model in ./model/
DA_MODEL=./base-model/ bash transcribe-local-audio.bash
# select program to record [uses pipewire], empty => skip
# select mic input to record [uses pipewire], empty => skip
# Runs the model
```


Run your Telegram bot

```bash
# Make sure to have your venv enabled.
# export TG_BOT_TOKEN=<your bot token>
# export TG_BOT_EXCLUSIVE_USERNAMES=<optional list of usernames to listen for messages>
# export DA_MODEL=./medium-model/ # if not given it'll try to find a model in ./model/
python tg-bot.py
```
---

```bash
# Make sure to have your venv enabled.
# if not given it'll try to find a model in ./model/
DA_MODEL=./base-model/ bash transcribe-local-audio.bash
# select program to record [uses pipewire], empty => skip
# select mic input to record [uses pipewire], empty => skip
# Runs the model
```



---

Notes for pipewire

list output streams
---
```bash
JQ_QUERY=$(cat <<EOF
.[]
    | select(
        .type == "PipeWire:Interface:Node"
        and .info.state == "running"
        and .info.props["stream.is-live"] == true
    )
    | {
        id: .id,
        application: .info.props["application.name"],
        media: .info.props["media.name"],
        node: .info.props["node.name"]
    }
EOF
)
pw-dump | jq "$JQ_QUERY"
```

list input streams
---
```bash
JQ_QUERY=$(cat <<EOF
.[]
    | select(
        .type == "PipeWire:Interface:Device"
        and .info.props["device.api"] == "alsa"
    )
    | {
        id: .id,
        name: .info.props["api.alsa.card.longname"]
    }
EOF
)
pw-dump | jq "$JQ_QUERY"
```

record from pipewire
---
```bash
pw-record -P '{ stream.capture.sink=true }' --target %TARGET% ./recording/
```
