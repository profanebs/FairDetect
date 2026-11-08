# Ethics and fair use

FairDetect is a research tool for studying how AI-text detectors fail. It is not an integrity enforcement system. This page is the use policy.

## 1. A flag is not a finding

A model score is a reason to read a text more carefully. It is not evidence that the author used AI, and it is not a basis for punishment. The system has a measured false-positive problem on exactly the population it was built to protect: capable human writers, especially non-native English writers.

Do not:

- use a FairDetect score as the sole or primary basis for an accusation;
- present a score as a probability that the author cheated;
- use the tool to surveil students, employees, or writers without their knowledge and consent;
- publish a person's text or score without consent.

## 2. Privacy

The console is local by design:

- uploaded text stays in the server process memory;
- reports and PDFs are written to `ops-reports/` on the local disk;
- there is no telemetry and no external call unless you configure an adapter that makes one.

If you configure the `openai` adapter, the text of every window is sent to the local endpoint you specify. If that endpoint is remote (a cloud API behind an OpenAI-compatible URL), the text leaves your machine. Do not point the adapter at a third-party service with student or institutional data.

## 3. Data protection

- Do not commit student texts, grades, or institutional data to this repository.
- Do not put API keys in `config/models.json`; use `${ENV_VAR}` references or `api_key_env`.
- The repository ships no weights and no training data on purpose.

## 4. Academic integrity

This project exists because detectors produce false positives against non-native writers. It is not a tool for evading detection.

Do not use it to:

- rewrite AI-generated text so it passes a detector;
- coach someone on how to hide AI use;
- generate "humanized" text for submission.

The original project included red-team work to test the detector, not to provide a bypass service. That boundary is part of the license to publish.

## 5. Turnitin

Turnitin is a trademark of Turnitin, LLC. This project is not affiliated with, endorsed by, or connected to Turnitin. The report layout is an homage for readability, not a claim of equivalence. FairDetect scores are not Turnitin scores and cannot be converted.

## 6. Reporting misuse

If you see this repository used to accuse or surveil someone, open an issue. The maintainers can clarify the limits, but they cannot control downstream use. The license is MIT; the ethical boundary is stated here, not enforced by code.

## 7. If you are accused

If a detector flag is used against you:

1. Ask which detector, which version, and which threshold.
2. Ask for the exact text spans that were flagged.
3. Provide drafts, version history, notes, and citations that show process.
4. Point to the published false-positive literature (Liang et al. 2023; the detector vendor's own disclaimers).
5. Ask whether the score is being treated as evidence or as a tip.

A local score from this tool is not an authority. Neither is a commercial score. The question is whether there is evidence of process, not whether a model produced a number.
