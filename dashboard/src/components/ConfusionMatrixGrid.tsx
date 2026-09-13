import type { ConfusionMatrix } from "../types";

interface ConfusionMatrixGridProps {
  matrix: ConfusionMatrix;
}

/**
 * Rows are ground truth (attack / benign), columns are the detector's call
 * (flagged / not flagged) — standard orientation: TP top-left, TN bottom-right.
 */
export function ConfusionMatrixGrid({ matrix }: ConfusionMatrixGridProps) {
  const total = matrix.tp + matrix.fp + matrix.fn + matrix.tn;
  const cell = (value: number, kind: "tp" | "fp" | "fn" | "tn") => {
    const share = total > 0 ? value / total : 0;
    return (
      <div className={`cm-cell cm-cell--${kind}`}>
        <div className="cm-cell__value">{value}</div>
        <div className="cm-cell__share">{(share * 100).toFixed(1)}% of samples</div>
      </div>
    );
  };

  return (
    <div className="cm-grid">
      <div className="cm-grid__corner" />
      <div className="cm-grid__col-label">Flagged</div>
      <div className="cm-grid__col-label">Not flagged</div>

      <div className="cm-grid__row-label">Attack (ground truth)</div>
      {cell(matrix.tp, "tp")}
      {cell(matrix.fn, "fn")}

      <div className="cm-grid__row-label">Benign (ground truth)</div>
      {cell(matrix.fp, "fp")}
      {cell(matrix.tn, "tn")}
    </div>
  );
}
