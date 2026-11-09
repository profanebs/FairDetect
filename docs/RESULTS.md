# Results

All numbers below were produced by the original checkpoints at the Judge 4.0 operating point or earlier published operating points, and were recomputed from per-document score files. They are **not** results of any model you attach yourself.

Read [EVALUATION.md](EVALUATION.md) first for what each pool means. The short version: AI-side numbers are optimistic (threshold and evaluation share a pool), human-side holdout numbers are the honest ones.

---

## 1. Judge 4.0 (the published operating point)

Rule: `caught iff shield window-mean >= 0.32 OR spear window-mean >= 0.80`.

| Pool | Size | Result |
| --- | --- | --- |
| AHBench-10 (humanized AI, held out) | 363 | **3 missed = 0.83%** |
| Strongly humanized set | 23 | **2 missed = 8.7%** |
| Human frozen pool (tuned-on, optimistic) | 1,595 | **99.42% pass** (10 false positives) |
| Human holdout, all | 3,478 | **91.78% pass** (8.22% false positives) |
| ESL learner holdout (NUCLE + PELIC) | 2,649 | **97.55% pass** (2.45% false positives) |
| High-ability academic holdout (MICUSP) | 829 | **73.34% pass** (26.66% false positives) |
| MICUSP native speakers | 681 | **71.07% pass** (28.93% false positives) |
| MICUSP non-native speakers | 148 | **83.78% pass** (16.22% false positives) |

The gap between the frozen pool (99.42%) and the holdout set (91.78%) is the clearest sign that a tuned-on pool is optimistic. Quote the holdout numbers.

---

## 2. Generations on the AI side

Miss rate, lower is better. Numbers from frozen external pools that never entered training for that generation. Pools change between generations, so compare within a row group, not across.

| Generation | AHBench-10 | External 50-doc corpus | Strongly humanized |
| --- | --- | --- | --- |
| Spear 1.0 (r6) | 5.0% | 4.0% | 95.7% |
| Spear 2.0 (r8 ep0) | 4.1% | 0% | 30.4% |
| Spear 3.0 (r9 ep0) | **3.0%** | 0% | 26.1% |
| Spear 3.0 (r9 final) | 9.9% | 0% | 69.6% |
| Spear 4.0 (r10 ep0) | **1/363 = 0.28%** | — | **1/23 = 4.3%** |
| Shield 3.0 (r11 ep0) | 0/363 | — | 0/23 |
| **Judge 4.0 pair** | **3/363 = 0.83%** | — | **2/23 = 8.7%** |

Two things to notice:

- **The second epoch is worse.** `r9 final` misses 9.9% where `r9 ep0` misses 3.0%. Checkpoints are selected per epoch on frozen pools.
- **The strongest AI-side combination is not the published one.** `r11-shield:ep0 × r10-spear:ep0` reaches 0/363 and 0/23, but it flags 23% of a human academic pool (see §3). It was rejected for that reason.

---

## 3. Why two models

The single-model attempts, same pools:

| Configuration | AHBench missed | Strongly humanized missed | Human five-pool macro | False positives |
| --- | --- | --- | --- | --- |
| Shield alone (`r11-shield:ep0`) | **0/363** | **0/23** | 76.69% | 157 / 1,595 |
| Shield alone (`r11-shield:ep1`) | 3/363 | 2/23 | 97.24% | 26 / 1,595 |
| Spear alone (`r10-spear:ep0`, mean >= 0.70) | 10/363 | 3/23 | **99.64%** | **9 / 1,595** |
| Pair + Judge 4.0 | 3/363 | 2/23 | 99.42% | 10 / 1,595 |

The two objectives genuinely conflict. The shield can achieve perfect AI-side numbers only by becoming aggressive enough to flag a quarter of real academic writing. The spear is the opposite: excellent on humans, blind to a subset of AI. The judge layer combines them at a chosen operating point.

---

## 4. The decision statistic matters as much as the model

An experiment on 4,223 human documents and 745 AI documents compared document-level statistics using the same model pair:

| Rule | AI caught | ESL false positive | MICUSP false positive |
| --- | --- | --- | --- |
| Judge 4.0 (mean bars 0.32 / 0.80) | 720 / 723 | 2.45% | **26.66%** |
| Window share >= 20% | 722 / 723 | 10.80% | 33.17% |
| Sentence share @0.8 >= 30% | 718 / 723 | 2.45% | **11.46%** |
| Sentence share @0.8 >= 40% | 717 / 723 | 1.81% | **7.84%** |

Switching to "share of high-confidence sentences" cuts the high-ability human false-positive rate by half to two-thirds while losing 2–3 AI documents. This was **not adopted** in the published version because it needs independent validation, and because the published Judge 4.0 numbers use the old rule. It is the most promising single change we know of.

---

## 5. Cross-generation instability (a warning, not a result)

The same document across model generations:

| Document | Spear r6 | Spear r9 | Spear r10 | Shield r11 | Shield r10 |
| --- | --- | --- | --- | --- | --- |
| Strongly humanized AI sample | 90.7 | **0.0** | 72.9 | 0.0 | 0.1 |
| Human-written sample | 77.3 | 0.4 | 21.5 | 0.0 | 0.2 |

A score is not a stable property of the text; it is a property of the text and the checkpoint. Any deployment should pin a model version and re-validate before switching. This is also why we publish the checkpoint alongside the code: the numbers only mean something with the exact pair that produced them.

---

## 6. What is not measured

- No independent AI-side threshold set. The current AI numbers are optimistic.
- No large humanized-AI set. 23 documents is not enough for a stable estimate.
- No multilingual evaluation.
- No adversarial robustness (paraphrase, back-translation, style transfer).
- No calibrated probability of authorship.
- No representative random sample of commercial detectors (see [COMPARISON.md](COMPARISON.md) for why the available comparison is not that).
