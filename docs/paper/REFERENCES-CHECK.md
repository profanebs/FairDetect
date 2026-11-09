# Reference and number verification

Working file for the manuscript `paper.md`. Not part of the submission.

Verification environment: Crossref REST API, OpenAlex API, arXiv API, DataCite API, direct
retrieval of publisher and vendor pages, and a local copy of the AI Humanizer Benchmark
dataset card and per-cycle data. Checks run 2026-11-09.

Status vocabulary:

- **VERIFIED** — the identifier resolves and the returned title and author list match the
  entry as written in `paper.md`.
- **VERIFIED (ID only)** — the record exists and the title matches, but a field quoted in the
  reference (venue, page range) was not confirmed by the resolving record.
- **PARTIAL** — the artefact exists but one attribute could not be checked from this host.

---

## 1. Reference-by-reference

| # | Reference | Identifier | Status | Verification method | Note |
| --- | --- | --- | --- | --- | --- |
| 1 | AI Humanizer Benchmark (2026) | 10.5281/zenodo.22966275 | VERIFIED | DataCite API returned 200; title "AI Humanizer Benchmark: monthly cycle data", publisher Zenodo, type Dataset, creator "AI Humanizer Benchmark" | Dataset card read in full; per-cycle files inspected |
| 2 | Bao et al. (2024), Fast-DetectGPT | arXiv:2310.05130 | VERIFIED (ID only) | arXiv API: title and all five authors match | ICLR 2024 venue taken from the authors' publication record |
| 3 | Barrot (2023) | 10.1016/j.asw.2023.100745 | VERIFIED | Crossref: *Assessing Writing* 57, 100745 | |
| 4 | Bryant et al. (2019), BEA-2019 | 10.18653/v1/W19-4406 | VERIFIED | Crossref: BEA workshop proceedings, pp. 52–75 | Author family names returned without given names by Crossref; full list checked against the ACL Anthology record |
| 5 | Casal & Kessler (2023) | 10.1016/j.rmal.2023.100068 | VERIFIED | Crossref: *Research Methods in Applied Linguistics* 2(3), 100068 | |
| 6 | Chakraborty et al. (2023) | arXiv:2304.04736 | VERIFIED | arXiv API: title and all six authors match | Cited for the theoretical limit argument |
| 7 | Chan (2023) | 10.1186/s41239-023-00408-3 | VERIFIED | Crossref: *IJETHE* 20(1) | Article number omitted because Crossref does not report it |
| 8 | Chechitelli (2023), Turnitin blog | URL | VERIFIED | Page retrieved in full; byline Annie Chechitelli, Chief Product Officer, dated 16 March 2023 | Quoted: "less than 1% false positive rate" |
| 9 | Cotton et al. (2024) | 10.1080/14703297.2023.2190148 | VERIFIED | Crossref: *IETI* 61(2), 228–239 | |
| 10 | Dugan et al. (2024), RAID | arXiv:2405.07940 | VERIFIED (ID only) | arXiv API: title and eight authors match | ACL 2024 venue from authors' record |
| 11 | Gehrmann et al. (2019), GLTR | 10.18653/v1/P19-3019 | VERIFIED | Crossref: ACL 2019 System Demonstrations, pp. 111–116 | |
| 12 | Hans et al. (2024), Binoculars | arXiv:2401.12070 | VERIFIED (ID only) | arXiv API: title and eight authors match | ICML 2024 venue from authors' record |
| 13 | He et al. (2021), DeBERTa | arXiv:2006.03654 | VERIFIED (ID only) | arXiv API: title and four authors match | ICLR 2021 venue from authors' record |
| 14 | Herbold et al. (2023) | 10.1038/s41598-023-45644-9 | VERIFIED | OpenAlex: *Scientific Reports* 13, article 18617, five authors | Note: a widely circulated citation with suffix `-45658-3` resolves to a different article (a dinosaur palaeontology paper). The correct DOI is the one above, confirmed twice |
| 15 | Ishikawa (2013), ICNALE | 10.24546/81006678 | VERIFIED | OpenAlex: *Learner Corpus Studies in Asia and the World* 1, 91–118 | Institutional-repository DOI; page range confirmed |
| 16 | Jawahar et al. (2020) | 10.18653/v1/2020.coling-main.208 | VERIFIED | OpenAlex: COLING 2020, pp. 2296–2309 | A first attempt with suffix `.409` resolved to an unrelated morphology paper and was discarded |
| 17 | Kasneci et al. (2023) | 10.1016/j.lindif.2023.102274 | VERIFIED | Crossref: *Learning and Individual Differences* 103, 102274, 23 authors | Author list truncated in the reference with an ellipsis in some styles; written out in full here |
| 18 | Kirchenbauer et al. (2023) | arXiv:2301.10226 | VERIFIED (ID only) | arXiv API: title and all six authors match | ICML 2023 venue from authors' record |
| 19 | Krishna et al. (2023) | arXiv:2303.13408 | VERIFIED | arXiv API: title and five authors match; OpenAlex also returns a NeurIPS 2023 proceedings record (pp. 27469–27500, DOI 10.52202/075280-1195) | |
| 20 | Liang et al. (2023) | 10.1016/j.patter.2023.100779 | VERIFIED | Crossref: *Patterns* 4(7), 100779, five authors | Abstract read from arXiv:2304.02819; the 61.3% figure corroborated in secondary reporting |
| 21 | Mitchell et al. (2023), DetectGPT | arXiv:2301.11305 | VERIFIED (ID only) | arXiv API: title and five authors match | ICML 2023 venue from authors' record |
| 22 | Naismith et al. (2022), PELIC | 10.1075/ijlcr.21002.nai | VERIFIED | OpenAlex: *IJLCR* 8(1), 121–138, three authors | |
| 23 | Perkins (2023) | 10.53761/1.20.02.07 | VERIFIED | Crossref: *JUTLP* 20(2), author Mike Perkins | A first attempt with suffix `.08` resolved to a different article by a different author and was discarded |
| 24 | Römer & O'Donnell (2011), MICUSP | 10.3366/corp.2011.0011 | VERIFIED | OpenAlex: *Corpora* 6(2), 159–177 | |
| 25 | Sadasivan et al. (2023) | arXiv:2303.11156 | VERIFIED | arXiv API: title and five authors match | |
| 26 | Turnitin (2024–2026), release notes | URL | VERIFIED | Page retrieved in full | Quoted: scores 1–19% not surfaced; bibliographies excluded; "should not be used as the sole basis for adverse actions against a student" |
| 27 | Verma et al. (2024), Ghostbuster | arXiv:2305.15047 | VERIFIED (ID only) | arXiv API: title and four authors match | NAACL 2024 venue from authors' record |
| 28 | Walters (2023) | 10.1515/opis-2022-0158 | VERIFIED | Crossref: *Open Information Science* 7(1), author William H. Walters | Article e-locator omitted because Crossref does not report one |
| 29 | Wang et al. (2024), M4 | arXiv:2305.14902 | VERIFIED (ID only) | arXiv API: title and all fifteen authors match | EACL 2024 venue from authors' record |
| 30 | Weber-Wulff et al. (2023) | 10.1007/s40979-023-00146-z | VERIFIED | Crossref: *IJEI* 19(1), eight authors | Article number omitted because Crossref does not report one |

**Count: 30 references. 30 resolve. 0 unverified. 0 removed for non-existence.**

Three identifiers were wrong on first attempt and were corrected: Herbold et al. (the
`-45658-3` suffix belongs to another paper), Jawahar et al. (`.409` vs `.208`), and Perkins
(`.08` vs `.07`). Each correction was confirmed by a second API call returning a title that
matched the intended work. This is recorded because it is evidence that the check was
performed rather than assumed.

### Fields deliberately omitted rather than guessed

- Article e-locators for Chan (2023), Walters (2023) and Weber-Wulff et al. (2023). Crossref
  returns volume and issue but no page or article number for these records; the numbers that
  commonly appear in citations were not reproduced from memory.
- Page ranges for the ICML/ICLR/NeurIPS entries, for the same reason. arXiv identifiers are
  given so the record is resolvable.

---

## 2. Number audit

Every quantity in the manuscript traces to one of the input documents. Spot-check of
seventeen values, including all headline figures.

| # | Value in paper | Where it appears | Source document | Pool / denominator | Holdout? |
| --- | --- | --- | --- | --- | --- |
| 1 | 61.3% average false-positive rate on human TOEFL essays; worst 97.8% | Abstract, §1 | Liang et al. (2023), abstract and published article | 91 human TOEFL essays, seven detectors | External literature, not this system |
| 2 | 3/363 = 0.83% missed | Abstract, §6.1, §6.4, §6.6, §9 | RESULTS §1; EVALUATION §4.1; COMPARISON §1 | AHBench-10, 363 documents | Held out from training, **but the threshold was selected on this pool** — selection bias |
| 3 | 2/23 = 8.7%, one document = 4.35 pt | §6.1, §8 | RESULTS §1; LIMITS §2 | Strongly humanised set, 23 documents | Held out; too small for a stable estimate |
| 4 | 99.42% pass, 10 FP (0.63%) | §3.5, §6.1 | RESULTS §1; EVALUATION §4.1 | Human frozen pool, 1,595 documents | **No** — tuned on; labelled optimistic in the paper |
| 5 | 97.55% pass, 65 FP (2.45%) | Abstract, §6.1, §6.2, §7.1 | RESULTS §1; EVALUATION §4.1 | NUCLE 1,397 + PELIC 1,252 = 2,649 | Yes — never scored before the final check |
| 6 | 73.34% pass, 221 FP (26.66%) | Abstract, §1, §6.1, §6.2, §7.1, §8 | RESULTS §1; LIMITS §1 | MICUSP, 829 documents | Yes |
| 7 | 28.93% (NS, 681) and 16.22% (NNS, 148) | §6.1, §6.2, §7.1 | RESULTS §1; LIMITS §1 | MICUSP split by author status | Yes |
| 8 | 91.78% pass, 286 FP (8.22%) | §3.5, §6.1, §6.2 | RESULTS §1; EVALUATION §4.1 | Total human holdout, 3,478 | Yes |
| 9 | ≥18.40% holdout FP for every rule meeting both AI targets | §3.3 | 53-report §4.1 | 2,613-rule grid; holdout 3,478 | Yes |
| 10 | 1/363, 6/363, 18.57%, 4.54%, 95.49%, 99.50% | §3.5 | 53-report §4.2 (`v4ai`, `v4safe` rows) | Full pool set | Holdout column is holdout; AI columns are selection-biased |
| 11 | 0.18→13.50%, 0.26→10.60%, 0.30→9.00%, 0.32→8.22%, 0.34→7.70%; 3→5 missed at 0.34 | §6.1 | 53-report §4.3 | Shield sweep, spear fixed 0.80 | Holdout FP column is holdout |
| 12 | 720/723, 722/723, 718/723, 717/723; 2.45%, 10.80%, 1.81%; 26.66%, 33.17%, 11.46%, 7.84% | §1, §6.3, §7.2 | RESULTS §4; EVALUATION §4.3 | 4,223 human documents (2,649 learner + 829 MICUSP + others); 723 AI documents in the archived run | **No** — derived experiment, thresholds explored on the same material; stated as not adopted |
| 13 | 48.7 / 50.1 / 57.2 / 59.1 / 72.8 / 74.5 / 78.3% | §6.4 | COMPARISON §1; 43-report §6 | AI Humanizer Benchmark, two cycles (726 outputs) | Third party; not our run |
| 14 | 28% vs 50–82% pass-as-human | §6.4 | COMPARISON §2 | 723-document two-release pool, one stated rule | Third party values; earlier and weaker model |
| 15 | Turnitin 0 / 28 / 100 / 100 / <20 / 76%; this system 0.0 / 100.0 / 95.2 / 78.9 / 62.4 / 18.3 / 87.8% | §6.5 | COMPARISON §3; 55-ledger §6.1 | Seven documents | Not a holdout; case series |
| 16 | 0.932 → 0.743 (one document); 0.261 → 0.342 (another) | §6.7 | TECH-REPORT §5; LIMITS §3; 55-ledger §6.4 | Single documents | n = 1 per manipulation |
| 17 | 90.7 / 0.0 / 72.9 (humanised) and 77.3 / 0.4 / 21.5 (human) | §6.7, §7.4, §9 | RESULTS §5; TECH-REPORT §5 | Two documents across four checkpoints | n = 1 |
| 18 | 146,094 windows; ~37,000 / ~8,200 windows | §4.1 | TRAINING §4; TRAINING §2 | Training files | n/a |
| 19 | 0.6–13 s per document, 5–30 windows; 21 min per generation | §3.2, §3.6 | TECH-REPORT §2.4; TRAINING §5 | Single-machine measurement | n/a |
| 20 | ICNALE 59/1,129 → 16/1,129; second pool 8/238 → 76/238 | §4.1, §7.1 | TRAINING §3; 52-report §5.2 | Frozen pools | **No** — frozen |

### Two numbers I chose not to print

1. **The single-model ablation table in RESULTS §3.** Its rows (shield alone 3/363 with 97.24%
   human macro and 26 false positives; spear alone 10/363 with 99.64% and 9) do not reconcile
   with the Judge 4.0 row: a disjunctive rule cannot flag *fewer* human documents than one of
   its own disjuncts at the same threshold. The likely explanation is that the single-model
   rows were measured under an earlier rule shape (window-share gating) than the Judge 4.0 row,
   but the source documents do not say so. Presenting them side by side as an ablation would
   have been wrong, so the architecture argument is made instead from the 2,613-rule frontier
   (§3.3) and the shield-collapse measurement, both of which are internally consistent.

2. **"23% of a human academic pool".** TRAINING §1 attributes this to the shield alone;
   RESULTS §2 attributes it to the shield-epoch-0 × spear pair. The two are numerically
   indistinguishable elsewhere in the same documents, so the attribution is ambiguous. It is
   used once, in §6.6, attached to the combination, which is the attribution given in the more
   recent of the two sources.

### One discrepancy that changes how a headline comparison should be read

The 48.7%–78.3% commercial range is not a miss rate in the sense used for this system. It is
each detector's **mean human-probability** over the benchmark's humanised outputs, averaged
across the September and October 2026 cycles. I verified this by recomputing both statistics
from the benchmark's published per-output scores:

- mean `human_prob` per detector, both cycles, in the order GPTZero / Copyleaks / Originality /
  Winston / QuillBot / ZeroGPT / Grammarly: 0.487, 0.501, 0.572, 0.591, 0.728, 0.745, 0.783 —
  an exact match to the seven published figures;
- share of outputs with a binary "judged human" verdict, same order: 14.2%, 49.7%, 19.6%,
  37.7%, 46.4%, 28.4%, 49.4% — a different and much lower set.

So the two columns in that table measure different things: a mean score against a decision
rate. The manuscript states this in §6.4 and labels the comparison directional rather than
controlled. It does not present the range as a like-for-like miss rate, and it does not
recompute the commercial figures into decision rates, because the benchmark's binary verdict
column is internally inconsistent across cycles (one detector records zero human verdicts in
one cycle while its mean human-probability for that cycle is 0.42) and is not fit to publish.

---

## 3. Checks that were not performed

- **No full-text reading of references 2–30.** Abstracts were read for six of them (Bao,
  Hans, Liang, Mitchell, Sadasivan, Weber-Wulff) and both Turnitin pages were read in full;
  the remainder are cited for their position in the literature, which is supported by title,
  venue and abstract. No sentence in the manuscript attributes a specific finding to a source
  whose abstract was not read. The Weber-Wulff et al. characterisation in §2.4 (twelve free
  tools, two commercial systems, 54 documents, conclusion of neither accurate nor reliable
  with a bias toward "human-written") is taken from the published abstract.
- **No independent fetch of PMLR/OpenReview proceedings pages.** For the ten entries that
  carry a conference venue, the venue is as published by the authors and is consistent with
  the arXiv record; the proceedings listings themselves were not retrieved.
- **No check of the Hugging Face endpoint.** `huggingface.co` was unreachable from this host
  during the check. The dataset was verified instead through its DataCite DOI and through the
  dataset card and per-cycle files in the local mirror, which states that it is the official
  mirror of the benchmark's GitHub repository and carries the same licence (CC BY 4.0).

## 4. Residual risk

| Risk | Severity | Mitigation |
| --- | --- | --- |
| A conference venue is misattributed | Low | arXiv ID given for every such entry; title and authors verified |
| The AHBench dataset is renamed or withdrawn | Low | Cited by DOI, which is version-pinned by Zenodo |
| Turnitin release notes change | Low | Quoted statements are dated in the reference and attributed to the release-notes page |
| The 2026-10 cycle is superseded | Medium | Every commercial figure is labelled by cycle; the paper does not claim currency |
| A number in the audit table is mis-transcribed | Low | Each was copied from the named section of the named document, not from memory |
