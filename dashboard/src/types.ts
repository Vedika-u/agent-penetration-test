// Data contract types — must match the JSON files fetched from public/data/*.json
// exactly. These are shared by src/target_agent (detection eval) and the harness
// (benchmark run) on the producing side; this file is the consuming side's mirror
// of that contract. Keep in sync with the shapes documented in the Phase 5 task.

export interface ConfusionMatrix {
  tp: number;
  fp: number;
  fn: number;
  tn: number;
}

export interface DetectorEval {
  detector: string;
  threshold: number;
  dataset_sources: string[];
  n_samples: number;
  precision: number;
  recall: number;
  f1: number;
  confusion_matrix: ConfusionMatrix;
}

export interface AsrCategory {
  category: string;
  asr_before: number;
  asr_after: number;
  n: number;
}

export interface BenchmarkAsr {
  run_id: string;
  n_behaviors: number;
  categories: AsrCategory[];
  asr_before_overall: number;
  asr_after_overall: number;
}

export interface TranscriptEntry {
  probe: string;
  prompt: string;
  response: string;
  detector_flagged: boolean;
  detector_score: number;
  ground_truth_attack_success: boolean;
}

export type TranscriptsSample = TranscriptEntry[];
