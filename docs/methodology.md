# Methodology

SynthSift is an intentionally small methodological pilot, not a systematic review and not a performance claim about production screening systems.

## Screening task
The primary analysis uses only rows with `primary_benchmark=1`: records for which the screening text was verified as source-authored abstract/summary text from the linked public source during the provenance audit. Legacy paraphrases are retained in the dataset for auditability but excluded from the headline benchmark.

Two deliberately lightweight baselines are evaluated:

- word TF-IDF (1–2 grams) + class-balanced logistic regression;
- character TF-IDF (3–5 grams) + class-balanced logistic regression.

Repeated stratified k-fold cross-validation generates out-of-fold scores. Each record receives one held-out prediction per repeat; scores are averaged across repeats. This avoids reporting an in-sample fit and makes the ranking less dependent on a single split. Because the dataset is small, results remain exploratory.

Metrics include precision, recall, F1, confusion matrix, false negatives, workload reduction at target recalls, and non-parametric bootstrap confidence intervals. Models are reported separately; the analysis does **not** choose a winner and then reuse the same data to advertise that model's workload reduction.

## Extraction task
A small reference table for included records contains country, study design, sample size and factor tags. `run_extraction_benchmark.py` evaluates a transparent deterministic baseline for country, study-design and sample-size extraction. This is deliberately a baseline: its purpose is to establish an auditable evaluation harness into which LLM or NLP extraction outputs can later be dropped.

## Provenance and limitations
Some original pilot records contained AI-rewritten summaries. They are explicitly marked `derived_summary` and excluded from the primary benchmark. A source mismatch detected for R14 is marked `source_mismatch`. The project never treats a generated summary as a verbatim abstract.

Reference labels are protocol-based pilot decisions and have not undergone dual independent human screening. The dataset is curated and small; prevalence and difficulty do not represent a database search result set. Workload-reduction percentages therefore illustrate the calculation, not expected real-world savings.
