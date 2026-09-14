import { useJson } from "../lib/useJson";
import { DataState } from "../components/DataState";
import { TranscriptsView } from "../components/TranscriptsView";
import type { TranscriptsSample } from "../types";

const DATA_PATH = `${import.meta.env.BASE_URL}data/transcripts_sample.json`;

export function TranscriptsPage() {
  const state = useJson<TranscriptsSample>(DATA_PATH);

  return (
    <DataState state={state} path={DATA_PATH}>
      {(data) => (
        <div className="view">
          <header className="view__header">
            <h2>Annotated transcripts</h2>
            <p className="view__subtitle">
              {data.length} sampled (prompt, response) pairs with detector and ground-truth
              labels
            </p>
          </header>
          <TranscriptsView transcripts={data} />
        </div>
      )}
    </DataState>
  );
}
