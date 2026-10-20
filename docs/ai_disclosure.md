# AI-assistance disclosure

AI tools were used during project development for code assistance, public-source retrieval, provenance checking and methodological critique. The repository records this rather than presenting AI-assisted work as unaided manual work.

The screening reference labels are protocol-based pilot decisions and should not be described as independent dual-human ground truth. Any future human adjudication should be recorded as a new decision layer, preserving the existing labels for auditability.

No LLM screening or extraction result is reported unless an actual model run and its configuration/output are committed. The current benchmark therefore reports only locally reproducible scikit-learn screening baselines and a deterministic extraction baseline.

## October 2026 AI-assisted sample screening

GPT-6 generated title/available-abstract eligibility recommendations and individual reasons for the frozen 240-record Phase-1 sample. A subsequent full-abstract check covered selected borderline records; other abstracts were initially screened from excerpts. The files are explicitly attributed to `ai_assistant_gpt6_20261020` and are stored only under `data/ai_screening/`. They are **machine-assisted suggestions, not independently reviewed human labels**. They must not be used to report screening-model accuracy, replace the 96-record blinded independent-review sample, claim human agreement, or serve as final inclusion decisions in a systematic review.
