# Phase 3 Detector Evaluation

Detector: `embedding-similarity (Ollama nomic-embed-text)`

## Results

| Metric | Value |
| --- | --- |
| Threshold (tuned) | 0.4581 |
| Precision | 0.661 |
| Recall | 0.820 |
| F1 | 0.732 |
| Held-out samples | 196 |
| True positives | 82 |
| False positives | 42 |
| False negatives | 18 |
| True negatives | 54 |

## Methodology

The detector classifies text by max cosine similarity (real embeddings from Ollama's
`nomic-embed-text`, called via `POST /api/embeddings`) against a 40-phrase
curated reference set of known injection/jailbreak templates (see
`src/target_agent/detection/injection_detector.py` for the list and its provenance). The
threshold was tuned by sweeping every observed similarity score on a stratified 120-example
subsample of deepset/prompt-injections' `train` split and keeping the value that maximized F1,
then evaluated once, unchanged, on a held-out set the tuning never saw: the full
116-example deepset `test` split plus 80 sampled JailbreakBench behaviors
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

- **Small, imbalanced-by-construction reference set.** 40 hand-written phrases
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
