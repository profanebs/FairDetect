# Evaluation

This document records what was measured, on which pools, and what the numbers do and do not mean. It is deliberately pessimistic: the point is to prevent the figures from being read as more than they are.

All results below come from the **original internal models** (`r11-shield:ep1` × `r10-spear:ep0`) at the **Judge 4.0** operating point. They are not results of any model you attach.

---

## 1. Operating point

```
g = shield window-mean score (0..1)
r = spear  window-mean score (0..1)
caught  iff  g >= 0.32  OR  r >= 0.80
S       = 100 * max(g, r)
flag    if not caught and r >= 0.90
```

The thresholds are model-specific. They were selected on internal evaluation pools, not on an independent threshold set.

## 2. Window pipeline

```
text -> sentence split -> windows of 8 consecutive sentences
     -> stride 2 -> at most 30 windows
     -> tokenizer truncation 256 tokens per window
     -> classifier -> per-window p(AI)
```

Document-level values:

| Name | Definition |
| --- | --- |
| `mean` | Mean of per-window p(AI). Used by Judge 4.0. |
| `pct50` | Percentage of windows with p(AI) >= 0.50. |
| `pct80` | Percentage of windows with p(AI) >= 0.80. |
| `s90` | Percentage of windows with p(AI) >= 0.90. |
| `sents` | Per-sentence mean of the windows covering that sentence. |
| `ai_rate.rate_word` | Share of words in sentences whose sentence-mean crosses the judge bar. |
| `ai_rate.rate_sent` | Share of sentences crossing the judge bar. |

`mean` and `pct50` are different quantities. Do not compare them.

## 3. Pools

| Pool | Size | Role |
| --- | --- | --- |
| AHBench-10 | 363 AI documents | AI-side generalization probe. |
| Strongly humanized set | 23 documents | Humanized-AI probe. Very small. |
| Human frozen pool | 1,595 documents | Historical human-side check. Tuned-on, so optimistic. |
| NUCLE + PELIC | 2,649 documents | ESL learner holdout. Never used for training. |
| MICUSP | 829 documents | High-ability academic writing holdout. Never used for training. |
| Total human holdout | 3,478 documents | NUCLE + PELIC + MICUSP. |

The holdout pools were **never used for training** and were not scored before the final check. That is why they are the honest numbers.

## 4. Results

### 4.1 Judge 4.0 (published operating point)

| Metric | Result |
| --- | --- |
| AHBench-10 missed | 3 / 363 = **0.83%** |
| Strongly humanized missed | 2 / 23 = **8.7%** |
| Human frozen pool pass | **99.418%** (10 / 1,595 false positives) |
| Human holdout pass | **91.78%** (8.22% false positives) |
| ESL holdout pass | **97.55%** (2.45% false positives) |
| MICUSP pass | **73.34%** (26.66% false positives) |
| MICUSP native pass | **71.07%** (28.93% false positives) |
| MICUSP non-native pass | **83.78%** (16.22% false positives) |

### 4.2 How the operating point was chosen (and why that is a problem)

The AI-side threshold was selected on AHBench-10. The same pool is then used to report "3/363". This is a selection-bias loop. An independent threshold set (red-team corpus b02/b03) was planned but not completed. Treat the AI-side number as **optimistic**.

The human-side threshold was checked on held-out human pools, which is better, but the final operating point was still chosen with knowledge of those results.

### 4.3 Threshold trade-off experiment

A later experiment on 4,223 human documents and 745 AI documents compared alternative document-level statistics:

| Rule | AI caught | ESL false positive | MICUSP false positive |
| --- | --- | --- | --- |
| Judge 4.0 (mean bars 0.32 / 0.80) | 720 / 723 | 2.45% | **26.66%** |
| Window share >= 20% | 722 / 723 | 10.80% | 33.17% |
| Sentence share @0.8 >= 30% | 718 / 723 | 2.45% | **11.46%** |
| Sentence share @0.8 >= 40% | 717 / 723 | 1.81% | **7.84%** |

This showed that the **decision statistic** matters as much as the model. The sentence-share rule would cut high-ability human false positives by roughly half to two-thirds while losing 2–3 AI documents. It was **not** adopted: it needs independent validation, and the published Judge 4.0 numbers use the old rule.

## 5. External comparison (Turnitin)

Seven samples were compared with Turnitin reports. The results were mixed:

- Easy AI samples: both systems agree.
- Strongly humanized AI: FairDetect sometimes catches, sometimes misses; Turnitin sometimes catches, sometimes misses.
- One human sample: both pass.
- FairDetect's percentage and Turnitin's percentage are not the same quantity.

With seven samples, no ranking claim is defensible. The comparison is recorded only to show that per-document variance is large for both systems.

## 6. What was never done

- No independent AI threshold set.
- No calibration of the score to a probability of authorship.
- No large-scale humanized-AI set (23 documents is not enough).
- No multilingual evaluation. English only.
- No adversarial robustness evaluation (paraphrase, translation, style transfer).
- No inter-annotator agreement study for "humanized AI".
- No comparison with a representative random sample of commercial detectors.

## 7. Reproducing these numbers

The original training and evaluation code is not included, because it depends on corpora that cannot be redistributed. The inference pipeline and judge rule in this repository are the same ones used for the results. If you have the original checkpoints, put them in `models/` and use the config in `config/models.json` with `ai_label_index` set correctly. The window parameters (`8 / 2 / 30`, `max_length 256`) and the judge rule (`0.32 / 0.80`, mean) are the published values.

## 8. Reporting rule

If you publish results with this tool, state:

1. which model/checkpoint you used (name + hash);
2. the operating point and how it was selected;
3. the human false-positive rate on a held-out set;
4. the size of every pool;
5. that the score is not a probability of authorship and is not Turnitin-calibrated.
