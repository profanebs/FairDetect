# Architecture

FairDetect is a small local application with four layers: input, windowing, scoring, and judgment/reporting.

```
Browser UI (React)
      |
      | POST /api/jobs (base64 files)
      v
HTTP server (Python stdlib)
      |
      +--> extract text (.docx via python-docx, .txt/.md as UTF-8)
      +--> split sentences
      +--> build windows
      +--> score each window with one or more adapters
      +--> aggregate per-sentence and document-level values
      +--> apply judge rule
      +--> render HTML report (and optional PDF)
      |
      v
JSON results + standalone HTML
```

## 1. Input

The browser accepts `.docx`, `.md`, `.txt`, and pasted text. Files are base64-encoded and posted to `/api/jobs`. The server decodes them and extracts text:

- `.docx`: paragraphs and table cells, joined with blank lines.
- everything else: decoded as UTF-8 with replacement.

A document with fewer than 30 words is rejected. A document with fewer than 4 sentences produces no score.

## 2. Sentence splitting and windows

```python
sentences = split on (?<=[.!?])\s+(?=[A-Z"'(])
```

Then:

```
if n <= 8:      one window (0, n)
else:           start at 0, step 2, length 8, until 30 windows
                append a tail window (n-8, n) if there is room
```

This is the **window pipeline**. It is deliberately simple and English-centric. The parameters are configurable per model (`win_sentences`, `stride_sentences`, `cap_windows`).

## 3. Scoring

Each adapter receives a list of window strings and returns one probability per window. The adapter layer is described in [MODEL-CONTRACT.md](MODEL-CONTRACT.md).

Scores are **not** averaged across models. Each model keeps its own per-window list.

## 4. Aggregation

For a model with per-window scores `s[0..k-1]`:

| Value | Definition |
| --- | --- |
| `mean` | mean of `s` |
| `pct50` | 100 * share of `s >= 0.5` |
| `pct80` | 100 * share of `s >= 0.8` |
| `s90` | 100 * share of `s >= 0.9` |
| `mx` | max of `s` |
| `mean100` | 100 * mean of `s` |

For per-sentence values, each sentence gets the mean of the windows that cover it. A sentence covered by two windows gets the average of both.

The **AI reference rate** (`ai_rate`) is computed by applying the judge bar sentence by sentence:

```
flagged(i) = (shield_sentence[i] >= g0) or (spear_sentence[i] >= r0)
rate_word  = 100 * sum(words of flagged sentences) / sum(words of all sentences)
rate_sent  = 100 * count(flagged) / count(sentences)
```

This is a share of text, not a probability of authorship.

## 5. Judgment

The judge is a pure function of the model scores. It does not know which models produced them. Two modes exist:

- `mode: "or"` (modern): mean-bar rule, thresholds in `0..1`.
- `mode: "max"` (legacy): percentage-based rule, thresholds in `0..100`.

The modern rule:

```
S = 100 * max(g, r)
caught = (g >= g0) or (r >= r0)
flag = (not caught) and (r >= 0.90)
tier = "caught" if caught else "t2"
band = "low" if S < 20 else ("mid" if S < 80 else "high")
```

A single-model judge sets `shield == spear`; the model is scored once and the same value is used on both sides.

## 6. Report

`report_html(job)` renders a standalone HTML document with:

1. a cover page (submission id, file size, time, windows);
2. an overview (AI reference rate, verdict, thresholds);
3. the document body with per-sentence highlighting;
4. a collapsible appendix with model scores and a window strip.

The report is self-contained: CSS is inline, no external assets. The PDF endpoint prints it with headless Edge or Chrome.

The report deliberately resembles a Turnitin report for readability. It is not a Turnitin report, and the numbers are not the same quantity.

## 7. Process and security model

- One Python process, one HTTP server, one background thread per job.
- Jobs are stored in an in-memory dict (`JOBS`). They are lost on restart.
- Uploaded text is held in memory; `_text` is stripped from API responses.
- Reports and PDFs are written to `ops-reports/`.
- The server binds `127.0.0.1` by default. `/api/jobs` is unauthenticated; `/score` and `/batch` use a Bearer token if one is configured.
- No telemetry, no analytics, no external calls except the adapters you configure.

## 8. Why two models

The original project found that a single classifier cannot simultaneously satisfy two goals:

- high recall on AI/humanized AI;
- low false positives on human writing.

A model trained toward one goal degrades the other. The shield/spear split makes the trade-off explicit and lets the judge choose the operating point. It is not a claim that two models are always better; it is a design response to a measured conflict.

## 9. Why the model adapter layer exists

The original checkpoints cannot be redistributed. A repository without weights would be a dead demo. The adapter layer turns it into a framework: the pipeline, the UI, the judge, and the report are reusable; the model is supplied by the user. That is the only honest way to publish this work.
