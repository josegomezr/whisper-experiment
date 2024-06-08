Fetch dependencies
---

- ffmpeg-7
- The model, use `python download-model.py openai/whisper-base base-model/`
- `pip install -r requirements.txt`

Running
----

```bash
# if not given it'll try to find a model in ./model/
DA_MODEL=./base-model/ python3 run-model.py -f - < your-file
# or
DA_MODEL=./base-model/ python3 run-model.py -f your-file
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
