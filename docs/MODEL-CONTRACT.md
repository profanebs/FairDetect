# Model contract

FairDetect is a pipeline, not a model. It expects one thing from a model: given a text window (up to eight sentences), return a probability that the window is AI-generated, in `[0, 1]`.

There are three adapter types. Pick the one that matches what you have.

---

## 1. `hf`: a local Hugging Face classifier

### What it expects

A directory containing a standard `AutoModelForSequenceClassification` checkpoint:

```
models/my-model/
  config.json
  tokenizer.json
  tokenizer_config.json
  special_tokens_map.json
  model.safetensors            # or pytorch_model.bin
```

It is loaded with:

```python
AutoTokenizer.from_pretrained(path, local_files_only=True)
AutoModelForSequenceClassification.from_pretrained(
    path, local_files_only=True, torch_dtype=torch.float32)
```

### How the score is produced

- Two or more logits: softmax, then take `ai_label_index`.
- One logit: sigmoid.
- `ai_label_index: "auto"`: look at `model.config.id2label` and pick the first label containing `ai`, `machine`, `fake`, `generated`, or `chatgpt`. If nothing matches, use index `1`.
- Set `ai_label_index` explicitly when your labels are ambiguous.

### Config

```json
{
  "id": "shield",
  "label": "My shield",
  "role": "shield",
  "adapter": "hf",
  "path": "models/shield",
  "ai_label_index": "auto",
  "max_length": 256,
  "device": "auto",
  "batch_size": 32
}
```

### Notes

- `device: "auto"` uses CUDA when available, otherwise CPU.
- A 700 MB DeBERTa checkpoint takes a few seconds to load and roughly 10–40 seconds per document on CPU. On a modern GPU it is much faster.
- The model is loaded lazily on the first score, so the web console can start without a GPU.
- If the directory is missing, the model shows as `MISSING` in `/api/models` and the console disables it. The server still starts.

### What to train

The original recipe: DeBERTa-v3-base, 8-sentence windows, stride 2, max length 256, batch size 16, 2 epochs, learning rate 2e-5. Training data and scripts are not included. Any binary AI/human classifier with a comparable window setup can be attached.

---

## 2. `openai`: a local OpenAI-compatible LLM

### What it expects

An HTTP endpoint implementing `POST {base_url}/chat/completions`, for example:

- Ollama: `http://127.0.0.1:11434/v1`
- LM Studio: `http://127.0.0.1:1234/v1`
- llama.cpp server: `http://127.0.0.1:8080/v1`
- vLLM: `http://127.0.0.1:8000/v1`

### How the score is produced

For each window, FairDetect sends:

```json
{
  "model": "your-model",
  "messages": [{"role": "user", "content": "...prompt with the passage..."}],
  "temperature": 0,
  "max_tokens": 64,
  "stream": false
}
```

The prompt asks for JSON only:

```json
{"ai_probability": 0.0}
```

The adapter parses the first JSON object, then a percentage, then the first number in `[0, 1]`. If parsing fails, the job reports an error.

### Config

```json
{
  "id": "local-llm",
  "label": "Local LLM",
  "role": "shield+spear",
  "adapter": "openai",
  "base_url": "http://127.0.0.1:11434/v1",
  "model": "qwen2.5:7b",
  "api_key_env": "LOCAL_LLM_API_KEY",
  "timeout": 180,
  "max_tokens": 64,
  "temperature": 0
}
```

### Performance and calibration warnings

- **One request per window**, up to 30 windows per document. Expect minutes per document on a 7B model.
- The score is **not calibrated**. The default judge thresholds (0.32 / 0.80) belong to the DeBERTa pair. For a single LLM, use `config/models.single.example.json` (0.50) or calibrate on your own data.
- The model may refuse, ramble, or answer in prose. The parser is tolerant but not magic. Test with `scripts/check_setup.py --score`.
- Prompt injection inside the document is possible in principle; this is a local research tool, not a security boundary.

---

## 3. `http`: your own scoring service

### What it expects

```http
POST http://127.0.0.1:9000/score
Content-Type: application/json

{"text": "one window"}
```

Response:

```json
{"score": 0.73}
```

Accepted fields: `score`, `ai_probability`, `probability`. The field name can be changed with `field`.

### Config

```json
{
  "id": "my-service",
  "label": "My scorer",
  "role": "shield+spear",
  "adapter": "http",
  "url": "http://127.0.0.1:9000/score",
  "field": "score",
  "timeout": 120,
  "headers": {"Authorization": "Bearer ${MY_TOKEN}"}
}
```

`${ENV_VAR}` is expanded at load time, so secrets can stay out of the config file.

### When to use it

- You have an ONNX model and a small Python server.
- You have a proprietary model you cannot load in-process.
- You want to batch or cache scores in your own service.
- You want to implement a different tokenizer or windowing scheme behind the same interface.

---

## 4. Judge configuration

A judge combines one or two model scores.

```json
{
  "id": "mean-bar",
  "label": "Shield >= 0.32 OR Spear >= 0.80",
  "shield": "shield",
  "spear": "spear",
  "mode": "or",
  "stat": "mean",
  "g0": 0.32,
  "r0": 0.8
}
```

| Field | Meaning |
| --- | --- |
| `shield` / `spear` | Model ids. They may be the same id. |
| `mode: "or"` | Mean-bar rule: `S = 100 * max(g, r)`, caught if `g >= g0` or `r >= r0`. |
| `mode: "max"` | Legacy pct-based rule (used by older internal judges). |
| `stat: "mean"` | Use the window mean (`0..1`). Required for mean-bar judges. |
| `stat: "pct50"` | Use the window percentage (`0..100`). Legacy. |
| `g0` / `r0` | Thresholds in the unit of `stat`. |

If you only have one model, set both `shield` and `spear` to the same id. The pipeline scores it once (the model cache is keyed by id) and applies the same score to both sides.

---

## 5. Calibrating your own thresholds

Do not reuse 0.32 / 0.80 blindly. A minimal procedure:

1. Collect a human set and an AI set that did **not** appear in training.
2. Split each into a tuning half and a validation half.
3. On the tuning half, choose the threshold that meets your human false-positive budget (for example, <= 2% on learner writing and <= 10% on advanced academic writing).
4. Freeze the threshold and the rule.
5. Run once on the validation half. Do not tune again on it.
6. Report the validation numbers with pool sizes and the rule written down before the run.

If you skip step 5, you are reporting a tuning result as if it were a validation result. That is the main methodological failure in the original project, and it is easy to repeat.

---

## 6. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `model not configured` | Path missing or not a HF directory | Check `models/README.md`; run `python scripts/check_setup.py`. |
| `torch/transformers not installed` | Dependencies missing | `pip install -r requirements.txt`. |
| `ai_label_index out of range` | Model has fewer labels than configured | Set `ai_label_index` to `0` or `1`; inspect `config.json`. |
| `cannot reach http://...` | Local LLM/server not running | Start Ollama/LM Studio/etc.; check the port. |
| `text too short` | Fewer than 4 sentences | Use a longer text. |
| `no verdict` | Judge referenced a model that failed | Check `/api/models` availability and the job error. |
| CUDA out of memory | Two large checkpoints on one GPU | Use CPU for one, or load one model at a time, or use a smaller checkpoint. |
