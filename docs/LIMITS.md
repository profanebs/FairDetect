# Known limitations

This is the list to read before using FairDetect for anything. If a limitation is not here, it is not because it was solved; it is because it was not measured.

## 1. High-ability human writing is over-flagged

At the Judge 4.0 operating point:

| Group | False-positive rate |
| --- | --- |
| ESL learner essays (NUCLE + PELIC, 2,649 docs) | 2.45% |
| MICUSP academic writing (829 docs) | 26.66% |
| MICUSP native speakers (681 docs) | 28.93% |
| MICUSP non-native speakers (148 docs) | 16.22% |

The better the prose, the more likely it is to be flagged. Political science, English, and philosophy were the worst disciplines; mechanical engineering was the least affected. This is a model-level defect. Lowering the threshold trades AI recall for human false positives; it does not remove the pattern.

## 2. Humanized AI is under-measured

The strong-humanized evaluation set has **23 documents**. At that size, one document moves the miss rate by 4.35 percentage points. The reported 8.7% miss rate is not a stable estimate. There is no evidence that the system is robust to paraphrase, translation, or deliberate style transfer.

## 3. Document structure changes the score

The pipeline splits sentences and slides an 8-sentence window. Headings, bullet lists, and short lines change sentence boundaries and window alignment. In one measured case, removing nine section headings changed the spear mean from **0.932 to 0.743**, flipping the verdict. Cross-document comparisons must use a fixed preprocessing convention.

## 4. Long documents are truncated

Only the first 30 windows are scored. With stride 2 and 8-sentence windows, that covers roughly the first 240 sentences (about 4,000–6,000 words). Anything after that is invisible.

## 5. English-centric preprocessing

Sentence splitting expects Latin punctuation (`.`, `!`, `?`) followed by a capital letter. Languages without spaces or with different punctuation will be split poorly. The word counter counts `[A-Za-z']+`.

## 6. Short texts are rejected

Fewer than 4 sentences produces no score. A single paragraph may be too short to analyze.

## 7. The score is not a probability of authorship

`mean`, `pct50`, and `ai_rate` are shares of windows/sentences crossing a model-specific bar. They are **not** the probability that the author used AI. The report's "AI reference rate" is a display convention, not a calibrated posterior.

## 8. No Turnitin calibration

Turnitin's model, thresholds, and training data are not public. The report is styled like a Turnitin report for readability, but the numbers are not the same quantity and cannot be converted. A FairDetect 40% is not a Turnitin 40%.

## 9. The LLM adapter is uncalibrated

The `openai` adapter asks a local LLM for `{"ai_probability": ...}` per window. The output is sensitive to the prompt, the model, and the sampling settings. The 0.32/0.80 thresholds are for the original DeBERTa pair and do not transfer. Use the LLM path for plumbing tests, not for decisions.

## 10. No adversarial robustness

A detector that relies on perplexity or style features can be attacked by paraphrase, back-translation, or style transfer. No attack evaluation was completed. Do not assume the system is robust to a motivated evader.

## 11. The console is not a service

- No multi-user authentication.
- No rate limiting.
- `/api/jobs` is unauthenticated. It binds to 127.0.0.1 by default for this reason.
- Uploaded text is kept in memory for the life of the process (`JOBS` dict). Reports and PDFs are written under `ops-reports/`.
- There is no audit log, no retention policy, and no encryption at rest.

## 12. Model-specific thresholds

The published thresholds belong to one model pair. A different checkpoint, a different tokenizer, a different window size, or a different language will shift the score distribution. Calibrate on your own data before using any fixed threshold.

## 13. Data provenance

The original checkpoints were trained on a mixture of public and restricted corpora (learner corpora with registration requirements, academic corpora with licenses, generated humanizer outputs). The **model weights are released** in the `models-v4` release attached to this repository, under research and evaluation use only, non-commercial terms. The **corpora themselves are not redistributed**. If you train your own model, you are responsible for the licenses of your training data.

## 14. Not a disciplinary tool

A flag is a reason to read the text more carefully. It is not evidence of misconduct. Use human review, writing-process evidence, and the institution's policy. Turnitin itself says its AI score must not be the sole basis for action; the same applies here, more strongly.
