# FairDetect: a local-first AI-text detector for non-native academic writing

**Technical report · 2026-11** · This report summarises the design, the experiments and the results behind the released model pair. The formal paper is in preparation; this document is the engineering record.

---

## Abstract

Commercial AI-text detectors over-flag non-native English writers. We built a local, inspectable alternative around two small fine-tuned DeBERTa classifiers — a *shield* trained to avoid flagging human writing and a *spear* trained to catch AI and humanized AI — combined by a separate decision layer. At the published operating point (Judge 4.0), the system misses 3 of 363 humanized-AI documents in the AHBench 2026-10 release (0.83%) while passing 97.55% of 2,649 held-out ESL learner essays. Its main weakness is the opposite of its target: it flags 26.66% of high-ability human academic writing (MICUSP). We report that failure prominently because it bounds what the tool may be used for.

---

## 1. Problem

The detector market optimises for catching AI. That objective, applied to non-native writing, produces a specific harm: learners who write in a formulaic academic register are statistically indistinguishable from generated text to style-based detectors. Liang et al. (2023) measured an average 61.3% false-positive rate on human TOEFL essays across seven detectors.

The question we asked is narrower than "can AI text be detected":

> Can a detector be built that is *conservative on human writing* — especially learner writing — and still catches humanized AI?

"Conservative" is a design constraint, not a slogan. It means the human false-positive rate is the primary metric, and AI recall is maximised subject to it.

---

## 2. System

### 2.1 Window pipeline

```
document -> sentence split -> 8-sentence windows, stride 2, cap 30
         -> tokenizer truncation at 256 tokens -> classifier -> p(AI) per window
```

Document-level statistics are computed over the windows: the mean (used by the judge), the share above 0.5, the share above 0.8, and per-sentence means.

### 2.2 Two classifiers

A single classifier could not satisfy both objectives. Measured on frozen pools:

| Configuration | AI missed (AHBench) | Human false positives |
| --- | --- | --- |
| One aggressive model | 0/363 | 157/1,595 (9.8%) |
| One conservative model | 10/363 | 9/1,595 (0.6%) |

The aggressive model achieves perfect AI recall by flagging roughly one in ten human documents; the conservative one is clean on humans and blind to a subset of AI. Both are 711 MB DeBERTa-v3-base checkpoints.

### 2.3 Judge layer

The decision rule is separate from the models, so the operating point can move without retraining:

```
g = shield window-mean, r = spear window-mean
caught iff g >= 0.32 OR r >= 0.80
```

The `OR` is deliberate. A humanized sample often collapses the shield to zero while the spear still sees it; a serial "shield first, then spear" design deadlocks on exactly those samples. We measured this: humanized samples scored shield 0.000–0.025 while the spear scored 0.666–0.935.

### 2.4 Why small models

Inference runs on CPU in 0.6–13 seconds per document (5–30 windows). No API, no GPU requirement, no text leaving the machine. The constraint that made this possible is the window design: a document becomes at most 30 short sequences, which a 86M-parameter encoder handles comfortably.

---

## 3. Data

| Source | Role | Licence |
| --- | --- | --- |
| W&I + LOCNESS (BEA-2019) | Human, learner + native | Competition terms |
| PELIC | Human, EAP | CC BY-NC-ND |
| ICNALE | Human, Asian learners | Registered use |
| ghostbuster | Human + 6 generators | Public research |
| AHBench | Humanized AI | CC BY 4.0 |
| Red-team corpus | Native + humanized AI | Internal |

Training windows never overlap evaluation windows; the build asserts zero overlap against every evaluation pool. Evaluation pools are registered as tune or holdout before use and never change role. This discipline matters more than any single model choice: it is what makes the reported numbers interpretable.

---

## 4. Results

### 4.1 Published operating point (Judge 4.0)

| Pool | n | Result |
| --- | --- | --- |
| AHBench-10 humanized AI | 363 | 3 missed (0.83%) |
| Strongly humanized set | 23 | 2 missed (8.7%) |
| ESL learner holdout | 2,649 | 97.55% pass |
| High-ability academic holdout (MICUSP) | 829 | 73.34% pass |
| Human frozen pool (tuned-on) | 1,595 | 99.42% pass |

The gap between the frozen pool and the holdout is the honest measure of selection bias: 99.42% versus 91.78% overall.

### 4.2 Commercial comparison

On the same AHBench humanized-AI benchmark, Judge 4.0 misses 0.83% of documents at the document level. The benchmark publishes each commercial detector's **mean human-probability** — 0.487 (GPTZero), 0.501 (Copyleaks), 0.572 (Originality.ai), 0.591 (Winston), 0.728 (QuillBot), 0.745 (ZeroGPT), 0.783 (Grammarly), averaged over two cycles. These are mean scores, not decision rates; they cannot be divided by our miss rate. Converted to a binary "judged human" rate the same detectors range 14.2%–49.7%, but that column is internally inconsistent across cycles and is not used as the headline. Details and caveats: [COMPARISON.md](COMPARISON.md).

### 4.3 Decision statistic

The largest single improvement we found is not a better model but a better statistic. Replacing the window mean with the share of high-confidence sentences:

| Rule | MICUSP false positive | AI caught |
| --- | --- | --- |
| Window mean (published) | 26.66% | 720/723 |
| Sentence share @0.8 >= 30% | 11.46% | 718/723 |
| Sentence share @0.8 >= 40% | 7.84% | 717/723 |

Cutting high-ability false positives by half to two-thirds at the cost of 2–3 AI documents is the best trade we have measured. It is not in the published rule because it has not been validated on an independent threshold set.

---

## 5. Three findings worth keeping

**1. Humanized AI collapses the shield, not the spear.** Across every humanized sample measured, the shield scored 0.000–0.025 while the spear scored 0.666–0.935. Any architecture that gates the spear behind the shield will systematically miss humanized text. The `OR` rule is a direct consequence.

**2. Document structure moves the score.** Removing nine section headings from one document changed the spear mean from 0.932 to 0.743, flipping the verdict. The pipeline splits on sentence boundaries; headings and short lines change the alignment. Cross-document comparisons require a fixed preprocessing convention.

**3. Scores are checkpoint-specific.** The same humanized document scored 90.7, 0.0 and 72.9 under three successive spear generations. A score is not a stable property of the text. Deployments must pin a version.

---

## 6. Limitations

The system must not be used as the sole basis for an accusation. Specifically:

- **26.66% false positives on high-ability human academic writing.** This is a model-level defect; threshold adjustment trades AI recall for it but does not remove it.
- **AI-side numbers are optimistic.** The threshold was selected on the same pool used to report it. An independent threshold set was planned but not completed.
- **The humanized-AI set is 23 documents.** One document moves the metric by 4.35 points.
- **English only, 30 windows maximum, four-sentence minimum.**
- **No adversarial robustness evaluation.**
- **The score is not a probability of authorship and is not Turnitin-calibrated.**

Full list: [LIMITS.md](LIMITS.md).

---

## 7. Conclusion

A small, local, two-model system with a transparent decision layer can be substantially more conservative on learner writing than the commercial baseline while remaining competitive on humanized AI. The bottleneck is not model capacity; it is data discipline and the choice of decision statistic. The largest unresolved defect — over-flagging strong human academic prose — is a training-data problem, not a threshold problem, and is stated here rather than hidden.

The released checkpoints and the inference pipeline are everything needed to reproduce the numbers in this report. The training code is not released because the corpora cannot be redistributed.

---

## References

- Liang, W. et al. (2023). GPT detectors are biased against non-native English writers. *Patterns*, 4(7).
- AI Humanizer Benchmark (2026). Hugging Face dataset `AIHumanizerBenchmark/ai-humanizer-benchmark`.
- Walters, W. H. (2023). The effectiveness of software designed to detect AI-generated writing.
- Turnitin (2024–2026). AI writing detection: public documentation and limitations statements.
