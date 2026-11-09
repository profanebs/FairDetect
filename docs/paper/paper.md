# FairDetect: A Local-First Detector Optimised for False Positives on Non-Native Academic Writing

## Abstract

Commercial AI-text detectors are built to catch generated text, and on non-native English writing that objective produces a measurable harm: across seven detectors, human-written TOEFL essays were flagged as AI-generated at an average rate of 61.3% (Liang et al., 2023). We describe FairDetect, a local-first detector built around the opposite objective. It pairs two DeBERTa-v3-base window classifiers trained to different targets — a *shield* penalised for flagging human writing and a *spear* penalised for missing AI and humanised AI — and combines them in a decision layer that is separate from both models, so the operating point can move without retraining. At the published operating point the system misses 3 of 363 humanised-AI documents (0.83%) in the October 2026 release of the AI Humanizer Benchmark while passing 97.55% of 2,649 held-out learner essays. It also flags 26.66% of 829 MICUSP papers, and we report that failure as a primary result rather than a caveat: the detector protects basic learner writing and penalises advanced academic prose, so the bias it removes at one end of the proficiency range reappears at the other. We describe the pool-registration discipline that makes these figures interpretable, quantify how far the choice of document-level decision statistic — rather than the choice of model — moves the false-positive rate, and state precisely what the score is not.

---

## 1 Introduction

A detector deployed in a writing classroom is not a classifier. It is a decision procedure with asymmetric costs attached: a missed AI document is an integrity problem that a human reader may still catch, while a false accusation is a harm that the accused student cannot undo by appeal, particularly when the accusation is delivered as a number. Detector development has overwhelmingly optimised the first cost. The prevailing evaluation frame rewards recall on generated text at a fixed, usually low, false-positive rate measured on a convenience sample of human writing; and the human sample is rarely the population that will actually be scored.

For non-native English writers that gap is not hypothetical. Liang et al. (2023) evaluated several widely used detectors on essays written by non-native speakers and found that the detectors consistently misclassified them as AI-generated while identifying native-speaker writing accurately; the average false-positive rate on human TOEFL essays was 61.3%, and the worst detector reached 97.8%. The mechanism they propose is not a bug in any single model. Formulaic academic register — limited lexical range, repeated connectives, tightly patterned paragraph structure — is precisely what style-based detectors associate with generation, and it is also what a learner produces when writing under examination conditions. The detector is doing what it was trained to do. The harm is in the objective.

We therefore asked a narrower question than "can AI text be detected":

> Can a detector be built that is *conservative on human writing*, and in particular on learner writing, while still catching AI and AI that has been passed through a humanising tool?

"Conservative" is treated here as a design constraint with an operational meaning: the human false-positive rate on held-out pools is the primary metric, and AI-side recall is maximised subject to it. Three consequences follow, and they organise the rest of the paper.

First, the two objectives do not fit in one model. Training a single classifier to catch humanised AI drives its decision boundary into the region where fluent human prose lives; training it to leave human prose alone produces blind spots on AI. We did not resolve this by finding a better single model, but by separating the objectives into two checkpoints and moving the trade-off into a decision layer that is applied after inference (§3.3–3.4).

Second, the document-level statistic matters as much as the model. Given a fixed pair of classifiers, replacing the mean of per-window scores with the share of high-confidence sentences cuts the false-positive rate on expert human academic writing from 26.66% to 11.46%, or to 7.84% at a stricter cut, at the cost of two to three AI documents out of 723 (§6.3). No retraining is involved. A detector paper that reports only architecture and thresholds has omitted a first-order design choice.

Third, the residual defect is not where the project intended to look. The system is clean on the population it was built for — 2.45% false positives on 2,649 held-out learner essays — and fails on a population it was not built for: 26.66% false positives on 829 papers from the Michigan Corpus of Upper-level Student Papers, rising to 28.93% for native-speaker authors and falling to 16.22% for non-native authors of the same corpus (§6.2). Within MICUSP, the mean score is 0.369 for political science, 0.312 for English and 0.295 for philosophy, against 0.043 for mechanical engineering. The bias tracks rhetorical polish, not nativeness. A tool that protects a Vietnamese undergraduate's placement essay and penalises a fourth-year political science major has not solved the fairness problem; it has relocated it.

### 1.1 Contributions

1. **An architecture that separates the objectives.** Two DeBERTa-v3-base window classifiers trained to conflicting targets, combined by a disjunctive rule whose thresholds are external to both models, so that the operating point is a deployment parameter rather than a property of the weights (§3).
2. **A false-positive-first evaluation on registered pools.** 3,478 held-out human documents split into 2,649 learner essays and 829 expert academic papers, plus 1,595 frozen human documents, 363 humanised-AI documents and a 23-document strongly humanised set, each registered as tune or holdout before use, with a zero-window-overlap assertion between training and every evaluation pool (§4).
3. **A quantified account of the decision statistic.** A re-scoring experiment over 4,223 human and 745 AI documents showing that the choice between a window mean and a high-confidence sentence share moves the expert-human false-positive rate by a factor of two to three at near-constant AI recall (§6.3).
4. **Two negative results with architectural consequences.** Humanised text collapses the shield but not the spear, which rules out serial gating (§7.3); and scores are checkpoint-specific to a degree that makes a score a property of the text *and* the checkpoint rather than of the text alone (§7.4).
5. **An explicit boundary statement.** The score is not a probability of authorship, is not calibrated to any commercial detector, and is not evidence of misconduct (§7.6, §8).

### 1.2 Scope

This is an evaluation paper for a deployed artefact, not a claim about the detectability of machine-generated text in general. The system is English-only, classifies at most 30 windows per document, requires at least four sentences, and has not been evaluated against a motivated evader. Section 8 lists what was not measured; where a limitation is absent from that list, it is because it was not measured, not because it was resolved.

---

## 2 Related Work

### 2.1 Zero-shot detectors and the metric problem

Statistical detection began with likelihood and rank-based tests over a language model's own distribution (Gehrmann et al., 2019), and was formalised as a curvature criterion by DetectGPT, which compares a passage's log-probability under the model of interest against perturbations of that passage (Mitchell et al., 2023). Fast-DetectGPT replaces perturbation with conditional sampling and reports a 75% relative improvement over DetectGPT at a 340-fold speed-up (Bao et al., 2024). Binoculars contrasts the scores of two related models and reports detection of over 90% of ChatGPT samples at a 0.01% false-positive rate without task-specific training (Hans et al., 2024).

These methods establish the genre convention this paper follows: a recall figure is meaningless without the false-positive rate at which it was obtained. They also establish its limitation. All three are evaluated on human text drawn from domains where the detectors were not expected to fail — news, abstracts, encyclopaedic prose. None reports a per-population breakdown on non-native student writing, and the fixed false-positive rate at which they are evaluated (0.01% in the Binoculars case) is measured on a human sample that does not contain the population at risk.

### 2.2 Trained classifiers and the transfer problem

Training a classifier on human/AI pairs avoids the need for access to the generating model. Ghostbuster trains over n-gram and probability features and reports cross-generator behaviour (Verma et al., 2024); the M4 benchmark shows that cross-generator and cross-domain generalisation, not in-domain accuracy, is the binding constraint (Wang et al., 2024); RAID organises the axes of variation — generator, domain, decoding strategy, adversarial attack — and shows that detector rankings are not stable across them (Dugan et al., 2024). The survey literature had already separated statistical, neural and watermarking approaches (Jawahar et al., 2020).

Two lessons transfer directly. A single aggregate number hides the sampling frame, which is why §4 registers every pool with its role and size before any model is scored. And the hardest axis is the adversary, not the generator family: paraphrase and back-translation degrade detectors substantially while leaving text quality largely intact (Krishna et al., 2023; Sadasivan et al., 2023). That is the reason a humanised-AI pool, rather than raw model output, is the primary AI-side test here.

### 2.3 Watermarking and its preconditions

Watermarking embeds a statistical signature at generation time and, where available, is a stronger signal than post-hoc classification (Kirchenbauer et al., 2023). Its precondition is provider cooperation, which a tool scoring a student's existing draft cannot assume, so we do not evaluate against it.

### 2.4 Validity, bias and the assessment context

The detector literature and the assessment literature have run in parallel. The former reports accuracy on corpora; the latter asks whether the construct being measured is the one that matters. Liang et al. (2023) is the point where the two meet: the finding is not that detectors are inaccurate but that their errors are distributed non-randomly across a protected population. Weber-Wulff et al. (2023) test twelve free tools and two commercial systems on 54 documents and conclude that the available detectors are neither accurate nor reliable, with a bias toward classifying output as human-written; Walters (2023) compares sixteen detectors on essays written by humans and by two model generations; Casal and Kessler (2023) report that expert linguists could not reliably perform the same discrimination, which sets the comparison class. On the policy side, Perkins (2023), Cotton et al. (2024) and Chan (2023) argue for process-based rather than detection-based integrity regimes, Kasneci et al. (2023) survey the broader educational stakes, and Barrot (2023) sets out the same tension for second-language writing instruction.

This paper takes the assessment literature's conclusion as a constraint rather than as a debating position: if a flag cannot ground a finding, then the only defensible design target is a low and *evenly distributed* false-positive rate. The second half of that target is what §6.2 tests, and what the system fails.

### 2.5 Commercial systems and public documentation

Turnitin's AI writing indicator is the most widely deployed commercial signal in higher education. Its documentation states that the reported percentage is the share of qualifying text identified as AI-generated, that scores between 1% and 19% are not surfaced as numbers (a floor introduced in July 2024 explicitly to limit false-positive exposure), that bibliographies are excluded from processing, and that an AI writing score "should not be used as the sole basis for adverse actions against a student" (Turnitin, 2024–2026). Turnitin's product office has separately described its target as a false-positive rate below 1% (Chechitelli, 2023).

We quote these statements because they define the comparison class, and because the vendor's own framing is closer to ours than much deployment practice: a score built to be read alongside human judgement is not the same artefact as a score used as a verdict, even when the number looks identical.

### 2.6 What is missing

Three gaps remain across this literature and motivate the present work. Detector evaluations rarely report the false-positive rate separately for learner writing and for expert academic writing, so the two cancel in a pooled human sample. The decision layer — the mapping from many per-window scores to one document verdict — is reported as a threshold rather than examined as a design choice, although §6.3 shows it dominates. And deployment constraints are treated as engineering detail rather than as evaluation-relevant, although they determine which populations can be served at all.

---

## 3 Method

### 3.1 Problem formulation

Let a document *d* be a sequence of sentences. A detector produces a score vector over windows of *d*, and a decision rule maps that vector to a binary flag. We treat the flag as a *screening* decision — a reason to read a text more carefully — and not as an inference about authorship. Under that framing the relevant quantity is not the area under a ROC curve but the false-positive rate at the chosen operating point, evaluated separately for each human population the tool will encounter.

Two design commitments follow. The human false-positive rate on held-out data is the primary metric, reported per population rather than pooled. And the operating point is exposed as configuration, so that an institution can trade recall for safety without retraining, and so that a change in the operating point cannot silently change the meaning of a published number.

### 3.2 Window pipeline

Documents are split into sentences, grouped into windows of eight consecutive sentences with a stride of two, and capped at 30 windows per document. Each window is truncated to 256 tokens and classified independently; the document-level statistics are computed from the resulting per-window probabilities.

| Parameter | Value |
| --- | --- |
| Sentence split | Latin terminal punctuation followed by a capital |
| Window | 8 consecutive sentences |
| Stride | 2 sentences |
| Window cap | 30 per document |
| Token truncation | 256 per window |
| Minimum length | 4 sentences |
| Base model | `microsoft/deberta-v3-base` (≈86M backbone parameters; He et al., 2021) |
| Checkpoint size | 711 MB (float32) |

The window design is what makes a small encoder sufficient: a document becomes at most 30 short sequences, which a base-size model handles on CPU. Inference takes 0.6–13 seconds per document for 5–30 windows, with no GPU and no network access. The cap has a cost that §8 records: at stride 2 and eight-sentence windows, 30 windows cover roughly the first 240 sentences, so longer documents are scored only in their opening portion.

The window is also the unit at which training labels are assigned. Every window of an AI document is positive and every window of a human document is negative, inherited from the document label. This is noisy at the boundaries — a human document may contain a genuinely generated paragraph — but document-level provenance is what the corpora actually provide, and sentence-level annotation does not exist at this scale.

### 3.3 Two objectives, two checkpoints

The published system uses two DeBERTa-v3-base sequence classifiers trained with identical hyperparameters and different data mixtures.

| Role | Checkpoint | Objective | Failure it is tuned against |
| --- | --- | --- | --- |
| Shield | `r11-shield:ep1` | Do not flag human writing | False positives on real human text |
| Spear | `r10-spear:ep0` | Catch AI and humanised AI | Missed AI text |

The reason for two checkpoints is not capacity. It is that the two targets select different decision boundaries over the same feature space, and the boundary that satisfies one violates the other. This is measurable at the level of the rule rather than the model: in a grid of 2,613 candidate rules over the same model pair, *every* rule that met both AI-side targets (at most 3 of 363 missed on the humanised benchmark, and 0 of 23 on the strongly humanised set) produced a human false-positive rate of at least 18.40% on the 3,478-document holdout. Reaching 0 of 23 requires lowering the shield's mean threshold to 0.10, and at that threshold human documents are flagged in bulk (§6.1).

The two checkpoints also respond to different properties of the text. Across every humanised sample we measured, the shield scored between 0.000 and 0.025 while the spear scored between 0.666 and 0.935. A humanising tool that rewrites surface style drives the shield's output to the floor, because the rewritten text no longer looks generated to a model trained on generation artefacts; the spear, trained against humanised outputs specifically, still registers it. The reverse holds on polished human prose, where the shield is the model that fires.

### 3.4 The judge layer

The decision rule is applied after inference and is not part of either checkpoint:

```
g = shield window mean      (0..1)
r = spear  window mean      (0..1)
caught  iff  g >= 0.32  OR  r >= 0.80
display S = 100 * max(g, r)
review flag if not caught and r >= 0.90
```

The disjunction is deliberate and is the architectural consequence of §3.3. A serial design — pass the document if the shield is confident it is human, otherwise consult the spear — deadlocks on exactly the documents the system exists to catch: the shielded samples score near zero on the shield, so the gate releases them before the spear is consulted. The `OR` removes the gate.

Two properties matter for interpretation. The thresholds belong to one checkpoint pair: a different checkpoint, tokenizer, window size or language shifts the distribution, so the constants do not transfer. And the displayed score `S` is a monotone rescaling of the larger of two means, not a probability. The secondary flag at `r ≥ 0.90` routes a near-threshold document with confident windows to human review without changing the verdict.

### 3.5 Choosing the operating point

The operating point was selected by scanning a rule grid against the frozen pools with the human holdout used as a hard constraint, then reading the resulting frontier rather than a single optimum. Three configurations bracket the frontier and are retained in the released configuration file:

| Configuration | Rule | AHBench-10 missed | Strongly humanised missed | Frozen human pass | Holdout false positives |
| --- | --- | --- | --- | --- | --- |
| `v4ai` (recall-first) | g ≥ 0.10 or r ≥ 0.70 | 1/363 | 0/23 | 95.49% | 18.57% |
| **`v4` (published)** | **g ≥ 0.32 or r ≥ 0.80** | **3/363** | **2/23** | **99.42%** | **8.22%** |
| `v4safe` (human-first) | g ≥ 0.50 or r ≥ 0.80 | 6/363 | 3/23 | 99.50% | 4.54% |

The published point is not the frontier's optimum on any single axis; it is the point at which neither human-side measure degrades relative to the previous release while the AI-side benchmark target is still met. Its AI-side margin is one document: raising the shield threshold from 0.32 to 0.34 takes the AHBench miss count from 3 to 5 (§6.1). We report that fragility rather than presenting 0.32 as a robust choice.

### 3.6 Implementation and cost

Both checkpoints were trained with the same configuration, held constant across generations so that differences between generations reflect data rather than hyperparameters: 256 tokens per window, batch size 16, two epochs with checkpoints saved at epoch 0, epoch 1 and final, learning rate 2×10⁻⁵, seed 0, cross-entropy over two labels. One generation trains in about 21 minutes on a single consumer GPU. Training is not the bottleneck; data preparation and evaluation are.

The released artefact is the inference pipeline, the decision rule and the checkpoints. Training code is not released because the corpora cannot be redistributed: the learner corpora carry registration or non-derivative terms, and the humanised-AI data carries benchmark terms. Checkpoints are released under research and evaluation use, non-commercial.

---

## 4 Data and Evaluation Protocol

### 4.1 Corpora

| Source | Content | Terms | Role |
| --- | --- | --- | --- |
| W&I + LOCNESS (BEA-2019) | Learner and native student essays, CEFR-graded (Bryant et al., 2019) | Competition data, research use | Human, learner domain |
| PELIC | University EAP learner essays, ≈4.2M words (Naismith et al., 2022) | CC BY-NC-ND | Human, learner domain |
| ICNALE | Asian learner English, registered access (Ishikawa, 2013) | Registered use, no redistribution | Human, training and evaluation |
| Ghostbuster corpus | Human and six-generator AI text (Verma et al., 2024) | Public research | AI |
| AI Humanizer Benchmark | Humanised outputs from 11 tools across monthly cycles | CC BY 4.0 | AI, earlier cycles only, plus external evaluation |
| Internal red-team corpus | Native and humanised documents produced for this project | Internal | AI, training and held-out evaluation |

Training-set sizes grew across generations. At the fifth generation the training set held roughly 37,000 windows, of which about 8,200 were AI, with about 8,200 validation windows; the largest shield training file contains 146,094 windows.

Two training findings recurred across generations and constrain what a single score can mean. The second epoch is usually worse: the epoch-0 checkpoint consistently outperformed the epoch-1 and final checkpoints on the frozen pools, so selecting on training loss would have chosen the wrong one. And targeted oversampling moves the failure rather than removing it — adding learner essays as hard negatives cut false positives on the ICNALE pool from 59/1,129 to 16/1,129 while raising them on another human pool from 8/238 to 76/238. The two kinds of false positive are not the same defect, which is why §6.2 reports per pool rather than pooled.

### 4.2 Evaluation pools

| Pool | Size | Composition | Role |
| --- | --- | --- | --- |
| Human frozen pool | 1,595 | 238 + 1,129 + 20 + 78 + 130 across five sub-pools | Historical check; tuned on |
| Human holdout, learner | 2,649 | NUCLE 1,397 + PELIC 1,252 | Holdout |
| Human holdout, expert | 829 | MICUSP, 16 disciplines, 681 native / 148 non-native (Römer & O'Donnell, 2011) | Holdout |
| Human holdout, total | 3,478 | Sum of the two holdout rows | Holdout |
| Humanised AI | 363 | AI Humanizer Benchmark, October 2026 cycle, 11 tools × 33 source texts | Held out from training |
| Strongly humanised | 23 | Hardest humanised documents from the same family | Difficulty probe |
| AI re-scoring set | 723 + 22 | Two-release AI Humanizer Benchmark pool + strongly humanised subset, sentence-level scores | Derived |

Pool membership was fixed before scoring. A pool registered as tune is used to choose thresholds and checkpoints; a pool registered as holdout is scored once, after the rule is frozen, and is not used to revise it. Roles do not change after registration. The 1,595-document frozen pool is reported with its historical status and is marked optimistic, because it was used for earlier selection.

### 4.3 Zero-overlap assertion and leakage probe

Before training, training windows are compared against every evaluation pool at the window level, and the build asserts zero overlapping windows against both the frozen evaluation sets and the reserved learner pool. This is enforced in the data-preparation step rather than checked by hand.

For documents produced after training, an eight-word sentence-level containment probe compares each new sample against the training files and all red-team batches, with a positive control confirming the probe fires. On the samples reported here it returned zero hits, as expected given that they post-date the checkpoints.

### 4.4 Document-level statistics

Six statistics are computed per document and are not interchangeable:

| Name | Definition | Used by |
| --- | --- | --- |
| `mean` | Mean of per-window p(AI) | Judge 4.0 |
| `pct50` | Share of windows with p(AI) ≥ 0.50 | Reporting, earlier rules |
| `pct80` | Share of windows with p(AI) ≥ 0.80 | Reporting |
| `s90` | Share of windows with p(AI) ≥ 0.90 | Reporting |
| `sents` | Per-sentence mean of covering windows | Display |
| `rate_word` | Share of words in sentences whose sentence-mean crosses the judge bar | Display, comparable in kind to commercial text-share percentages |

`mean` and `pct50` are different quantities and are never compared with each other. The display percentage shown to a user is `rate_word` at a 0.5 sentence cut, which is the closest analogue to a commercial "share of text flagged" figure; it is not the decision statistic. This distinction caused a documented misreading during development and is now enforced in the report layout.

Every result that follows is reported with the pool, its size, and whether it was held out; figures from the frozen pool are labelled optimistic wherever they appear; and where a number comes from a third party, the party and the statistic are named in the same sentence.

---

## 5 Experiments

Six experiments are reported. Each varies one thing, and each is reported against the human-side cost measured on the same rule.

**E1 — Operating point.** Three configurations on one checkpoint pair (`v4ai`, `v4`, `v4safe`), plus a one-dimensional sweep of the shield threshold with the spear threshold fixed at 0.80, measured on the humanised benchmark, the strongly humanised set, the frozen human pool and the 3,478-document holdout. Purpose: expose the trade-off curve and the width of the plateau.

**E2 — Decision statistic.** A sentence-level re-scoring of 4,223 human and 745 AI documents, comparing four document-level rules built from the *same* model pair: the window mean at 0.32/0.80, a window-share rule at 20%, and two high-confidence sentence-share rules (sentence-mean ≥ 0.8 covering ≥ 30% or ≥ 40% of the text). Purpose: separate the contribution of the statistic from that of the model.

**E3 — Generations.** Five successive spear generations and one shield generation, each scored on frozen pools that never entered its own training. Purpose: test whether gains are generalisation or memorisation, and whether checkpoint selection is stable.

**E4 — Commercial comparison.** The October 2026 AI Humanizer Benchmark release, on which this system was scored on all 363 documents and for which the benchmark publishes verdicts from seven commercial detectors. Purpose: place the result in the field, subject to the statistic mismatch stated in §6.4.

**E5 — Turnitin case series.** Seven documents with known provenance, each scored by Turnitin and by this system. Purpose: test whether the two systems measure the same quantity, not to rank them.

**E6 — Robustness probes.** Removing section headings before scoring, and re-scoring the same document under successive checkpoint generations. Purpose: bound how much of a score is a property of the text.

---

## 6 Results

### 6.1 Operating point and its margin

At the published operating point the system misses 3 of 363 humanised-AI documents (0.83%) and 2 of 23 strongly humanised documents (8.7%), while passing 99.42% of the 1,595-document frozen human pool (10 false positives) and 91.78% of the 3,478-document holdout.

| Pool | n | Result | False positives |
| --- | --- | --- | --- |
| Humanised AI (AHBench, Oct 2026) | 363 | 3 missed = 0.83% | — |
| Strongly humanised | 23 | 2 missed = 8.7% | — |
| Human frozen pool (tuned on) | 1,595 | 99.42% pass | 10 (0.63%) |
| Human holdout, learner (NUCLE + PELIC) | 2,649 | 97.55% pass | 65 (2.45%) |
| Human holdout, expert (MICUSP) | 829 | 73.34% pass | 221 (26.66%) |
| — MICUSP native speakers | 681 | 71.07% pass | 197 (28.93%) |
| — MICUSP non-native speakers | 148 | 83.78% pass | 24 (16.22%) |
| Human holdout, total | 3,478 | 91.78% pass | 286 (8.22%) |

The gap between the frozen pool and the holdout is the honest measure of selection bias on the human side: 0.63% false positives against 8.22%, an order of magnitude. The frozen number should not be quoted as a performance figure, and we do not.

The shield threshold sweep shows how narrow the AI-side margin is:

| Shield mean threshold | AHBench missed | Strongly humanised missed | Frozen human pass | Holdout false positives |
| --- | --- | --- | --- | --- |
| 0.18 | 3 | 2/23 | 96.21% | 13.50% |
| 0.26 | 3 | 2/23 | 99.08% | 10.60% |
| 0.30 | 3 | 2/23 | 99.33% | 9.00% |
| **0.32** | **3** | **2/23** | **99.42%** | **8.22%** |
| 0.34 | 5 | 3/23 | 99.42% | 7.70% |

The AI-side result is flat from 0.18 to 0.32 and breaks at 0.34. A published miss count of 3 of 363 therefore has a margin of one document — a property of a 363-document pool rather than of the method. It determines how the number should be read: as an order of magnitude relative to the commercial range, not as a precise rate.

### 6.2 Where the false positives are

The aggregate human false-positive rate of 8.22% conceals a two-population structure that is the most consequential result in this paper.

Learner writing is clean: 2.45% false positives on 2,649 held-out NUCLE and PELIC essays, and six false positives among 1,129 ICNALE essays in the frozen pool. Expert academic writing is not clean. On 829 MICUSP papers the false-positive rate is 26.66% — roughly one paper in four — and the ordering within the corpus is systematic rather than random:

| Slice | Mean score (0–1) |
| --- | --- |
| Political science | 0.369 |
| English | 0.312 |
| Philosophy | 0.295 |
| Linguistics | 0.079 |
| Mechanical engineering | 0.043 |

The ordering by author status runs the same way. Native-speaker MICUSP authors are flagged at 28.93%, non-native authors at 16.22%. By year of study, fourth-year undergraduates score 0.260, first-year master's students 0.161, third-year doctoral students 0.118.

Four candidate explanations were tested and rejected. Window length is not the cause: per-window token count correlates with the score at −0.003. Document length is not: word count correlates at −0.128, in the wrong direction for a length artefact. Truncation is not: re-scoring at four- and two-sentence windows *raises* the score (0.122 → 0.159 → 0.193). And it is not a pipeline mismatch: the diagnostic used the deployed window parameters. Inspection of the highest-scoring MICUSP documents returned policy memoranda, a disability-rights paper, an essay on a slaughterhouse, and a literary analysis of Joyce — all verifiably human.

The pattern is therefore a model-level property: the detector has learned a boundary that places rhetorically controlled, thesis-driven, humanistic academic prose on the generated side. Lowering the threshold moves the boundary and reduces the rate; it does not remove the ordering.

### 6.3 The decision statistic is a first-order choice

Holding the model pair fixed and changing only the document-level rule:

| Rule | AI caught | Learner false positives | Expert false positives |
| --- | --- | --- | --- |
| Window mean, bars 0.32 / 0.80 (published) | 720/723 | 2.45% | **26.66%** |
| Window share ≥ 20% | 722/723 | 10.80% | 33.17% |
| Sentence share @0.8 ≥ 30% | 718/723 | 2.45% | **11.46%** |
| Sentence share @0.8 ≥ 40% | 717/723 | 1.81% | **7.84%** |

(The AI-side column is computed over the 723 AI Humanizer Benchmark documents carried in that run, which covered 745 AI documents in total; the human side covers 4,223 documents, of which 2,649 are learner essays and 829 are MICUSP papers.)

Two readings matter. The window-share rule at 20% — the configuration closest to a commercial display threshold — is *worse* than the published rule on both human populations, raising expert false positives to 33.17% and learner false positives to 10.80%. The high-confidence sentence-share rules are better on both: at a 30% cut the expert false-positive rate falls by more than half with no change on learner writing, and at 40% it falls to 7.84% with learner false positives *below* the published rule.

The mechanism is visible in the two models' output distributions. The published rule flags a document when the shield's *mean* crosses 0.32, and MICUSP prose frequently pushes that mean over the bar while the shield rarely assigns any single sentence a score of 0.8 or above. A rule that requires a substantial share of high-confidence sentences therefore bypasses the shield's contribution on exactly this population, while the spear's high-confidence windows still catch humanised AI.

This rule was not adopted. It requires an independent threshold set, and the published numbers were produced under the older rule. We report it because the size of the effect — a factor of two to three on the population the system fails — is larger than any model change we measured, and because it reframes the problem: the residual bias is not only a training-data defect (§7.1) but also a decision-statistic defect that can be attacked without retraining.

### 6.4 Commercial comparison

On the October 2026 AI Humanizer Benchmark release, this system was scored on all 363 documents; the benchmark publishes verdicts from seven commercial detectors on the same document set, and those verdicts are quoted here. The figure below is a miss rate for this system and a mean human-probability for each commercial detector; the two definitions are discussed after the table.

| Detector | Published figure |
| --- | --- |
| **FairDetect, Judge 4.0** | **0.83%** (3/363, decision rate) |
| GPTZero | 48.7% |
| Copyleaks | 50.1% |
| Originality.ai | 57.2% |
| Winston AI | 59.1% |
| QuillBot | 72.8% |
| ZeroGPT | 74.5% |
| Grammarly | 78.3% |

The commercial figures are the benchmark's own published numbers, not measurements we made, and they carry three qualifications that we regard as part of the result rather than as hedging.

First, the statistic is not identical. The benchmark publishes, for each detector, the mean human-probability it assigned to the humanising tools' outputs; the figures above are those per-detector means over the September and October 2026 cycles. Our 0.83% is a document-level decision rate on the October cycle alone. A mean human-probability and a decision rate are different quantities, and a detector can carry a high mean human-probability while still deciding "AI" on most documents. The comparison is therefore directional.

Second, the cycles are not the same. The commercial figures average two releases; ours are from one. The benchmark notes that humanising tools change monthly, and its own methodology freezes each cycle separately for that reason.

Third, this benchmark measures detection of *humanised* output from eleven specific tools. A detector can perform well here and be ordinary on raw model output; the ordering should not be read as a general ranking.

With those qualifications, the direction is large enough to survive them: a 0.83% miss rate against a 48.7%–78.3% range is not a rounding difference. An earlier and weaker model, scored on a 723-document two-release pool under a single stated rule, passed 28% of humanised documents as human where the same seven detectors passed 50%–82%. The two runs agree in direction on pools of different construction.

### 6.5 The Turnitin case series

Seven documents with known provenance were scored by both systems.

| Document | Truth | Turnitin | This system (`rate_word` @0.5) | Judge 4.0 verdict |
| --- | --- | --- | --- | --- |
| Academic annotated bibliography | Human | 0% | 0.0% | pass |
| Humanised course essay | AI | 28% | 100.0% | miss |
| Native AI statement of intent | AI | 100% | 95.2% | caught |
| Manually humanised statement of intent | AI | not available | 78.9% | caught (margin 0.003) |
| Anchored humanised statement of intent | AI | 100% | 62.4% | miss |
| Proposal, model A | AI | below 20% (not displayed) | 18.3% | miss |
| Proposal, model B | AI | 76% | 87.8% | caught |

Three observations, offered as observations. On unmodified AI output both systems agree and the two percentages are close (95.2% against 100%), which supports the claim that `rate_word` at a 0.5 cut is the closest available analogue to a commercial text-share figure. On strongly humanised output both systems are inconsistent, in both directions: the anchored humanised sample is caught by Turnitin at 100% and missed here at 62.4%, while the humanised course essay is reported at 28% by Turnitin and 100% here. And per-document variance is large for both — one document is caught here with a margin of 0.003 on the spear mean.

With seven documents no ranking is defensible, and we make none. The series is reported because it establishes two things the rest of the paper relies on: the two systems do not measure the same quantity, and a single-document verdict from either is weak evidence.

### 6.6 Generations

Miss rates on frozen pools that never entered the training of the generation being scored:

| Generation | Humanised AI (363) | External 50-document corpus | Strongly humanised (23) |
| --- | --- | --- | --- |
| Spear 1.0 | 5.0% | 4.0% | 95.7% |
| Spear 2.0 | 4.1% | 0% | 30.4% |
| Spear 3.0 (epoch 0) | 3.0% | 0% | 26.1% |
| Spear 3.0 (final epoch) | 9.9% | 0% | 69.6% |
| Spear 4.0 (epoch 0) | 1/363 = 0.28% | — | 1/23 = 4.3% |
| Shield 3.0 (epoch 0) | 0/363 | — | 0/23 |
| **Judge 4.0 pair** | **3/363 = 0.83%** | — | **2/23 = 8.7%** |

Pools change between generations, so rows are compared within a group and not across. Two patterns are stable. The epoch-0 checkpoint beats the final checkpoint on frozen pools in every generation where both were scored — 9.9% at the final epoch against 3.0% at epoch 0 in the third spear generation — which is why checkpoints are selected on frozen pools rather than on validation loss. And the strongest AI-side pair is not the published one: the combination reaching 0 of 363 and 0 of 23 flags 23% of a human academic pool and was rejected for that reason.

### 6.7 Robustness probes

Removing nine section headings from a 1,543-word proposal changed the spear mean from 0.932 to 0.743 and flipped the verdict from caught to missed. Applying the same manipulation to a different document moved its spear mean in the opposite direction, from 0.261 to 0.342. The mechanism is positional: the pipeline splits on sentence boundaries and slides a fixed-length window, so short heading lines shift the alignment of every subsequent window and the document-level field moves with it.

The same humanised document scored under three successive spear generations returned 90.7, 0.0 and 72.9 on a 0–100 display scale; a human-written sample returned 77.3, 0.4 and 21.5. A score is therefore a property of the text *and* the checkpoint. Deployments must pin a version and re-validate before switching, and cross-document comparisons require a fixed preprocessing convention — in particular a stated decision about whether headings are scored.

---

## 7 Discussion

### 7.1 The bias moved; it did not disappear

The project's premise was that detectors over-flag non-native writers. At the operating point reported here that failure is largely absent on learner essays: 2.45% false positives on 2,649 held-out NUCLE and PELIC documents. The same system flags 26.66% of MICUSP papers, and within MICUSP it flags native speakers *more* than non-native speakers (28.93% against 16.22%).

The natural reading is that the operative variable is not nativeness but register. MICUSP contains upper-level papers written for assessment in a disciplinary genre: thesis stated early, signposted, hedged as the discipline expects, lexically dense. That is close to the profile that humanised or generated academic prose also occupies (Herbold et al., 2023), and a classifier trained to separate generated from student writing will place it on the generated side. Learner essays produced under time pressure in an examination register occupy a different region, and are separated cleanly.

Two implications pull in different directions. The specific harm documented by Liang et al. (2023) is addressable by data: adding learner essays as hard negatives cut ICNALE false positives from 59/1,129 to 16/1,129, and within the next shield generation the mean share of MICUSP windows above 0.5 fell from 55.2% to 18.5% between the two saved epochs. But the fix is population-specific, and fixing one population moved the failure to another — the same model that improved ICNALE raised false positives on a second human pool from 8/238 to 76/238.

For deployment this means a single global false-positive rate is not a usable safety claim. The rate has to be reported per population, and a tool validated on learner writing should not be released to a graduate programme without re-validation on that programme's writing.

### 7.2 The statistic is a design surface

Section 6.3 is, in our reading, the most transferable result here. With the models fixed, changing the document-level statistic from a window mean to a high-confidence sentence share halved to two-thirds the false-positive rate on expert human writing, at the cost of two to three AI documents out of 723, with no change in training. The mechanism is interpretable: the shield's *mean* crosses a low bar on fluent human prose while its per-sentence confidence stays low, so a rule demanding several confident sentences ignores precisely the signal that caused the error.

Detector papers typically report the decision rule as a threshold on an aggregate and move on. The aggregate's *shape* deserves the same scrutiny as the model, and a rule reported without its per-population behaviour is under-specified. We did not adopt the alternative because it had not been validated on an independent threshold set, and adopting it would have repeated the selection-bias error described in §8. It remains the most promising change we know of, and it is a change to a constant.

### 7.3 Humanisation attacks the gate, not the detector

The measured asymmetry — shield 0.000–0.025, spear 0.666–0.935 on the same humanised samples — has an architectural consequence we did not anticipate. A serial pipeline, in which the shield decides whether the spear is consulted, is the natural way to build a conservative system: let the permissive model gate the aggressive one. That design fails on exactly the adversary it is built against, because the humanising tool's output is what drives the shield to zero. The gate opens and the spear never runs.

The disjunctive rule follows, and it is uncomfortable: an `OR` over two models is less interpretable than a cascade and makes the operating point harder to reason about. The alternative — one model that is both conservative and sensitive — is what §3.3 shows to be unavailable at this data scale. Sadasivan et al. (2023), Chakraborty et al. (2023) and Krishna et al. (2023) frame this as an arms race in which the detector loses ground under a motivated adversary. Our measurements are consistent with that framing and add a deployment detail: the loss is not uniform across a detector's components, and an architecture that assumes uniformity fails earlier than its per-component accuracy suggests.

### 7.4 A score is not a stable property of the text

The cross-generation result — the same humanised document at 90.7, 0.0 and 72.9 under three successive spear generations — is the strongest argument in this paper against treating a detector score as a measurement. A measurement should be stable under a change of instrument, or at least its variation should be characterised. Here 0.0 and 90.7 are the same quantity under two checkpoints trained two days apart on overlapping data.

Structural sensitivity compounds this: removing headings moved one document's spear mean by −0.189 and another's by +0.081, without changing a word of prose. A tool whose output depends on whether section headings were pasted in is not measuring an authorial property; it is measuring a surface configuration that correlates with one. We report both as warnings rather than findings, because the underlying cause was not characterised. What can be said is operational: pin the checkpoint, fix the preprocessing convention, and re-validate on both sides after any change.

### 7.5 Why local-first is an evaluation property

The system runs on CPU, needs no network access, and processes a document in under thirteen seconds at zero marginal cost. That is usually presented as an engineering convenience; here it is also an evaluation property, because it determines which populations can be served at all. An institution that cannot send student text to a third-party API cannot use a hosted detector, and a student who cannot afford a subscription cannot check a draft before submitting it.

The cost is a small model trained on corpora that cannot be redistributed, and a hosted detector with fresher data will on average discriminate better on raw model output. The claim is not that a local model is more accurate, but that a detector whose false-positive structure is published and whose score can be recomputed by the person it is used against is a different kind of instrument.

### 7.6 What the number may and may not be used for

The displayed score is a monotone rescaling of the larger of two window means. It is not the probability that the author used AI, it is not comparable to a commercial percentage, and it is not calibrated to any external system. A FairDetect 40 and a Turnitin 40 are not the same quantity, and no conversion exists.

The decision layer produces a flag, and a flag is a reason to read a text more carefully. It is not evidence of misconduct, and it is weaker evidence than a conversation with the student about their process. Turnitin's own documentation says its AI score should not be the sole basis for adverse action (Turnitin, 2024–2026); the same statement applies here with more force, because this system's false-positive rate on expert academic writing is more than twenty times the vendor's stated target.

---

## 8 Limitations

**Expert human writing is over-flagged.** 26.66% false positives on 829 MICUSP papers, 28.93% for native speakers. This is a model-level defect: threshold adjustment trades AI recall against it and does not remove the ordering by discipline and author status.

**AI-side numbers carry selection bias.** Thresholds were selected on the same pool used to report the 0.83% miss rate. An independent AI-side threshold set was planned and not completed, so the AI-side figures are optimistic as well as fragile (§6.1).

**The strongly humanised set is 23 documents.** One document moves that metric by 4.35 percentage points. The reported 8.7% is not a stable estimate and no ranking based on it is defensible.

**English only, and structurally constrained.** Sentence splitting assumes Latin terminal punctuation followed by a capital, and the word counter recognises `[A-Za-z']+` only. Only the first 30 windows are scored, so at stride 2 and eight-sentence windows material beyond roughly 240 sentences is invisible. Fewer than four sentences produces no score.

**No adversarial robustness evaluation.** Paraphrase, back-translation and style transfer were not tested as attacks. The humanised-AI pool measures eleven commercial tools, which is not a motivated evader with access to the score.

**No calibration.** The score is not a probability of authorship and is not mapped to any commercial scale. The optional language-model adapter in the released pipeline is uncalibrated and inherits none of the thresholds reported here.

**No inter-annotator study for "humanised AI".** The category is operationalised by provenance — which tool produced the document — not by a judged property of the text.

**Neither comparison is controlled.** The commercial figures are the benchmark's published numbers, on a different statistic and a two-cycle average; we did not run the commercial APIs. The Turnitin series rests on seven documents and establishes only that the two systems measure different quantities and that per-document variance is large.

**Single-machine evaluation.** All numbers come from one inference environment with fixed library versions. The pipeline is deterministic given the checkpoint, but numerical reproducibility across hardware was not tested.

---

## 9 Conclusion

A detector built around the false-positive case behaves differently from one built around recall. Separating the two objectives into two checkpoints and a decoupled decision rule produced a system that misses 0.83% of 363 humanised-AI documents while passing 97.55% of 2,649 learner essays, at a cost in engineering complexity — two models, an interpretable but unusual disjunctive rule, and a configuration surface that has to be pinned.

The result we consider most important is not the AI-side number. It is that the fairness problem moved rather than dissolved. The same system flags one in four upper-level humanities and social-science papers and one in twenty-five mechanical engineering papers, and it flags native speakers more than non-native speakers. A tool that is safe for the population it was designed for, and unsafe for the population next door, is a tool whose validation does not transfer. Publishing the per-population rates, rather than a pooled human false-positive rate, is the minimum condition for using such a system responsibly.

Two design lessons generalise beyond this artefact. The document-level decision statistic is a first-order choice that deserves the attention usually reserved for architecture: a change of statistic cut the expert false-positive rate by more than half at near-constant recall, with no retraining. And a score is not a property of a text — two checkpoints trained two days apart returned 0.0 and 90.7 for the same document. Deployments that treat a detector's output as a measurement, rather than as the output of a specific instrument at a specific version, will draw conclusions the instrument cannot support.

The largest unresolved defect — over-flagging strong human academic prose — is a training-data problem rather than a threshold problem. It requires hard negatives drawn from advanced academic writing, stratified by discipline and length, and an evaluation pool that was not used to build the model. Until that work is done, the honest description of this system is narrow: a local screening aid that is unusually safe on learner writing and demonstrably unsafe on expert academic writing, which should be deployed, if at all, with that asymmetry stated to everyone who sees its output.

---

## References

AI Humanizer Benchmark. (2026). *AI Humanizer Benchmark: monthly cycle data* [Data set]. Zenodo. https://doi.org/10.5281/zenodo.22966275

Bao, G., Zhao, Y., Teng, Z., Yang, L., & Zhang, Y. (2024). Fast-DetectGPT: Efficient zero-shot detection of machine-generated text via conditional probability curvature. In *Proceedings of the 12th International Conference on Learning Representations (ICLR 2024)*. arXiv:2310.05130

Barrot, J. S. (2023). Using ChatGPT for second language writing: Pitfalls and potentials. *Assessing Writing, 57*, 100745. https://doi.org/10.1016/j.asw.2023.100745

Bryant, C., Felice, M., Andersen, Ø. E., & Briscoe, T. (2019). The BEA-2019 shared task on grammatical error correction. In *Proceedings of the Fourteenth Workshop on Innovative Use of NLP for Building Educational Applications* (pp. 52–75). https://doi.org/10.18653/v1/W19-4406

Casal, J. E., & Kessler, M. (2023). Can linguists distinguish between ChatGPT/AI and human writing? A study of research ethics and academic publishing. *Research Methods in Applied Linguistics, 2*(3), 100068. https://doi.org/10.1016/j.rmal.2023.100068

Chakraborty, S., Bedi, A. S., Zhu, S., An, B., Manocha, D., & Huang, F. (2023). On the possibilities of AI-generated text detection. arXiv:2304.04736

Chan, C. K. Y. (2023). A comprehensive AI policy education framework for university teaching and learning. *International Journal of Educational Technology in Higher Education, 20*(1). https://doi.org/10.1186/s41239-023-00408-3

Chechitelli, A. (2023, March 16). *Understanding false positives within our AI writing detection capabilities*. Turnitin. https://www.turnitin.com/blog/understanding-false-positives-within-our-ai-writing-detection-capabilities

Cotton, D. R. E., Cotton, P. A., & Shipway, J. R. (2024). Chatting and cheating: Ensuring academic integrity in the era of ChatGPT. *Innovations in Education and Teaching International, 61*(2), 228–239. https://doi.org/10.1080/14703297.2023.2190148

Dugan, L., Hwang, A., Trhlik, F., Ludan, J. M., Zhu, A., Xu, H., Ippolito, D., & Callison-Burch, C. (2024). RAID: A shared benchmark for robust evaluation of machine-generated text detectors. In *Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (ACL 2024)*. arXiv:2405.07940

Gehrmann, S., Strobelt, H., & Rush, A. M. (2019). GLTR: Statistical detection and visualization of generated text. In *Proceedings of the 57th Annual Meeting of the Association for Computational Linguistics: System Demonstrations* (pp. 111–116). https://doi.org/10.18653/v1/P19-3019

Hans, A., Schwarzschild, A., Cherepanova, V., Kazemi, H., Saha, A., Goldblum, M., Geiping, J., & Goldstein, T. (2024). Spotting LLMs with binoculars: Zero-shot detection of machine-generated text. In *Proceedings of the 41st International Conference on Machine Learning (ICML 2024)*. arXiv:2401.12070

He, P., Liu, X., Gao, J., & Chen, W. (2021). DeBERTa: Decoding-enhanced BERT with disentangled attention. In *Proceedings of the 9th International Conference on Learning Representations (ICLR 2021)*. arXiv:2006.03654

Herbold, S., Hautli-Janisz, A., Heuer, U., Kikteva, Z., & Trautsch, A. (2023). A large-scale comparison of human-written versus ChatGPT-generated essays. *Scientific Reports, 13*, 18617. https://doi.org/10.1038/s41598-023-45644-9

Ishikawa, S. (2013). The ICNALE and sophisticated contrastive interlanguage analysis of Asian learners of English. *Learner Corpus Studies in Asia and the World, 1*, 91–118. https://doi.org/10.24546/81006678

Jawahar, G., Abdul-Mageed, M., & Lakshmanan, L. V. S. (2020). Automatic detection of machine generated text: A critical survey. In *Proceedings of the 28th International Conference on Computational Linguistics (COLING 2020)* (pp. 2296–2309). https://doi.org/10.18653/v1/2020.coling-main.208

Kasneci, E., Sessler, K., Küchemann, S., Bannert, M., Dementieva, D., Fischer, F., Gasser, U., Groh, G., Günnemann, S., Hüllermeier, E., Krusche, S., Kutyniok, G., Michaeli, T., Nerdel, C., Pfeffer, J., Poquet, O., Sailer, M., Schmidt, A., Seidel, T., Stadler, M., Weller, J., Kuhn, J., & Kasneci, G. (2023). ChatGPT for good? On opportunities and challenges of large language models for education. *Learning and Individual Differences, 103*, 102274. https://doi.org/10.1016/j.lindif.2023.102274

Kirchenbauer, J., Geiping, J., Wen, Y., Katz, J., Miers, I., & Goldstein, T. (2023). A watermark for large language models. In *Proceedings of the 40th International Conference on Machine Learning (ICML 2023)*. arXiv:2301.10226

Krishna, K., Song, Y., Karpinska, M., Wieting, J., & Iyyer, M. (2023). Paraphrasing evades detectors of AI-generated text, but retrieval is an effective defense. In *Advances in Neural Information Processing Systems 36 (NeurIPS 2023)*. arXiv:2303.13408

Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., & Zou, J. (2023). GPT detectors are biased against non-native English writers. *Patterns, 4*(7), 100779. https://doi.org/10.1016/j.patter.2023.100779

Mitchell, E., Lee, Y., Khazatsky, A., Manning, C. D., & Finn, C. (2023). DetectGPT: Zero-shot machine-generated text detection using probability curvature. In *Proceedings of the 40th International Conference on Machine Learning (ICML 2023)*. arXiv:2301.11305

Naismith, B., Han, N.-R., & Juffs, A. (2022). The University of Pittsburgh English Language Institute Corpus (PELIC). *International Journal of Learner Corpus Research, 8*(1), 121–138. https://doi.org/10.1075/ijlcr.21002.nai

Perkins, M. (2023). Academic integrity considerations of AI large language models in the post-pandemic era: ChatGPT and beyond. *Journal of University Teaching & Learning Practice, 20*(2). https://doi.org/10.53761/1.20.02.07

Römer, U., & O'Donnell, M. B. (2011). From student hard drive to web corpus (part 1): The design, compilation and genre classification of the Michigan Corpus of Upper-level Student Papers (MICUSP). *Corpora, 6*(2), 159–177. https://doi.org/10.3366/corp.2011.0011

Sadasivan, V. S., Kumar, A., Balasubramanian, S., Wang, W., & Feizi, S. (2023). Can AI-generated text be reliably detected? arXiv:2303.11156

Turnitin. (2024–2026). *AI writing detection model* [Release notes]. Turnitin Guides. https://guides.turnitin.com/hc/en-us/articles/28294949544717-AI-writing-detection-model

Verma, V., Fleisig, E., Tomlin, N., & Klein, D. (2024). Ghostbuster: Detecting text ghostwritten by large language models. In *Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics (NAACL 2024)*. arXiv:2305.15047

Walters, W. H. (2023). The effectiveness of software designed to detect AI-generated writing: A comparison of 16 AI text detectors. *Open Information Science, 7*(1). https://doi.org/10.1515/opis-2022-0158

Wang, Y., Mansurov, J., Ivanov, P., Su, J., Shelmanov, A., Tsvigun, A., Whitehouse, C., Afzal, O. M., Mahmoud, T., Sasaki, T., Arnold, T., Aji, A. F., Habash, N., Gurevych, I., & Nakov, P. (2024). M4: Multi-generator, multi-domain, and multi-lingual black-box machine-generated text detection. In *Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics (EACL 2024)*. arXiv:2305.14902

Weber-Wulff, D., Anohina-Naumeca, A., Bjelobaba, S., Foltýnek, T., Guerrero-Dib, J., Popoola, O., Šigut, P., & Waddington, L. (2023). Testing of detection tools for AI-generated text. *International Journal for Educational Integrity, 19*(1). https://doi.org/10.1007/s40979-023-00146-z
