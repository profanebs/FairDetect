# Training

How the original checkpoints were built. These are the models behind the numbers in [EVALUATION.md](EVALUATION.md) and [RESULTS.md](RESULTS.md). They are not required to use the pipeline; see [MODEL-CONTRACT.md](MODEL-CONTRACT.md) if you want to attach your own model.

The training code is not included in this repository. It depends on corpora that cannot be redistributed (see [Data sources](#4-data-sources)).

---

## 1. Architecture in one paragraph

Both classifiers are **DeBERTa-v3-base** fine-tuned for binary sequence classification (`DebertaV2ForSequenceClassification`, two labels: human / AI). The base model has roughly 86M backbone parameters; the saved checkpoint is 711 MB in float32. Inference runs on CPU or a single consumer GPU.

The two models are not two sizes of the same thing. They are two **different training objectives**:

| Role | Internal name | Objective | Failure it is tuned to avoid |
| --- | --- | --- | --- |
| Shield | `r11-shield:ep1` | Avoid flagging human writing | False positives on real human text |
| Spear | `r10-spear:ep0` | Catch AI and humanized AI | Missed AI text |

A single model cannot do both. The measured evidence is in [RESULTS.md §3](RESULTS.md#3-why-two-models): the shield alone reaches 0/363 missed on AHBench but flags 23% of a human academic pool; the spear alone passes 99.6% of human documents but misses 10/363 AI documents.

---

## 2. Window construction

Training and inference share the same window definition:

```
text -> sentence split -> 8 consecutive sentences per window
     -> stride 2 sentences -> cap 30 windows per document
     -> tokenizer truncation at 256 tokens per window
```

Each window is a training example. The label is inherited from the document (all windows of an AI document are positive, all windows of a human document are negative). This is noisy at the edges — a human document can contain an AI-sounding paragraph — but it scaled better than sentence-level annotation, which does not exist at this size.

At the r5 stage the training set contained roughly **37,000 windows** (of which about 8,200 were AI) and the validation set about **8,200 windows**. Later generations expanded this substantially (see §3).

---

## 3. Generations

Five generations were trained. Each one was evaluated on frozen pools that never entered training; the full table is in [RESULTS.md](RESULTS.md).

| Generation | Produced | What changed | Key result |
| --- | --- | --- | --- |
| r5 | 2026-10-05 | First DeBERTa window classifier, W&I + ghostbuster data | Human false positives halved vs the earlier single-signal approach |
| r6 | 2026-10-07 | Added AHBench-09 humanized outputs to training | Humanized-AI recall jumped; human false positives rose |
| r7 | 2026-10-07 | Split into shield (`r7-general`, `r7-shield`) and spear (`r7-spear`) | The two-objective split becomes explicit |
| r8 | 2026-10-08 | New humanized data, hard-window mining | 0% miss on an external 50-document corpus; human side held |
| r9 | 2026-10-09 | More red-team data, stronger spear | AHBench miss 3.0%, strongly-humanized miss 26.1% |
| r10 | 2026-10-14 | Shield 2.0 (`r10-shield`) + Spear 4.0 (`r10-spear`) | Judge 3.0 shipped; best spear so far |
| r11 | 2026-10-15/16 | Shield 3.0 (`r11-shield`) | Judge 4.0 shipped; MICUSP false positives dropped roughly 3x from ep0 to ep1 |

Two training-discipline findings that generalised across generations:

1. **The second epoch is usually worse.** For the spear, `ep0` consistently outperformed `ep1` and `final` on frozen pools (AHBench miss 4.1% at ep0 vs 9.9% at final in r9). The checkpoints are saved per epoch and the best one is selected on frozen pools — not on the training loss.
2. **Targeted oversampling works, but it moves the failure.** Adding WEP-style learner essays as hard negatives cut the ICNALE false positives from 59/1,129 to 16/1,129 in `r11-shield:ep0`, while making other human pools much worse (newc 8/238 to 76/238). The two kinds of false positive are not the same defect.

---

## 4. Data sources

The training mixture combines public learner corpora, public humanized-AI benchmarks, and internally generated red-team samples.

| Source | What it is | License / terms | Role |
| --- | --- | --- | --- |
| W&I + LOCNESS (BEA-2019) | Learner and native student essays, CEFR-graded | Competition data, research use | Human side, ESL domain |
| PELIC | University EAP learner essays, ~4.2M words | **CC BY-NC-ND** (non-commercial, no derivatives) | Human side, ESL domain |
| ICNALE | Asian learner English corpus, registered access | Registered use, no redistribution | Human side + evaluation |
| ghostbuster | Human and six-generator AI text | Public research dataset | AI side |
| AHBench (AI Humanizer Benchmark) | 11 humanizer tools × multiple releases | CC BY 4.0 | AI side (earlier releases only) + external evaluation |
| Red-team corpus | Native and humanized AI documents produced for this project | Internal | AI side (training) and evaluation (held out) |

The largest training file used for the shield (`r11-shield`) contains **146,094 windows**; the file prepared for a next-generation spear contains **237,138 windows** and was frozen before training (the `r11-spear` run was never completed).

### Zero-overlap assertion

Before any model is trained, the training windows are checked against every evaluation pool at the window level. The build asserts **0 overlapping windows** against the frozen evaluation sets and the ESL reserve. This is enforced in the data-preparation step, not checked by hand.

### What is not redistributed

No corpus text, no student text, and no per-document scores are in this repository. The model weights are released separately (see the release attached to this repository) under a research-use, non-commercial terms because the corpora above carry non-commercial or no-redistribution terms.

---

## 5. Training configuration

The configuration was held constant across generations so that differences between generations reflect data, not hyperparameters:

```
base model      microsoft/deberta-v3-base
max_length      256 tokens per window
batch size      16
epochs          2 (checkpoints saved at ep0, ep1, final)
learning rate   2e-5
seed            0
loss            cross-entropy, 2 labels
```

At this size, one generation trains in about **21 minutes on a single RTX 3060 Ti**. Training is not the bottleneck; data preparation and evaluation are.

---

## 6. Evaluation protocol

Training decisions were made against the protocol in [EVALUATION.md](EVALUATION.md):

- **Tune pools** are used to choose thresholds and model checkpoints.
- **Holdout pools** are scored once, after the rule is frozen, and are never used to revise the rule.
- **Frozen pools** never enter training and are reported with their historical status (some are optimistic because they were used for earlier selection).
- A material set is registered as tune or holdout before it is used, and its role never changes afterwards.

The strongest evidence in this project comes from the holdout pools (NUCLE + PELIC + MICUSP, 3,478 documents) because they were never scored before the final check.

---

## 7. What we would do differently

- Build the independent AI-side threshold set **before** tuning, not after. The current AI numbers carry selection bias because the threshold and the evaluation used the same pool.
- Expand the strongly-humanized set from 23 documents to at least 100 before making any ranking claim. At 23 documents, one document moves the metric by 4.35 points.
- Train the shield with hard negatives from high-ability academic writing (MICUSP-style) rather than only learner corpora. The current shield is excellent on ESL essays and weak on polished academic prose, which is the opposite of what a general-purpose tool needs.
