import { useState } from "react";
import { AsrView } from "./views/AsrView";
import { DetectorView } from "./views/DetectorView";
import { TranscriptsPage } from "./views/TranscriptsPage";

type Tab = "asr" | "detector" | "transcripts";

const TABS: { id: Tab; label: string }[] = [
  { id: "asr", label: "ASR by category" },
  { id: "detector", label: "Detector confusion matrix" },
  { id: "transcripts", label: "Annotated transcripts" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("asr");

  return (
    <div className="app">
      <header className="app__header">
        <div className="app__title">
          <h1>agent-red-team</h1>
          <p>Red-teaming results: attack success rate, detector accuracy, and transcripts</p>
        </div>
        <nav className="app__nav" aria-label="Dashboard sections">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              className={`app__nav-tab ${tab === t.id ? "app__nav-tab--active" : ""}`}
              onClick={() => setTab(t.id)}
              aria-current={tab === t.id ? "page" : undefined}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="app__main">
        {tab === "asr" ? <AsrView /> : null}
        {tab === "detector" ? <DetectorView /> : null}
        {tab === "transcripts" ? <TranscriptsPage /> : null}
      </main>
    </div>
  );
}
