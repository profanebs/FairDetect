# Comparison with commercial detectors

This document collects every external comparison we have, and states what each one is worth. The short version: **we have one batch where our numbers and seven commercial detectors were measured on humanized AI outputs from the same benchmark, and it is not a clean head-to-head.**

---

## 1. The AHBench comparison

[AI Humanizer Benchmark](https://huggingface.co/datasets/AIHumanizerBenchmark/ai-humanizer-benchmark) publishes humanized AI outputs plus the verdicts of seven commercial detectors. The 2026-10 release contains 363 documents across 11 humanizer tools. Our models were scored on that release.

Two different statistics are involved, and they cannot be compared directly:

| Detector | Statistic | Value |
| --- | --- | --- |
| **FairDetect Judge 4.0** (r11-shield ep1 × r10-spear ep0) | document-level miss rate | **0.83%** (3/363) |
| **FairDetect Spear 3.0** (r9 ep0, earlier) | document-level miss rate | **3.0%** |
| GPTZero | mean human-probability | 0.487 |
| Copyleaks | mean human-probability | 0.501 |
| Originality.ai | mean human-probability | 0.572 |
| Winston AI | mean human-probability | 0.591 |
| QuillBot | mean human-probability | 0.728 |
| ZeroGPT | mean human-probability | 0.745 |
| Grammarly | mean human-probability | 0.783 |

The commercial figures are each detector's **mean human-probability** over the benchmark's humanized outputs, averaged across two cycles. This was verified by recomputing both statistics from the benchmark's per-output scores: the seven published figures match the mean `human_prob` exactly.

If the commercial verdicts are converted to a binary "judged human" rate, the same order gives 14.2%, 49.7%, 19.6%, 37.7%, 46.4%, 28.4%, 49.4%. That column is not published as the main comparison because the benchmark's binary verdicts are internally inconsistent across cycles (one detector records zero human verdicts in one cycle while its mean human-probability for that cycle is 0.42) and is not fit to publish.

**Do not read 0.83% against 48.7–78.3% as the same quantity.** One is a decision rate; the other is a mean score. The honest statement is: on the same humanized-AI benchmark, FairDetect's document-level miss rate is under 1%, while the published commercial mean human-probabilities are 0.49–0.78 — different statistics, same direction.

### What this comparison is

- Same benchmark, same document set for the AI side.
- Our numbers come from our own scoring run on the 363-document release.
- The commercial numbers are **mean human-probabilities**, not verdict rates, averaged over **two releases** (2026-09 and 2026-10) across 11 humanizer tools.
- The binary commercial verdict column exists in the benchmark but is internally inconsistent across cycles, so it is not used as the headline comparison.

### What it is not

- **Not a like-for-like statistic.** Our number is a document-level decision rate; theirs is a mean score. A detector that averages a 0.49 human-probability can still catch most documents at its own threshold.
- **Not a clean head-to-head.** The commercial figures average two releases; ours are from one. The benchmark's own methodology notes that humanizer tools change monthly.
- **Not a claim about general AI detection.** This benchmark measures detection of **humanized** output from 11 specific tools. A detector can be excellent here and ordinary on raw model output.
- **Not a claim about all seven vendors' current versions.** The published verdicts are a snapshot. Vendors retrain every 3–6 months.
- **Not an independent audit.** We did not run the commercial APIs ourselves.

The direction survives those caveats: a sub-1% document-level miss rate against commercial mean human-probabilities of 0.49–0.78 is a large gap on any reading. The exact multiplier is not defensible because the statistics differ.

---

## 2. The 723-document comparison (earlier model)

A larger internal run used two AHBench releases (723 documents) and compared the then-current r5 model against the same seven detectors, using each detector's "flagged as AI" threshold:

| Detector | Documents passed as human (lower = stricter) |
| --- | --- |
| **FairDetect r5** | **28%** (72% detected) |
| Copyleaks | 50% |
| GPTZero | 50% |
| Originality.ai | 58% |
| Winston AI | 59% |
| QuillBot | 75% |
| ZeroGPT | 80% |
| Grammarly | 82% |

This is the same direction, on an earlier and weaker model. It is included because it is the only place where both sides were computed over the identical 723-document set with a single stated rule.

Three of the eleven humanizers beat r5 consistently: GPTinf, AI Humanize and CleverHumanizer. The model is not uniformly better than the commercial tools; it is better on the average of this benchmark.

---

## 3. Turnitin

Turnitin's AI score is not for sale and its model is not public. Seven documents were compared against real Turnitin reports:

| Sample | Truth | Turnitin | FairDetect @0.5 share | Judge 4.0 verdict |
| --- | --- | --- | --- | --- |
| Academic annotated bibliography | Human | 0% | 0.0% | pass |
| Humanized course essay | AI | 28% | 100% | miss |
| Native AI statement of intent | AI | 100% | 95.2% | caught |
| Manually humanized statement of intent | AI | pending | 78.9% | caught |
| Anchored humanized statement of intent | AI | 100% | 62.4% | miss |
| Academic proposal, model A | AI | below 20% (not displayed) | 18.3% | miss |
| Academic proposal, model B | AI | 76% | 87.8% | caught |

What this shows: on easy AI both systems agree; on strongly humanized AI both systems are inconsistent; per-document variance is huge for both. With seven documents, **no ranking claim is defensible**. The table exists to document that the two systems are not measuring the same quantity and that neither is reliable on a single document.

The two percentages are not the same number:

- Turnitin reports "share of qualifying text flagged as AI".
- FairDetect's `@0.5 share` is "share of words in sentences whose sentence-mean crosses the judge bar". This is the closest analogue.
- The Judge 4.0 verdict is a separate, conservative document-level decision. It is not the same as either percentage.

---

## 4. Published false-positive evidence

The reason this project exists is the false-positive literature, not the detection race:

- Liang et al. (2023), *Patterns*: seven GPT detectors flagged **61.3%** of TOEFL essays written by humans as AI-generated on average; the worst flagged **97.8%**.
- Turnitin states its AI score is a probability estimate that can produce false positives and must not be the sole basis for disciplinary action.
- Our own holdout: **2.45%** false positives on ESL learner essays and **26.66%** on high-ability academic writing.

The last line is the one to keep in view. A tool that is excellent on its target population can still be unsafe on an adjacent one, and that is exactly the failure mode this project was built to reduce.

---

## 5. How to cite these numbers

If you use them, cite the pool and the version:

> FairDetect Judge 4.0 (r11-shield ep1 × r10-spear ep0) missed 3/363 (0.83%) on the AHBench 2026-10 humanized-AI release, and passed 97.55% of 2,649 ESL learner essays in a held-out pool, while passing only 73.34% of 829 MICUSP academic papers. Commercial detector figures on the same benchmark are published by AI Humanizer Benchmark and average two releases; they are not results we produced.
