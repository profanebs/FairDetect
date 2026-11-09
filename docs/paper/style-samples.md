# Style and structure samples

Purpose: to fix the register, section conventions and hedging habits of the FairDetect paper
against published work in AI-text detection, academic integrity and learner-corpus research.
This is an internal working note, not part of the manuscript.

Selection rule: prefer papers that (a) are verifiable, (b) represent the genre the manuscript
belongs to — an evaluation paper reporting a detector — and (c) differ from each other in what
they do well, so that no single paper's habits dominate. Where a vendor or benchmark is the
only authoritative source for a number, the document itself is used as a sample.

"Consulted" records what was actually read while drafting, not what the paper contains.
Claims about a source's content are limited to what was read.

---

## A. Detection methods

### 1. Liang, W., Yuksekgonul, M., Mao, Y., Wu, E., & Zou, J. (2023). GPT detectors are biased against non-native English writers. *Patterns*, 4(7), 100779.

- **Why chosen**: the empirical study that defines the problem this paper addresses. Its
  structure — one striking measurement, then a controlled comparison, then an ethical
  conclusion scoped to deployment — is the model for the Introduction.
- **What was taken**: open with a single quantified harm rather than with the technology;
  keep the policy claim in a separate closing paragraph instead of mixing it into results.
- **Consulted**: abstract (arXiv:2304.02819 and publisher indexing); the 61.3% average
  false-positive figure cross-checked against secondary reporting.

### 2. Mitchell, E., Lee, Y., Khazatsky, A., Manning, C. D., & Finn, C. (2023). DetectGPT: Zero-shot machine-generated text detection using probability curvature. ICML 2023.

- **Why chosen**: a method paper that isolates one mechanism and reports it cleanly.
- **What was taken**: describe the mechanism before the numbers; state explicitly what the
  method does *not* require (no training data, no watermark) — the same move is used in §3
  to explain why the decision layer is separate from the models.
- **Consulted**: abstract (arXiv:2301.11305).

### 3. Bao, G., Zhao, Y., Teng, Z., Yang, L., & Zhang, Y. (2024). Fast-DetectGPT: Efficient zero-shot detection of machine-generated text via conditional probability curvature. ICLR 2024.

- **Why chosen**: shows how to report a cost/quality trade without overclaiming.
- **What was taken**: quantify both axes (accuracy gain and speed-up) in one sentence, and
  attribute each to a named table. Used for the CPU-latency reporting in §3.6.
- **Consulted**: abstract (arXiv:2310.05130).

### 4. Hans, A., Schwarzschild, A., Cherepanova, V., Kazemi, H., Saha, A., Goldblum, M., Geiping, J., & Goldstein, T. (2024). Spotting LLMs with binoculars: Zero-shot detection of machine-generated text. ICML 2024.

- **Why chosen**: the cleanest example in this literature of stating a result at a fixed
  false-positive rate rather than at a fixed threshold.
- **What was taken**: always name the operating constraint alongside a recall figure. This is
  why every AI-side number in the manuscript carries its human-side cost next to it.
- **Consulted**: abstract (arXiv:2401.12070).

### 5. Verma, V., Fleisig, E., Tomlin, N., & Klein, D. (2024). Ghostbuster: Detecting text ghostwritten by large language models. NAACL 2024.

- **Why chosen**: a trained-classifier detector, closest in family to the present system.
- **What was taken**: the convention of reporting a classifier's behaviour across several
  generator families rather than a single source model; mirrored in the generation table (§6.2).
- **Consulted**: metadata and abstract (arXiv:2305.15047).

### 6. Sadasivan, V. S., Kumar, A., Balasubramanian, S., Wang, W., & Feizi, S. (2023). Can AI-generated text be reliably detected? arXiv:2303.11156.

- **Why chosen**: the theoretical counterweight. Any detector paper that omits the
  impossibility argument reads as naive.
- **What was taken**: state the threat model before the defence; separate "detectable in
  principle" from "reliable under an adversary". Shapes §7.3 and §8.
- **Consulted**: abstract (arXiv:2303.11156).

### 7. Krishna, K., Song, Y., Karpinska, M., Wieting, J., & Iyyer, M. (2023). Paraphrasing evades detectors of AI-generated text, but retrieval is an effective defence. NeurIPS 2023.

- **Why chosen**: the canonical paraphrase-attack result; the reason a humanized-AI pool is
  part of the evaluation rather than an afterthought.
- **What was taken**: treat humanization as an adversary with a named capability, not as noise.
- **Consulted**: metadata and abstract (arXiv:2303.13408).

### 8. Kirchenbauer, J., Geiping, J., Wen, Y., Katz, J., Miers, I., & Goldstein, T. (2023). A watermark for large language models. ICML 2023.

- **Why chosen**: the main alternative to post-hoc detection; needed so Related Work does not
  present classification as the only option.
- **What was taken**: one paragraph that positions watermarking by its preconditions
  (provider cooperation) rather than by accuracy.
- **Consulted**: abstract (arXiv:2301.10226).

### 9. Gehrmann, S., Strobelt, H., & Rush, A. M. (2019). GLTR: Statistical detection and visualization of generated text. ACL 2019 (System Demonstrations).

- **Why chosen**: the origin of the "detection as a display, not a verdict" idea that this
  paper's reporting convention inherits.
- **What was taken**: report interpretable intermediate quantities to a human reviewer
  instead of a single label.
- **Consulted**: metadata (DOI 10.18653/v1/P19-3019).

### 10. Jawahar, G., Abdul-Mageed, M., & Lakshmanan, L. V. S. (2020). Automatic detection of machine generated text: A critical survey. COLING 2020.

- **Why chosen**: the survey that organised the pre-LLM taxonomy this paper still uses
  (statistical vs. neural vs. watermark).
- **What was taken**: the three-way division of Related Work.
- **Consulted**: metadata (DOI 10.18653/v1/2020.coling-main.208).

---

## B. Evaluation and benchmarking

### 11. Weber-Wulff, D., Anohina-Naumeca, A., Bjelobaba, S., Foltýnek, T., Guerrero-Dib, J., Popoola, O., Šigut, P., & Waddington, L. (2023). Testing of detection tools for AI-generated text. *International Journal for Educational Integrity*, 19, 26.

- **Why chosen**: the best available model for the sentence "here is what we tested, and here
  is why it cannot support the claim you want to make".
- **What was taken**: report the number of documents tested next to every comparative claim;
  refuse rankings that the sample cannot support. Used for the seven-document Turnitin
  comparison (§6.5), which is reported as an observation and explicitly not as a ranking.
- **Consulted**: metadata (DOI 10.1007/s40979-023-00146-z) and the published abstract.

### 12. Walters, W. H. (2023). The effectiveness of software designed to detect AI-generated writing: A comparison of 16 AI text detectors. *Open Information Science*, 7(1).

- **Why chosen**: multi-detector comparison with an explicit corpus description.
- **What was taken**: the table-plus-caveat pattern — a comparison table followed immediately
  by a paragraph beginning "what this is not".
- **Consulted**: metadata (DOI 10.1515/opis-2022-0158) and the published abstract.

### 13. Dugan, L., Hwang, A., Trhlik, F., Ludan, J. M., Zhu, A., Xu, H., Ippolito, D., & Callison-Burch, C. (2024). RAID: A shared benchmark for robust evaluation of machine-generated text detectors. ACL 2024.

- **Why chosen**: the current standard for arguing that a detector's numbers depend on the
  sampling frame.
- **What was taken**: name the axes of variation (generator, domain, decoding, attack) before
  reporting a single aggregate. This produced the pool-registration table in §4.
- **Consulted**: metadata and abstract (arXiv:2405.07940).

### 14. Wang, Y., Mansurov, J., Ivanov, P., Su, J., Shelmanov, A., Tsvigun, A., Whitehouse, C., Afzal, O. M., Mahmoud, T., Sasaki, T., Arnold, T., Aji, A. F., Habash, N., Gurevych, I., & Nakov, P. (2024). M4: Multi-generator, multi-domain, and multi-lingual black-box machine-generated text detection. EACL 2024.

- **Why chosen**: establishes that cross-generator generalisation is the hard part, which is
  exactly what the humanized-AI pool measures.
- **What was taken**: the phrase-level habit of naming the generalisation gap as a *result*
  rather than as a limitation buried at the end.
- **Consulted**: metadata and abstract (arXiv:2305.14902).

### 15. AI Humanizer Benchmark. (2026). AI Humanizer Benchmark: monthly cycle data [Data set]. Zenodo. https://doi.org/10.5281/zenodo.22966275

- **Why chosen**: the only source for the commercial comparison, and a well-documented
  example of how to report a third-party benchmark without implying you ran it.
- **What was taken**: quote the cycle, the version stamps and the exact statistic; never
  quote a bare percentage. The dataset card's own wording ("each cycle's scoring code is
  frozen and published with it") is the model for §6.4's provenance paragraph.
- **Consulted**: full dataset card and README; per-cycle leaderboard file for the 2026-10
  release.

---

## C. Context: integrity, assessment and learner writing

### 16. Casal, J. E., & Kessler, M. (2023). Can linguists distinguish between ChatGPT/AI and human writing? A study of research ethics and academic publishing. *Research Methods in Applied Linguistics*, 2(3), 100068.

- **Why chosen**: the human-ceiling result. Any claim that a detector "detects AI" has to be
  read against the fact that expert humans do poorly at the same task.
- **What was taken**: the comparison class for a detector is not perfection but expert
  judgement; used once, in §7.1, without overstating it.
- **Consulted**: metadata (DOI 10.1016/j.rmal.2023.100068) and abstract.

### 17. Herbold, S., Hautli-Janisz, A., Heuer, U., Kikteva, Z., & Trautsch, A. (2023). A large-scale comparison of human-written versus ChatGPT-generated essays. *Scientific Reports*, 13, 18617.

- **Why chosen**: the register-gap finding — generated essays differ from student essays in
  ways that are *not* about quality — is the mechanism behind the MICUSP result.
- **What was taken**: discuss feature-level differences (lexical diversity, nominal style)
  rather than only aggregate accuracy; used in §7.1 to interpret the discipline ordering.
- **Consulted**: metadata (DOI 10.1038/s41598-023-45644-9) and abstract.

### 18. Perkins, M. (2023). Academic integrity considerations of AI large language models in the post-pandemic era: ChatGPT and beyond. *Journal of University Teaching & Learning Practice*, 20(2).

- **Why chosen**: the policy-facing register the Discussion has to be legible in.
- **What was taken**: the "what institutions should and should not do with this output"
  framing in §7.5, kept short and free of exhortation.
- **Consulted**: metadata (DOI 10.53761/1.20.02.07) and abstract.

### 19. Cotton, D. R. E., Cotton, P. A., & Shipway, J. R. (2024). Chatting and cheating: Ensuring academic integrity in the era of ChatGPT. *Innovations in Education and Teaching International*, 61(2), 228–239.

- **Why chosen**: shows how to write about misconduct risk without accusing anyone.
- **What was taken**: the distinction between detection evidence and misconduct evidence,
  which the Limitations section has to make unambiguous.
- **Consulted**: metadata (DOI 10.1080/14703297.2023.2190148) and abstract.

---

## D. Vendor documentation

### 20. Turnitin. (2023–2024). AI writing detection: false positives and model release notes.

Two documents: Chechitelli, A. (2023, March 16), "Understanding false positives within our AI
writing detection capabilities"; and Turnitin Guides, "AI writing detection model" (release
notes through 2026).

- **Why chosen**: the only authoritative statement of what a commercial score means, and the
  clearest example of a vendor bounding its own product.
- **What was taken**: quote vendor statements verbatim and attribute them; do not paraphrase
  a vendor's accuracy claim into a stronger one. Also the source of the "<1% false positive"
  figure and the 20% display floor, both quoted in §2.5 and §6.5.
- **Consulted**: both pages in full.

---

## What was deliberately not imitated

- **Leaderboard posts and blog comparisons.** They optimise for a single rank and omit the
  sampling frame. The manuscript reports ranges and pool sizes instead.
- **Vendor marketing pages.** Claims there are unverifiable by construction; only the
  documentation pages that bound the product are used.
- **The "our detector beats GPTZero" genre.** Even where the numbers favour this system, the
  manuscript states the statistic mismatch rather than the ranking, because the comparison
  is not a controlled experiment.

## Register notes derived from the set

1. Numbers carry their denominator in the same sentence, not in a footnote.
2. Every comparison paragraph ends with what the comparison cannot establish.
3. Architecture claims are stated as consequences of a measurement, never as design
   intuition that the measurement confirms post hoc.
4. The word "detect" is avoided where "flag" is meant; a detector outputs a decision, not a
   fact about authorship.
5. No sentence begins with "Moreover", "Furthermore" or "In conclusion".
