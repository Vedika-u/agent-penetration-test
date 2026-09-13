import { useState } from "react";
import type { AsrCategory } from "../types";

interface AsrBarChartProps {
  categories: AsrCategory[];
}

interface Hover {
  category: string;
  series: "before" | "after";
  value: number;
  n: number;
  x: number;
  y: number;
}

const CHART_HEIGHT = 260;
const BAR_WIDTH = 22;
const GROUP_GAP = 2; // gap between the before/after bars within a group
const GROUP_PADDING = 28; // space between groups

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

export function AsrBarChart({ categories }: AsrBarChartProps) {
  const [hover, setHover] = useState<Hover | null>(null);

  const maxValue = Math.max(0.1, ...categories.flatMap((c) => [c.asr_before, c.asr_after]));
  // Round the axis ceiling up to the next 10% for tidy gridlines.
  const axisMax = Math.min(1, Math.ceil(maxValue * 10) / 10 + 0.05);

  const groupWidth = BAR_WIDTH * 2 + GROUP_GAP;
  const chartWidth = categories.length * (groupWidth + GROUP_PADDING) + GROUP_PADDING;
  const yFor = (v: number) => CHART_HEIGHT - (v / axisMax) * CHART_HEIGHT;

  const gridLines = [0, 0.25, 0.5, 0.75, 1].map((f) => f * axisMax).filter((v) => v <= axisMax);

  return (
    <div className="viz-root asr-chart">
      <div className="asr-chart__legend">
        <span className="legend-item">
          <span className="legend-swatch legend-swatch--before" /> Before detection
        </span>
        <span className="legend-item">
          <span className="legend-swatch legend-swatch--after" /> After detection
        </span>
      </div>

      <div className="asr-chart__scroll">
        <svg
          role="img"
          aria-label="Attack success rate by category, before and after detection"
          width={chartWidth}
          height={CHART_HEIGHT + 56}
          viewBox={`0 0 ${chartWidth} ${CHART_HEIGHT + 56}`}
        >
          {gridLines.map((v) => (
            <g key={v}>
              <line
                x1={0}
                x2={chartWidth}
                y1={yFor(v)}
                y2={yFor(v)}
                className="asr-chart__gridline"
              />
              <text x={0} y={yFor(v) - 4} className="asr-chart__axis-label">
                {pct(v)}
              </text>
            </g>
          ))}
          <line
            x1={0}
            x2={chartWidth}
            y1={CHART_HEIGHT}
            y2={CHART_HEIGHT}
            className="asr-chart__baseline"
          />

          {categories.map((cat, i) => {
            const groupX = GROUP_PADDING + i * (groupWidth + GROUP_PADDING);
            const beforeH = CHART_HEIGHT - yFor(cat.asr_before);
            const afterH = CHART_HEIGHT - yFor(cat.asr_after);
            return (
              <g key={cat.category}>
                <rect
                  x={groupX}
                  y={yFor(cat.asr_before)}
                  width={BAR_WIDTH}
                  height={beforeH}
                  rx={4}
                  className="asr-chart__bar asr-chart__bar--before"
                  onMouseEnter={() =>
                    setHover({
                      category: cat.category,
                      series: "before",
                      value: cat.asr_before,
                      n: cat.n,
                      x: groupX + BAR_WIDTH / 2,
                      y: yFor(cat.asr_before),
                    })
                  }
                  onMouseLeave={() => setHover(null)}
                />
                <rect
                  x={groupX + BAR_WIDTH + GROUP_GAP}
                  y={yFor(cat.asr_after)}
                  width={BAR_WIDTH}
                  height={afterH}
                  rx={4}
                  className="asr-chart__bar asr-chart__bar--after"
                  onMouseEnter={() =>
                    setHover({
                      category: cat.category,
                      series: "after",
                      value: cat.asr_after,
                      n: cat.n,
                      x: groupX + BAR_WIDTH + GROUP_GAP + BAR_WIDTH / 2,
                      y: yFor(cat.asr_after),
                    })
                  }
                  onMouseLeave={() => setHover(null)}
                />
                <text
                  x={groupX + BAR_WIDTH + GROUP_GAP / 2}
                  y={CHART_HEIGHT + 18}
                  className="asr-chart__category-label"
                >
                  {cat.category}
                </text>
                <text
                  x={groupX + BAR_WIDTH + GROUP_GAP / 2}
                  y={CHART_HEIGHT + 34}
                  className="asr-chart__category-n"
                >
                  n={cat.n}
                </text>
              </g>
            );
          })}
        </svg>

        {hover ? (
          <div
            className="asr-chart__tooltip"
            style={{ left: hover.x, top: hover.y }}
          >
            <strong>{hover.category}</strong>
            <div>{hover.series === "before" ? "Before detection" : "After detection"}</div>
            <div>
              ASR {pct(hover.value)} · n={hover.n}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
