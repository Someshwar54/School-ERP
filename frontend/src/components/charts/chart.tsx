"use client";

import { useEffect, useRef, useState } from "react";
import type { Config, Data, Layout } from "plotly.js";
import { school } from "@/config/school";

/** Plotly is ~1 MB, so it is loaded lazily and only on pages that draw charts. */
export function Chart({ data, layout, height = 280, label }: { data: Data[]; layout?: Partial<Layout>; height?: number; label: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const el = ref.current;
    import("plotly.js-dist-min")
      .then((mod) => {
        const Plotly = (mod as unknown as { default: typeof import("plotly.js") }).default ?? mod;
        if (cancelled || !el) return;
        const config: Partial<Config> = { displayModeBar: false, responsive: true };
        void Plotly.react(
          el,
          data,
          {
            height,
            margin: { l: 48, r: 16, t: 16, b: 48 },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            font: { family: "Inter, system-ui, sans-serif", size: 12, color: "#1c2430" },
            showlegend: false,
            bargap: 0.35,
            hovermode: "closest",
            ...layout,
            // Axis overrides are merged with (not substituted for) the defaults so labels never clip.
            xaxis: { gridcolor: "#eef0f3", automargin: true, nticks: 12, ...layout?.xaxis },
            yaxis: { gridcolor: "#eef0f3", automargin: true, ...layout?.yaxis },
          },
          config,
        );
      })
      .catch(() => setFailed(true));
    return () => {
      cancelled = true;
    };
  }, [data, layout, height]);

  if (failed) return <p className="text-sm text-muted">Chart could not be loaded.</p>;
  return <div ref={ref} role="img" aria-label={label} style={{ minHeight: height }} />;
}

/** Validated per-school series colours (see config theme.chart). Single-series charts use the first. */
export const SERIES = school.theme.chart;

/** Bar trace with the house mark spec: thin bars, rounded data-ends, 2px gaps, hover on. */
export function barTrace(x: (string | number)[], y: (string | number | null)[], name: string, opts: Partial<Data> = {}): Data {
  return {
    type: "bar",
    x,
    y,
    name,
    marker: { color: SERIES[0], cornerradius: 4 },
    hovertemplate: `%{x}<br>${name}: %{y}<extra></extra>`,
    ...opts,
  } as Data;
}

export function lineTrace(x: (string | number)[], y: (number | null)[], name: string, suffix = ""): Data {
  return {
    type: "scatter",
    mode: "lines+markers",
    x,
    y,
    name,
    connectgaps: false,
    line: { color: SERIES[0], width: 2 },
    marker: { color: SERIES[0], size: 8, line: { color: "#ffffff", width: 2 } },
    hovertemplate: `%{x}<br>${name}: %{y}${suffix}<extra></extra>`,
  } as Data;
}

/** Chart plus an always-available table view of the same numbers. */
export function ChartPanel({
  label,
  data,
  layout,
  height,
  headers,
  rows,
}: {
  label: string;
  data: Data[];
  layout?: Partial<Layout>;
  height?: number;
  headers: string[];
  rows: (string | number | null)[][];
}) {
  return (
    <div>
      <Chart label={label} data={data} layout={layout} height={height} />
      <details className="mt-2 text-sm">
        <summary className="cursor-pointer text-muted hover:text-ink">View as table</summary>
        <div className="mt-2 max-h-64 overflow-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-line text-muted">
                {headers.map((h) => (
                  <th key={h} scope="col" className="py-1 pr-3 font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-line/60">
                  {r.map((c, j) => (
                    <td key={j} className="py-1 pr-3">
                      {c ?? "—"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}
