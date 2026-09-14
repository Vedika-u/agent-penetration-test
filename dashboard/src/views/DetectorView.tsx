import { useJson } from "../lib/useJson";
import { DataState } from "../components/DataState";
import { StatTile } from "../components/StatTile";
import { ConfusionMatrixGrid } from "../components/ConfusionMatrixGrid";
import type { DetectorEval } from "../types";

const DATA_PATH = `${import.meta.env.BASE_URL}data/detector_eval.json`;

export function DetectorView() {
  const state = useJson<DetectorEval>(DATA_PATH);

  return (
    <DataState state={state} path={DATA_PATH}>
      {(data) => (
        <div className="view">
          <header className="view__header">
            <h2>Detector confusion matrix</h2>
            <p className="view__subtitle">
              <strong>{data.detector}</strong> · threshold {data.threshold} ·{" "}
              {data.n_samples} samples from {data.dataset_sources.join(", ")}
            </p>
          </header>

          <div className="stat-row">
            <StatTile label="Precision" value={data.precision.toFixed(3)} tone="neutral" />
            <StatTile label="Recall" value={data.recall.toFixed(3)} tone="neutral" />
            <StatTile label="F1" value={data.f1.toFixed(3)} tone="good" />
            <StatTile label="Samples" value={String(data.n_samples)} tone="neutral" />
          </div>

          <div className="panel">
            <ConfusionMatrixGrid matrix={data.confusion_matrix} />
          </div>
        </div>
      )}
    </DataState>
  );
}
