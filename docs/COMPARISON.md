# Comparison with commercial detectors

This document collects every external comparison we have, and states what each one is worth. The short version: **we have one batch where our numbers and seven commercial detectors were measured on humanized AI outputs from the same benchmark, and it is not a clean head-to-head.**

---

## 1. The AHBench comparison

[AI Humanizer Benchmark](https://huggingface.co/datasets/AIHumanizerBenchmark/ai-humanizer-benchmark) publishes humanized AI outputs plus the verdicts of seven commercial detectors. The 2026-10 release contains 363 documents across 11 humanizer tools. Our models were scored on that release.

Miss rate (lower is better):

| Detector | Miss rate |
| --- | --- |
| **FairDetect Judge 4.0** (r11-shield ep1 × r10-spear ep0) | **0.83%** (3/363) |
| **FairDetect Spear 3.0** (r9 ep0, earlier) | **3.0%** |
| GPTZero | 48.7% |
| Copyleaks | 50.1% |
| Originality.ai | 57.2% |
| Winston AI | 59.1% |
| QuillBot | 72.8% |
| ZeroGPT | 74.5% |
| Grammarly | 78.3% |

### What this comparison is

- Same benchmark, same document set for the AI side.
- Our numbers come from our own scoring run on the 363-document release.
- The commercial numbers come from the benchmark's published verdicts, which average **two releases** (2026-09 and 2026-10) across 11 humanizer tools.

### What it is not

- **Not a clean head-to-head.** The commercial figures average two releases; ours are from one. The benchmark's own methodology notes that humanizer tools change monthly.
- **Not a claim about general AI detection.** This benchmark measures detection of **humanized** output from 11 specific tools. A detector can be excellent here and ordinary on raw model output.
- **Not a claim about all seven vendors' current versions.** The published verdicts are a snapshot. Vendors retrain every 3–6 months.
- **Not an independent audit.** We did not run the commercial APIs ourselves.

The direction is large enough to survive those caveats — a 0.8% miss rate against a 49–78% range is not a rounding difference — but the exact gap should be read as "order of magnitude on this benchmark", not as a measured ratio.

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
