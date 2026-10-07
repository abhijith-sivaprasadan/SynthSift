# Annotation workspace

`scripts/screen_queue.py` writes in-progress reviewer decisions here.

CSV annotation files are intentionally ignored by Git while screening is ongoing. This prevents partial or changing decisions from becoming accidental benchmark labels.

When a reference set is ready to freeze:

1. validate reviewer coverage and unresolved `uncertain` records;
2. preserve each reviewer's original decisions;
3. adjudicate disagreements in a separate field/table;
4. export the frozen labels to a versioned file under `data/labels/`;
5. only then run model benchmarking against that version.
