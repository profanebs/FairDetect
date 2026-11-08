# FairDetect

**A local-first AI-text detection research prototype.** Two window classifiers, a transparent judge layer, a Turnitin-style review report, and a model adapter layer that lets you attach your own local model.

> [!WARNING]
> **This repository does not detect AI text out of the box.**
> The fine-tuned DeBERTa checkpoints that produced the numbers below are **not included**. They were trained on corpora that cannot be redistributed. You must attach your own local model: a Hugging Face classifier, a local OpenAI-compatible LLM, or a small HTTP scorer.
>
> Even with the original weights, the system has a **measured 26.7% false-positive rate on high-ability human academic writing** (MICUSP) and an **8.22% false-positive rate on a 3,478-document human holdout set**. It is not calibrated to Turnitin. It must never be used as the sole basis for an accusation.

---

## Why this exists

Commercial AI detectors are known to over-flag non-native English writers. Liang et al. (2023, *Patterns*) found that TOEFL essays written by humans were classified as AI-generated **61.3%** of the time on average; the worst detector flagged **97.8%** of them. Turnitin itself says its AI score is a probability estimate that can produce false positives and must not be the only basis for disciplinary action.

FairDetect asks a narrower question:

> Can a local, inspectable detector be built that is *conservative on human writing* and still catches humanized AI text?

The short answer is **partly**. The long answer, including the failures, is in [docs/EVALUATION.md](docs/EVALUATION.md) and [docs/LIMITS.md](docs/LIMITS.md).

This repository is the **best version we can publish**: the full inference pipeline, the judge layer, the review UI, and the adapter contract — everything except the weights.

---

## What is in the box

| Part | What it does |
| --- | --- |
| `app/` | React + Vite + Tailwind review console. Drag in `.docx` / `.md` / `.txt`, pick models and judges, get a report. |
| `server/` | Python standard-library HTTP server. No FastAPI, no Flask. Loads adapters, runs jobs, renders the HTML/PDF report. |
| `server/adapters.py` | **The part that makes this reusable.** `hf` (local Hugging Face classifier), `openai` (any OpenAI-compatible local LLM), `http` (your own scoring service). |
| `judge/judge.py` | Portable CLI for single files and batches. Same pipeline as the console. |
| `config/` | Model and judge definitions. Defaults, single-model, local-LLM, and HTTP examples. |
| `docs/` | Evaluation, limitations, model contract, architecture, ethics. |
| `examples/` | Two synthetic smoke-test texts. Not real submissions. |

No model weights, no training data, no student texts. The repository is intentionally data-free.

---

## How it works

```
.docx / .md / .txt
        |
        v
  extract text  ->  sentence split  ->  windows of 8 sentences, stride 2, cap 30
                                              |
                             +----------------+----------------+
                             |                                 |
                             v                                 v
                    shield adapter                      spear adapter
                 (conservative model)                (aggressive model)
                             |                                 |
                             +----------------+----------------+
                                              |
                                              v
                              per-sentence mean scores -> judge rule
                                              |
                                              v
                                  HTML report / PDF / JSON
```

- **Shield** is trained to avoid flagging human writing, even at the cost of missing AI.
- **Spear** is trained to catch AI and humanized AI, even at the cost of being aggressive.
- The **judge** is a separate rule layer, so you can change the operating point without retraining.

The published operating point (Judge 4.0) is:

```
g = shield window-mean score (0..1)
r = spear  window-mean score (0..1)
caught  iff  g >= 0.32  OR  r >= 0.80
S       = 100 * max(g, r)
flag    if not caught and r >= 0.90     (review recommended)
```

These thresholds are **specific to the original FairDetect pair**. If you attach your own models, calibrate them. The config ships with the original thresholds only as a starting point.

---

## Quick start (bring your own model)

### 1. Install

```powershell
git clone https://github.com/profanebs/FairDetect.git
cd FairDetect
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Linux / macOS: `python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`.

### 2. Put a checkpoint under `models/`

```
models/
  shield/
    config.json
    tokenizer.json
    tokenizer_config.json
    special_tokens_map.json
    model.safetensors
  spear/
    ...
```

Any Hugging Face `AutoModelForSequenceClassification` checkpoint works. Binary classifiers use softmax; single-logit models use sigmoid. The AI label is read from `id2label` when `ai_label_index` is `"auto"`; set it to `0` or `1` if your labels are ambiguous.

### 3. Check the setup

```powershell
python scripts/check_setup.py
```

It prints each configured model as `READY` or `MISSING`, and exits non-zero when nothing is ready.

### 4. Run the console

```powershell
python server/fairdetect_api.py
# open http://127.0.0.1:8790
```

Or double-click `scripts/start.cmd` on Windows.

The server binds **127.0.0.1 only** by default. Set `FAIRDETECT_HOST=0.0.0.0` if you really need LAN access, and set a token (below) before doing that.

### 5. Or use the CLI

```powershell
python judge/judge.py --list
python judge/judge.py --config config/models.json essay.txt
python judge/judge.py --config config/models.json --json essay.docx
python judge/judge.py --config config/models.json --batch meta.jsonl --out results.jsonl
```

---

## Attach a local LLM instead of a classifier

The `openai` adapter speaks the OpenAI chat-completions protocol, so it works with Ollama, LM Studio, llama.cpp server, vLLM, and anything else that exposes `/v1/chat/completions`.

```powershell
copy config\models.openai.example.json config\models.llm.json
# edit base_url and model, then:
$env:FAIRDETECT_CONFIG = "config/models.llm.json"
python scripts/check_setup.py --score examples/human_style.txt
python server/fairdetect_api.py
```

Example endpoints:

| Runtime | `base_url` | Notes |
| --- | --- | --- |
| Ollama | `http://127.0.0.1:11434/v1` | Use the exact model tag, e.g. `qwen2.5:7b`. |
| LM Studio | `http://127.0.0.1:1234/v1` | Start the local server first. |
| llama.cpp | `http://127.0.0.1:8080/v1` | `llama-server -m model.gguf`. |
| vLLM | `http://127.0.0.1:8000/v1` | OpenAI-compatible by default. |

**Read this before using the LLM path:**

- It makes **one request per window** (up to 30 windows per document), so a document can take minutes.
- The returned probability is **prompt-sensitive and uncalibrated**. The 0.32/0.80 thresholds do not transfer.
- It is useful for exercising the pipeline or for experimentation, not for decisions about people.

If you only have one model, use `config/models.single.example.json` and set both `shield` and `spear` to the same model id. The pipeline scores it once and applies a single 0.50 threshold.

## Attach a custom HTTP scorer

Implement this contract:

```http
POST http://127.0.0.1:9000/score
Content-Type: application/json

{"text": "one window of up to eight sentences"}
```

Response:

```json
{"score": 0.73}
```

`score`, `ai_probability`, and `probability` are all accepted. See `config/models.http.example.json`.

---

## Configuration reference

`config/models.json`:

```json
{
  "models": [
    {
      "id": "shield",
      "label": "Shield",
      "role": "shield",
      "adapter": "hf",
      "path": "models/shield",
      "ai_label_index": "auto",
      "max_length": 256,
      "device": "auto",
      "batch_size": 32,
      "win_sentences": 8,
      "stride_sentences": 2,
      "cap_windows": 30
    }
  ],
  "judges": [
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
  ],
  "default_judge": "mean-bar"
}
```

| Field | Meaning |
| --- | --- |
| `adapter` | `hf`, `openai`, or `http`. |
| `path` | HF checkpoint directory, relative to the repo root. |
| `ai_label_index` | `"auto"` (read `id2label`), or `0` / `1`. |
| `device` | `auto`, `cpu`, `cuda`, `cuda:1`, ... |
| `max_length` | Tokenizer truncation per window. Original: 256. |
| `win_sentences` / `stride_sentences` / `cap_windows` | Window pipeline. Original: 8 / 2 / 30. |
| `aliases` | Optional extra names accepted by `/score` and `/batch`. |
| `base_url` / `model` | OpenAI-compatible endpoint and model tag. |
| `url` / `field` | Custom HTTP scorer and response field. |

Environment variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `FAIRDETECT_CONFIG` | `config/models.json` | Config path. |
| `FAIRDETECT_PORT` | `8790` | HTTP port. |
| `FAIRDETECT_HOST` | `127.0.0.1` | Bind address. |
| `FAIRDETECT_CONSOLE_TOKEN` | from `server/service-token.txt` if present | Bearer token for `/score` and `/batch`. |

---

## HTTP API

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/health` | no | Liveness + model availability. |
| GET | `/api/models` | no | Models, judges, availability. |
| POST | `/api/jobs` | no | Upload files and run a job. |
| GET | `/api/jobs/{id}` | no | Job status + results. |
| GET | `/api/jobs/{id}/report` | no | Standalone HTML report. |
| GET | `/api/jobs/{id}/pdf` | no | PDF via headless Edge/Chrome. |
| POST | `/score` | token if set | Score one text. |
| POST | `/batch` | token if set | Score many texts. |

The browser UI uses `/api/jobs`. The `score` and `batch` endpoints are for other local tools.

---

## Measured results (original models, frozen pools)

These numbers come from the original `r11-shield:ep1` × `r10-spear:ep0` pair at the Judge 4.0 operating point. They are **not** the results of whatever model you attach.

| Metric | Result |
| --- | --- |
| AHBench-10 AI detection | **3 / 363 missed** (0.83%) |
| Strongly humanized AI | **2 / 23 missed** (8.7%) |
| Human frozen pool (1,595 docs) | **99.418% pass** (10 false positives) |
| Human holdout, ESL learners (2,649 docs) | **97.55% pass** (2.45% false positives) |
| Human holdout, MICUSP academic writing (829 docs) | **73.34% pass** (26.66% false positives) |
| MICUSP native speakers (681 docs) | **71.07% pass** (28.93% false positives) |
| MICUSP non-native speakers (148 docs) | **83.78% pass** (16.22% false positives) |
| All human holdout (3,478 docs) | **91.78% pass** (8.22% false positives) |

### How to read this

- **The 99.4% frozen-pool number is optimistic.** The operating point was tuned on pools that include the evaluation material. The honest number is the 3,478-document holdout: **8.22% of human documents were flagged**.
- **Writing ability correlates with false positives.** The better the human academic prose, the more likely it is to be flagged. This is the largest known defect.
- **The strong-humanized set is only 23 documents.** One document moves the percentage by 4.35 points. Treat it as a directional signal, not a stable estimate.
- **The AI-side threshold was selected on the evaluation pool.** "3/363" carries selection bias; an independent threshold set was never completed.
- **These are not probabilities that an author used AI.** They are shares of text/windows that cross a model-specific bar.

Full detail: [docs/EVALUATION.md](docs/EVALUATION.md).

---

## Known limitations

1. **High-ability human academic writing is over-flagged** (MICUSP 26.7% at the v4 operating point; native speakers 28.9%). This is a model-level problem; changing the threshold alone does not fix it.
2. **Humanized AI can be missed.** The 23-document set is too small to claim robustness.
3. **Document structure changes scores.** Removing section headings changed the spear mean from 0.932 to 0.743 on one document, flipping the verdict. The pipeline is sensitive to sentence and window alignment.
4. **Only the first 30 windows are scored.** Long documents are effectively truncated around the first ~240 sentences.
5. **English-centric sentence splitting.** The splitter expects Latin punctuation and capitalization.
6. **Texts shorter than 4 sentences are rejected.**
7. **No Turnitin calibration.** The report looks like a Turnitin report; the numbers are not the same quantity and cannot be converted.
8. **No adversarial robustness.** Paraphrase and style-transfer attacks are out of scope.
9. **The LLM adapter is not a detector.** It is a way to connect a local model to the pipeline; its probabilities are prompt-sensitive.
10. **The console is a research tool, not a service.** No multi-user auth, no rate limits, no audit log.

More: [docs/LIMITS.md](docs/LIMITS.md).

---

## Fair use and ethics

- **Do not use this to accuse, punish, or surveil anyone.** A flag is a reason to look at the text, not a conclusion about the author.
- **Keep student texts local.** The server stores uploaded text in memory for the life of the process and writes reports/PDFs under `ops-reports/`. It does not call external services unless you configure an adapter that does.
- **Do not send FERPA / GDPR / institutional data to a third-party API** through this tool.
- **The original weights are not distributed** because their training corpora include resources with registration or license restrictions.
- **Turnitin is a trademark of Turnitin, LLC.** This project is not affiliated with or endorsed by Turnitin.

---

## Repository layout

```
FairDetect/
  app/                 React review console (source + built dist)
  server/
    fairdetect_api.py  HTTP server, jobs, report rendering
    adapters.py        hf / openai / http model adapters
    report_zh.json     report strings
  judge/judge.py       portable CLI
  config/              model and judge definitions
  models/              your checkpoints (git-ignored)
  docs/                evaluation, limits, contract, architecture, ethics
  examples/            synthetic smoke-test texts
  scripts/             setup check and launchers
  requirements.txt
```

---

## License

MIT. See [LICENSE](LICENSE).

## Citation

```bibtex
@misc{fairdetect2026,
  title  = {FairDetect: a local-first AI-text detection research prototype},
  author = {FairDetect contributors},
  year   = {2026},
  url    = {https://github.com/profanebs/FairDetect}
}
```
