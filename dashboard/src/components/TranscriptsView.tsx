import { useMemo, useState } from "react";
import type { TranscriptEntry } from "../types";

interface TranscriptsViewProps {
  transcripts: TranscriptEntry[];
}

type FlagFilter = "all" | "flagged" | "not-flagged";
type OutcomeFilter = "all" | "succeeded" | "not-succeeded";

type RowTone = "critical" | "warning" | "neutral";

interface RowStatus {
  label: string;
  tone: RowTone;
  isMismatch: boolean;
}

function rowStatus(t: TranscriptEntry): RowStatus {
  if (t.detector_flagged && t.ground_truth_attack_success) {
    return {
      label: "Mismatch — flagged, but the attack still succeeded",
      tone: "critical",
      isMismatch: true,
    };
  }
  if (t.detector_flagged && !t.ground_truth_attack_success) {
    return {
      label:
        "Flagged, attack unsuccessful — worth a look: false alarm on benign input, or a real attack that got blocked?",
      tone: "warning",
      isMismatch: true,
    };
  }
  if (!t.detector_flagged && t.ground_truth_attack_success) {
    return {
      label: "Missed — not flagged, but the attack succeeded",
      tone: "critical",
      isMismatch: true,
    };
  }
  return { label: "Not flagged, attack did not succeed", tone: "neutral", isMismatch: false };
}

function truncate(s: string, max: number): string {
  return s.length > max ? `${s.slice(0, max - 1)}…` : s;
}

export function TranscriptsView({ transcripts }: TranscriptsViewProps) {
  const [query, setQuery] = useState("");
  const [flagFilter, setFlagFilter] = useState<FlagFilter>("all");
  const [outcomeFilter, setOutcomeFilter] = useState<OutcomeFilter>("all");
  const [mismatchOnly, setMismatchOnly] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return transcripts
      .map((t, index) => ({ t, index, status: rowStatus(t) }))
      .filter(({ t, status }) => {
        if (q) {
          const haystack = `${t.probe} ${t.prompt} ${t.response}`.toLowerCase();
          if (!haystack.includes(q)) return false;
        }
        if (flagFilter === "flagged" && !t.detector_flagged) return false;
        if (flagFilter === "not-flagged" && t.detector_flagged) return false;
        if (outcomeFilter === "succeeded" && !t.ground_truth_attack_success) return false;
        if (outcomeFilter === "not-succeeded" && t.ground_truth_attack_success) return false;
        if (mismatchOnly && !status.isMismatch) return false;
        return true;
      });
  }, [transcripts, query, flagFilter, outcomeFilter, mismatchOnly]);

  return (
    <div className="transcripts">
      <div className="transcripts__filters">
        <input
          type="search"
          placeholder="Search prompt, response, or probe…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="transcripts__search"
          aria-label="Search transcripts"
        />
        <select
          value={flagFilter}
          onChange={(e) => setFlagFilter(e.target.value as FlagFilter)}
          aria-label="Filter by detector flag"
        >
          <option value="all">Detector: all</option>
          <option value="flagged">Detector: flagged</option>
          <option value="not-flagged">Detector: not flagged</option>
        </select>
        <select
          value={outcomeFilter}
          onChange={(e) => setOutcomeFilter(e.target.value as OutcomeFilter)}
          aria-label="Filter by attack outcome"
        >
          <option value="all">Outcome: all</option>
          <option value="succeeded">Outcome: attack succeeded</option>
          <option value="not-succeeded">Outcome: attack did not succeed</option>
        </select>
        <label className="transcripts__mismatch-toggle">
          <input
            type="checkbox"
            checked={mismatchOnly}
            onChange={(e) => setMismatchOnly(e.target.checked)}
          />
          Mismatches only
        </label>
      </div>

      <div className="transcripts__count">
        {filtered.length} of {transcripts.length} transcripts
      </div>

      <ul className="transcripts__list">
        {filtered.map(({ t, index, status }) => {
          const isOpen = expanded === index;
          return (
            <li
              key={index}
              className={`transcript-row transcript-row--${status.tone}`}
            >
              <button
                type="button"
                className="transcript-row__summary"
                onClick={() => setExpanded(isOpen ? null : index)}
                aria-expanded={isOpen}
              >
                <div className="transcript-row__meta">
                  <span className="transcript-row__probe">{t.probe}</span>
                  <span className={`badge badge--${t.detector_flagged ? "flagged" : "clear"}`}>
                    {t.detector_flagged ? "Flagged" : "Not flagged"} ·{" "}
                    {t.detector_score.toFixed(2)}
                  </span>
                  <span
                    className={`badge badge--${
                      t.ground_truth_attack_success ? "succeeded" : "blocked"
                    }`}
                  >
                    {t.ground_truth_attack_success ? "Attack succeeded" : "Attack did not succeed"}
                  </span>
                </div>
                <div className="transcript-row__prompt">
                  {isOpen ? t.prompt : truncate(t.prompt, 140)}
                </div>
                {status.isMismatch ? (
                  <div className={`transcript-row__status transcript-row__status--${status.tone}`}>
                    {status.label}
                  </div>
                ) : null}
              </button>
              {isOpen ? (
                <div className="transcript-row__body">
                  <div className="transcript-row__field">
                    <div className="transcript-row__field-label">Prompt</div>
                    <pre className="transcript-row__text">{t.prompt}</pre>
                  </div>
                  <div className="transcript-row__field">
                    <div className="transcript-row__field-label">Response</div>
                    <pre className="transcript-row__text">{t.response}</pre>
                  </div>
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>

      {filtered.length === 0 ? (
        <div className="panel panel--muted">No transcripts match the current filters.</div>
      ) : null}
    </div>
  );
}
