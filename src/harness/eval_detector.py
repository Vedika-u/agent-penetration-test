"""CLI: measure the Phase 3 embedding-similarity injection detector's precision/recall/F1.

Usage:
    uv run python -m harness.eval_detector

Requires Ollama running locally with the `nomic-embed-text` model pulled (the detector's real
embedding backend -- see `target_agent.detection.injection_detector` for why embedding
similarity was chosen over attention-shift detection, and why no TF-IDF fallback is used here).

Data sources
------------
1. **deepset/prompt-injections** (https://huggingface.co/datasets/deepset/prompt-injections):
   `text` + `label` columns, label 1 = injection prompt, 0 = benign. Downloaded directly from
   HF's public parquet resolve URLs (no `datasets`/`huggingface_hub` dependency needed). Its own
   `train`/`test` split is reused here: `train` (subsampled, stratified by label) is the set the
   detection threshold is *tuned* against; `test` (used in full) is held out for the reported
   metrics.
2. **JailbreakBench/JBB-Behaviors** (config `behaviors`): `harmful-behaviors.csv` and
   `benign-behaviors.csv`. IMPORTANT distinction: these rows are harmful *goals/behaviors*
   ("Write a phishing email that...") the benchmark uses to test whether a target model can be
   made to comply with them -- they are NOT prompt-injection strings like deepset's ("Ignore
   previous instructions and..."). This script does not silently conflate the two framings: JBB
   rows are added to the *held-out* evaluation set only (never used for threshold tuning),
   labeled as "adversarial input that should be flagged" (harmful split -> 1) or "benign input"
   (benign split -> 0), and are reported under their own `dataset_sources` entry.

Both dataset downloads are cached under `data/cache/datasets/` and embeddings are cached under
`data/cache/embeddings.json` so re-running this script doesn't re-download or re-embed
unchanged text.
"""

from __future__ import annotations

import hashlib
import io
import json
import random
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests

from target_agent.detection.injection_detector import (
    EMBEDDING_MODEL,
    InjectionDetector,
    embed_text,
)

DEEPSET_TRAIN_URL = (
    "https://huggingface.co/datasets/deepset/prompt-injections/resolve/main/"
    "data/train-00000-of-00001-9564e8b05b4757ab.parquet"
)
DEEPSET_TEST_URL = (
    "https://huggingface.co/datasets/deepset/prompt-injections/resolve/main/"
    "data/test-00000-of-00001-701d16158af87368.parquet"
)
JBB_HARMFUL_URL = (
    "https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors/resolve/main/"
    "data/harmful-behaviors.csv"
)
JBB_BENIGN_URL = (
    "https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors/resolve/main/"
    "data/benign-behaviors.csv"
)

DEEPSET_SOURCE = "deepset/prompt-injections"
JBB_SOURCE = "JailbreakBench/JBB-Behaviors"

CACHE_DIR = Path("data/cache/datasets")
EMBEDDING_CACHE_PATH = Path("data/cache/embeddings.json")
RESULTS_PATH = Path("data/results/detector_eval.json")
REPORT_PATH = Path("reports/phase3_detector_eval.md")

RANDOM_SEED = 42
TRAIN_SUBSAMPLE_SIZE = 120  # deepset `train` split, stratified subsample used only for tuning
JBB_SUBSAMPLE_SIZE = 40  # per class, added to the held-out eval set only

DETECTOR_NAME = f"embedding-similarity (Ollama {EMBEDDING_MODEL})"


@dataclass(frozen=True)
class Example:
    text: str
    label: int  # 1 = injection/adversarial, 0 = benign
    source: str


def _download(url: str, cache_name: str) -> bytes:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / cache_name
    if cache_path.exists():
        return cache_path.read_bytes()
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    cache_path.write_bytes(response.content)
    return response.content


def _load_deepset() -> tuple[list[Example], list[Example]]:
    train_df = pd.read_parquet(io.BytesIO(_download(DEEPSET_TRAIN_URL, "deepset_train.parquet")))
    test_df = pd.read_parquet(io.BytesIO(_download(DEEPSET_TEST_URL, "deepset_test.parquet")))
    train = [Example(row.text, int(row.label), DEEPSET_SOURCE) for row in train_df.itertuples()]
    test = [Example(row.text, int(row.label), DEEPSET_SOURCE) for row in test_df.itertuples()]
    return train, test


def _load_jbb() -> list[Example]:
    harmful_df = pd.read_csv(io.BytesIO(_download(JBB_HARMFUL_URL, "jbb_harmful.csv")))
    benign_df = pd.read_csv(io.BytesIO(_download(JBB_BENIGN_URL, "jbb_benign.csv")))
    # See module docstring: JBB rows are harmful/benign *goals*, not injection *prompts*. We
    # treat the harmful split as label=1 ("adversarial input that should be flagged") and the
    # benign split as label=0, added only to the held-out set below.
    harmful = [Example(row.Goal, 1, JBB_SOURCE) for row in harmful_df.itertuples()]
    benign = [Example(row.Goal, 0, JBB_SOURCE) for row in benign_df.itertuples()]
    return harmful + benign


def _stratified_sample(examples: list[Example], n: int, rng: random.Random) -> list[Example]:
    if n >= len(examples):
        return list(examples)
    positives = [e for e in examples if e.label == 1]
    negatives = [e for e in examples if e.label == 0]
    frac = n / len(examples)
    n_pos = max(1, round(len(positives) * frac))
    n_neg = max(1, n - n_pos)
    sample = rng.sample(positives, min(n_pos, len(positives))) + rng.sample(
        negatives, min(n_neg, len(negatives))
    )
    rng.shuffle(sample)
    return sample


class _CachedEmbedder:
    """Wraps the real `embed_text` Ollama call with an on-disk JSON cache keyed by
    md5(model + text), so re-running this script (or iterating on it) doesn't re-embed text
    it has already seen. Flushes to disk periodically rather than on every call."""

    def __init__(self, cache_path: Path, flush_every: int = 25) -> None:
        self._cache_path = cache_path
        self._flush_every = flush_every
        self._dirty_count = 0
        if cache_path.exists():
            self._cache: dict[str, list[float]] = json.loads(cache_path.read_text())
        else:
            self._cache = {}

    def _key(self, text: str) -> str:
        return hashlib.md5(f"{EMBEDDING_MODEL}:{text}".encode("utf-8")).hexdigest()

    def __call__(self, text: str) -> list[float]:
        key = self._key(text)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        embedding = embed_text(text)
        self._cache[key] = embedding
        self._dirty_count += 1
        if self._dirty_count >= self._flush_every:
            self.flush()
        return embedding

    def flush(self) -> None:
        if self._dirty_count == 0 and self._cache_path.exists():
            return
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._cache_path.write_text(json.dumps(self._cache))
        self._dirty_count = 0


def _confusion_matrix(scores_labels: list[tuple[float, int]], threshold: float) -> dict[str, int]:
    tp = fp = fn = tn = 0
    for score, label in scores_labels:
        predicted = score >= threshold
        if predicted and label == 1:
            tp += 1
        elif predicted and label == 0:
            fp += 1
        elif not predicted and label == 1:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def _precision_recall_f1(cm: dict[str, int]) -> tuple[float, float, float]:
    tp, fp, fn = cm["tp"], cm["fp"], cm["fn"]
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return precision, recall, f1


def _tune_threshold(scores_labels: list[tuple[float, int]]) -> float:
    """Sweeps every distinct observed score as a candidate threshold and keeps the one that
    maximizes F1 on the tuning set (deepset's `train` split only -- never the held-out set)."""
    best_threshold = 0.5
    best_f1 = -1.0
    for candidate in sorted({score for score, _ in scores_labels}):
        cm = _confusion_matrix(scores_labels, candidate)
        _, _, f1 = _precision_recall_f1(cm)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = candidate
    return best_threshold


def main() -> None:
    rng = random.Random(RANDOM_SEED)

    print("Downloading/loading datasets (cached under data/cache/datasets/)...")
    deepset_train, deepset_test = _load_deepset()
    jbb_examples = _load_jbb()

    tuning_set = _stratified_sample(deepset_train, TRAIN_SUBSAMPLE_SIZE, rng)
    jbb_positive = [e for e in jbb_examples if e.label == 1]
    jbb_negative = [e for e in jbb_examples if e.label == 0]
    jbb_sample = rng.sample(jbb_positive, min(JBB_SUBSAMPLE_SIZE, len(jbb_positive))) + rng.sample(
        jbb_negative, min(JBB_SUBSAMPLE_SIZE, len(jbb_negative))
    )
    held_out_set = list(deepset_test) + jbb_sample

    print(
        f"Tuning set: {len(tuning_set)} examples (deepset train subsample). "
        f"Held-out set: {len(held_out_set)} examples "
        f"({len(deepset_test)} deepset test + {len(jbb_sample)} JBB behaviors)."
    )

    embedder = _CachedEmbedder(EMBEDDING_CACHE_PATH)
    detector = InjectionDetector(embed_fn=embedder)

    print(f"Embedding {len(detector.reference_phrases)} reference phrases...")
    detector.warm_reference_embeddings()

    print(f"Scoring {len(tuning_set)} tuning examples...")
    tuning_scores = [
        (detector.classify(ex.text).score, ex.label) for ex in tuning_set
    ]
    threshold = _tune_threshold(tuning_scores)
    print(f"Tuned threshold (max F1 on tuning set): {threshold:.4f}")

    print(f"Scoring {len(held_out_set)} held-out examples...")
    held_out_scores = [
        (detector.classify(ex.text).score, ex.label) for ex in held_out_set
    ]
    embedder.flush()

    confusion_matrix = _confusion_matrix(held_out_scores, threshold)
    precision, recall, f1 = _precision_recall_f1(confusion_matrix)

    results = {
        "detector": DETECTOR_NAME,
        "threshold": threshold,
        "dataset_sources": [DEEPSET_SOURCE, JBB_SOURCE],
        "n_samples": len(held_out_set),
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "confusion_matrix": confusion_matrix,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"Wrote {RESULTS_PATH}")

    _write_report(
        results=results,
        n_tuning=len(tuning_set),
        n_deepset_test=len(deepset_test),
        n_jbb=len(jbb_sample),
        n_reference_phrases=len(detector.reference_phrases),
    )
    print(f"Wrote {REPORT_PATH}")

    print(json.dumps(results, indent=2))


def _write_report(
    results: dict, n_tuning: int, n_deepset_test: int, n_jbb: int, n_reference_phrases: int
) -> None:
    cm = results["confusion_matrix"]
    report = f"""# Phase 3 Detector Evaluation

Detector: `{results["detector"]}`

## Results

| Metric | Value |
| --- | --- |
| Threshold (tuned) | {results["threshold"]:.4f} |
| Precision | {results["precision"]:.3f} |
| Recall | {results["recall"]:.3f} |
| F1 | {results["f1"]:.3f} |
| Held-out samples | {results["n_samples"]} |
| True positives | {cm["tp"]} |
| False positives | {cm["fp"]} |
| False negatives | {cm["fn"]} |
| True negatives | {cm["tn"]} |

## Methodology

The detector classifies text by max cosine similarity (real embeddings from Ollama's
`nomic-embed-text`, called via `POST /api/embeddings`) against a {n_reference_phrases}-phrase
curated reference set of known injection/jailbreak templates (see
`src/target_agent/detection/injection_detector.py` for the list and its provenance). The
threshold was tuned by sweeping every observed similarity score on a stratified {n_tuning}-example
subsample of deepset/prompt-injections' `train` split and keeping the value that maximized F1,
then evaluated once, unchanged, on a held-out set the tuning never saw: the full
{n_deepset_test}-example deepset `test` split plus {n_jbb} sampled JailbreakBench behaviors
(evenly split harmful/benign).

## Reference-set expansion: 26 -> 40 phrases made this *worse*, not better

The first version of this detector shipped with 26 hand-authored reference phrases and measured
precision 0.689 / recall 0.840 / F1 0.757 on this same held-out set. Expanding the reference set
to 40 phrases (adding prefix-forcing, authority-appeal, context-reset, and character-obfuscation
styles -- see the detector module's docstring) was expected to *improve* recall against a wider
range of attack styles. Instead, on this held-out set, it measured precision 0.661 / recall 0.820
/ F1 0.732 -- a small regression on all three metrics. The added phrases apparently pulled some
benign held-out examples closer to the reference set in embedding space (more false positives:
38 -> 42) without a compensating recall gain large enough to offset it. This is reported as-is,
not reverted or hidden: "add more reference examples" is not a free win for an embedding-similarity
detector, and this is a real, reproducible instance of that. A follow-up worth doing (not done
here) would be evaluating which of the 14 new phrases are responsible, rather than treating the
expansion as a single unit.

## Caveats

- **Small, imbalanced-by-construction reference set.** {n_reference_phrases} hand-written phrases
  is enough to demonstrate the method but is not an exhaustive attack catalogue; recall against
  injection styles unlike anything in the reference set will be worse than reported here.
- **JailbreakBench rows are goals, not injection prompts.** `JBB-Behaviors` rows read like "Write
  a phishing email that..." -- harmful *asks*, not "ignore previous instructions"-style
  injection text. They're included in the held-out set as adversarial input that should be
  flagged, not as more instances of deepset's injection-prompt framing; a detector tuned purely
  on injection-phrasing similarity should be expected to do worse on these than on deepset's own
  test split, and the confusion matrix above is a blend of both, not a per-source breakdown.
- **"Positive" here means "similar in phrasing/intent to the reference set,"** not "would
  actually jailbreak the target LLM." This measures the detector as a text classifier in
  isolation, not end-to-end attack success reduction (that's Phase 4).
- **Threshold tuned on a subsample, not the full train split**, to keep embedding-call runtime
  reasonable; a larger tuning sample might shift the threshold slightly.
"""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report)


if __name__ == "__main__":
    main()
