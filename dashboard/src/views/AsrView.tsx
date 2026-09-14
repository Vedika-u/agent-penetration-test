import { useJson } from "../lib/useJson";
import { DataState } from "../components/DataState";
import { AsrBarChart } from "../components/AsrBarChart";
import { StatTile } from "../components/StatTile";
import type { BenchmarkAsr } from "../types";

const DATA_PATH = `${import.meta.env.BASE_URL}data/benchmark_asr.json`;

export function AsrView() {
  const state = useJson<BenchmarkAsr>(DATA_PATH);

  return (
    <DataState state={state} path={DATA_PATH}>
      {(data) => {
        const delta = data.asr_before_overall - data.asr_after_overall;
        const relativeDropLabel =
          data.asr_before_overall === 0
            ? "baseline ASR was already 0%"
            : `${((delta / data.asr_before_overall) * 100).toFixed(0)}% relative drop`;
        return (
          <div className="view">
            <header className="view__header">
              <h2>Attack success rate by category</h2>
              <p className="view__subtitle">
                Run <code>{data.run_id}</code> · {data.n_behaviors} behaviors across{" "}
                {data.categories.length} categories
              </p>
            </header>

            <div className="stat-row">
              <StatTile
                label="ASR before detection"
                value={`${(data.asr_before_overall * 100).toFixed(1)}%`}
                tone="critical"
              />
              <StatTile
                label="ASR after detection"
                value={`${(data.asr_after_overall * 100).toFixed(1)}%`}
                tone="good"
              />
              <StatTile
                label="Absolute reduction"
                value={`${(delta * 100).toFixed(1)} pts`}
                hint={relativeDropLabel}
              />
            </div>

            <div className="panel">
              <AsrBarChart categories={data.categories} />
            </div>

            <div className="table-wrap panel">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>n</th>
                    <th>ASR before</th>
                    <th>ASR after</th>
                    <th>Reduction</th>
                  </tr>
                </thead>
                <tbody>
                  {data.categories.map((c) => (
                    <tr key={c.category}>
                      <td>{c.category}</td>
                      <td>{c.n}</td>
                      <td>{(c.asr_before * 100).toFixed(1)}%</td>
                      <td>{(c.asr_after * 100).toFixed(1)}%</td>
                      <td>{((c.asr_before - c.asr_after) * 100).toFixed(1)} pts</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      }}
    </DataState>
  );
}
