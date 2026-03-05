"use client";
import { useState, useEffect, useRef } from "react";
import useSWR from "swr";
import { TrendingUp, RefreshCw, ExternalLink, ChevronDown, ChevronRight, Palette, Maximize2 } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import {
  getBriefs, getLatestBrief, scanMarket,
  getLatestColorTrends, scanColorTrends,
  type MarketBrief, type ColorSizeTrend,
} from "@/lib/api";

const SCAN_STEPS = [
  "Searching Christie's auction results...",
  "Searching Sotheby's top lots...",
  "Scanning Art Basel highlights...",
  "Checking Pace Gallery exhibitions...",
  "Scanning Artsy market data...",
  "Extracting market signals...",
  "Generating creative brief...",
  "Saving brief...",
];

const COLOR_SCAN_STEPS = [
  "Scanning contemporary art color palettes...",
  "Analysing popular artwork sizes...",
  "Extracting format trends...",
  "Generating color & size summary...",
];

const TREND_BADGE: Record<string, string> = {
  dominant: "bg-studio-accent/20 text-studio-accent",
  rising: "bg-yellow-500/20 text-yellow-400",
  emerging: "bg-studio-text-muted/20 text-studio-text-muted",
};

export default function BriefsPage() {
  const [tab, setTab] = useState<"brief" | "colors">("brief");
  const [scanning, setScanning] = useState(false);
  const [stepIdx, setStepIdx] = useState(0);
  const [colorScanning, setColorScanning] = useState(false);
  const [colorStepIdx, setColorStepIdx] = useState(0);
  const [expanded, setExpanded] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const stepRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const colorPollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const colorStepRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const { data: latest, mutate: mutateLatest } = useSWR("briefs/latest", getLatestBrief);
  const { data: briefs, isLoading, mutate: mutateBriefs } = useSWR("briefs", getBriefs);
  const { data: colorTrends, mutate: mutateColorTrends } = useSWR("briefs/color-trends/latest", getLatestColorTrends);

  useEffect(() => () => {
    [pollRef, stepRef, colorPollRef, colorStepRef].forEach(r => { if (r.current) clearInterval(r.current); });
  }, []);

  const handleScan = async () => {
    setScanning(true);
    setStepIdx(0);
    await scanMarket();
    const prevUpdatedAt = latest?.updated_at ?? latest?.created_at ?? null;

    stepRef.current = setInterval(() => {
      setStepIdx(i => Math.min(i + 1, SCAN_STEPS.length - 1));
    }, 20000);

    pollRef.current = setInterval(async () => {
      const fresh = await getLatestBrief();
      const freshTs = fresh?.updated_at ?? fresh?.created_at ?? null;
      const isNew = fresh?.brief && (fresh.id !== latest?.id || (freshTs && freshTs !== prevUpdatedAt));
      if (isNew) {
        clearInterval(pollRef.current!);
        clearInterval(stepRef.current!);
        setScanning(false);
        mutateLatest();
        mutateBriefs();
      }
    }, 10000);
  };

  const handleColorScan = async () => {
    setColorScanning(true);
    setColorStepIdx(0);
    await scanColorTrends();
    const prevUpdatedAt = colorTrends?.updated_at ?? colorTrends?.created_at ?? null;

    colorStepRef.current = setInterval(() => {
      setColorStepIdx(i => Math.min(i + 1, COLOR_SCAN_STEPS.length - 1));
    }, 25000);

    colorPollRef.current = setInterval(async () => {
      const fresh = await getLatestColorTrends();
      const freshTs = fresh?.updated_at ?? fresh?.created_at ?? null;
      const isNew = fresh?.summary && (fresh.id !== colorTrends?.id || (freshTs && freshTs !== prevUpdatedAt));
      if (isNew) {
        clearInterval(colorPollRef.current!);
        clearInterval(colorStepRef.current!);
        setColorScanning(false);
        mutateColorTrends();
      }
    }, 10000);
  };

  const toggle = (id: string) => setExpanded(e => e === id ? null : id);

  return (
    <div>
      <PageHeader
        title="Trend-to-Brief"
        description="Weekly creative briefs generated from Christie's, Sotheby's, Art Basel, Pace & Artsy"
        actions={
          tab === "brief" ? (
            <button onClick={handleScan} disabled={scanning} className="btn-primary flex items-center gap-2">
              <RefreshCw size={13} className={scanning ? "animate-spin" : ""} />
              {scanning ? "Scanning..." : "Scan & Generate Brief"}
            </button>
          ) : (
            <button onClick={handleColorScan} disabled={colorScanning} className="btn-primary flex items-center gap-2">
              <RefreshCw size={13} className={colorScanning ? "animate-spin" : ""} />
              {colorScanning ? "Scanning..." : "Scan Color & Size Trends"}
            </button>
          )
        }
      />

      {/* Tab bar */}
      <div className="flex gap-1 mb-6 border-b border-studio-border">
        <button
          onClick={() => setTab("brief")}
          className={`px-4 py-2 text-xs font-medium transition-colors border-b-2 -mb-px ${
            tab === "brief"
              ? "border-studio-accent text-studio-accent"
              : "border-transparent text-studio-text-muted hover:text-studio-text"
          }`}
        >
          Market Brief
        </button>
        <button
          onClick={() => setTab("colors")}
          className={`px-4 py-2 text-xs font-medium transition-colors border-b-2 -mb-px ${
            tab === "colors"
              ? "border-studio-accent text-studio-accent"
              : "border-transparent text-studio-text-muted hover:text-studio-text"
          }`}
        >
          Color & Size
        </button>
      </div>

      {/* ── MARKET BRIEF TAB ──────────────────────────────────────────────── */}
      {tab === "brief" && (
        <>
          {scanning && (
            <div className="card mb-6 border-studio-accent/20">
              <div className="flex items-center gap-3">
                <RefreshCw size={13} className="animate-spin text-studio-accent flex-shrink-0" />
                <div>
                  <p className="text-xs text-studio-text">{SCAN_STEPS[stepIdx]}</p>
                  <p className="text-xs text-studio-text-muted mt-0.5">
                    This takes 2–4 minutes — scanning Christie's, Sotheby's, Art Basel, Pace & Artsy
                  </p>
                </div>
              </div>
              <div className="mt-3 flex gap-1">
                {SCAN_STEPS.map((_, i) => (
                  <div key={i} className={`h-0.5 flex-1 rounded-full transition-colors ${i <= stepIdx ? "bg-studio-accent" : "bg-studio-border"}`} />
                ))}
              </div>
            </div>
          )}

          {latest && latest.brief && (
            <div className="card mb-6 border-studio-accent/30">
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="tag-accent">Latest</span>
                    <span className="text-xs text-studio-text-muted">
                      {latest.week_of ? new Date(latest.week_of).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" }) : ""}
                    </span>
                  </div>
                  <h2 className="text-sm font-medium text-studio-text">{latest.title}</h2>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3 mb-4">
                {latest.top_mediums?.length > 0 && (
                  <div className="bg-studio-bg rounded border border-studio-border p-3">
                    <div className="text-xs text-studio-text-muted uppercase tracking-widest mb-2">Trending Mediums</div>
                    <div className="flex flex-wrap gap-1">
                      {(latest.top_mediums as string[]).slice(0, 5).map((m: string) => (
                        <span key={m} className="tag">{m}</span>
                      ))}
                    </div>
                  </div>
                )}
                {latest.top_artists?.length > 0 && (
                  <div className="bg-studio-bg rounded border border-studio-border p-3">
                    <div className="text-xs text-studio-text-muted uppercase tracking-widest mb-2">Market Momentum</div>
                    <div className="flex flex-wrap gap-1">
                      {(latest.top_artists as string[]).slice(0, 5).map((a: string) => (
                        <span key={a} className="tag">{a}</span>
                      ))}
                    </div>
                  </div>
                )}
                {latest.signals?.length > 0 && (
                  <div className="bg-studio-bg rounded border border-studio-border p-3">
                    <div className="text-xs text-studio-text-muted uppercase tracking-widest mb-2">Signal Strength</div>
                    <div className="space-y-1">
                      {["strong", "moderate", "emerging"].map(s => {
                        const count = (latest.signals as any[]).filter((x: any) => x.strength === s).length;
                        return count > 0 ? (
                          <div key={s} className="flex items-center gap-2">
                            <span className={`inline-block w-1.5 h-1.5 rounded-full ${s === "strong" ? "bg-studio-accent" : s === "moderate" ? "bg-yellow-500" : "bg-studio-text-muted"}`} />
                            <span className="text-xs text-studio-text-muted capitalize">{s}: {count}</span>
                          </div>
                        ) : null;
                      })}
                    </div>
                  </div>
                )}
              </div>

              <div className="bg-studio-bg rounded border border-studio-border p-4 text-xs text-studio-text whitespace-pre-wrap leading-relaxed max-h-[60vh] overflow-y-auto font-mono">
                {latest.brief}
              </div>

              {latest.sources?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="text-xs text-studio-text-muted">Sources:</span>
                  {(latest.sources as string[]).slice(0, 6).map((url: string) => (
                    <a key={url} href={url} target="_blank" rel="noopener noreferrer"
                      className="text-xs text-studio-accent hover:underline flex items-center gap-0.5">
                      <ExternalLink size={10} />
                      {new URL(url).hostname.replace("www.", "")}
                    </a>
                  ))}
                </div>
              )}
            </div>
          )}

          {!isLoading && !latest?.brief && (
            <EmptyState
              icon={TrendingUp}
              message="No market briefs yet"
              sub="Click 'Scan & Generate Brief' to scan Christie's, Sotheby's, Art Basel, Pace & Artsy"
            />
          )}

          {(briefs ?? []).length > 1 && (
            <div>
              <h3 className="text-xs uppercase tracking-widest text-studio-text-muted mb-3">Past Briefs</h3>
              <div className="space-y-2">
                {(briefs ?? []).slice(1).map((b: MarketBrief) => (
                  <div key={b.id} className="card hover:border-studio-muted transition-colors">
                    <button onClick={() => toggle(b.id)} className="w-full flex items-center justify-between text-left">
                      <div>
                        <p className="text-sm text-studio-text">{b.title}</p>
                        <p className="text-xs text-studio-text-muted mt-0.5">
                          {b.week_of ? new Date(b.week_of).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" }) : ""}
                          {b.signals?.length ? ` · ${(b.signals as any[]).length} signals` : ""}
                        </p>
                      </div>
                      {expanded === b.id ? <ChevronDown size={13} className="text-studio-text-muted" /> : <ChevronRight size={13} className="text-studio-text-muted" />}
                    </button>
                    {expanded === b.id && b.brief && (
                      <div className="mt-4 bg-studio-bg rounded border border-studio-border p-4 text-xs text-studio-text whitespace-pre-wrap leading-relaxed max-h-96 overflow-y-auto font-mono">
                        {b.brief}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {/* ── COLOR & SIZE TAB ─────────────────────────────────────────────── */}
      {tab === "colors" && (
        <>
          {colorScanning && (
            <div className="card mb-6 border-studio-accent/20">
              <div className="flex items-center gap-3">
                <RefreshCw size={13} className="animate-spin text-studio-accent flex-shrink-0" />
                <div>
                  <p className="text-xs text-studio-text">{COLOR_SCAN_STEPS[colorStepIdx]}</p>
                  <p className="text-xs text-studio-text-muted mt-0.5">
                    Scanning contemporary art — paintings, photography, print, digital (excluding sculpture & furniture)
                  </p>
                </div>
              </div>
              <div className="mt-3 flex gap-1">
                {COLOR_SCAN_STEPS.map((_, i) => (
                  <div key={i} className={`h-0.5 flex-1 rounded-full transition-colors ${i <= colorStepIdx ? "bg-studio-accent" : "bg-studio-border"}`} />
                ))}
              </div>
            </div>
          )}

          {colorTrends && (colorTrends.popular_colors?.length > 0 || colorTrends.popular_sizes?.length > 0) ? (
            <div className="space-y-6">
              {/* Summary */}
              {colorTrends.summary && (
                <div className="card border-studio-accent/20">
                  <p className="text-xs text-studio-text-muted uppercase tracking-widest mb-2">Overview</p>
                  <p className="text-sm text-studio-text leading-relaxed">{colorTrends.summary}</p>
                  <p className="text-xs text-studio-text-muted mt-2">
                    Week of {colorTrends.week_of ? new Date(colorTrends.week_of).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" }) : ""}
                  </p>
                </div>
              )}

              {/* Popular Colors */}
              {colorTrends.popular_colors?.length > 0 && (
                <div>
                  <h3 className="text-xs uppercase tracking-widest text-studio-text-muted mb-3 flex items-center gap-2">
                    <Palette size={12} /> Popular Colors
                  </h3>
                  <div className="grid grid-cols-2 gap-3">
                    {colorTrends.popular_colors.map((c, i) => (
                      <div key={i} className="card flex items-start gap-3">
                        <div
                          className="w-10 h-10 rounded flex-shrink-0 border border-studio-border"
                          style={{ backgroundColor: c.hex }}
                        />
                        <div className="min-w-0">
                          <div className="flex items-center gap-2 mb-0.5">
                            <span className="text-sm text-studio-text font-medium">{c.name}</span>
                            <span className={`text-xs px-1.5 py-0.5 rounded capitalize font-medium ${TREND_BADGE[c.trend] ?? TREND_BADGE.emerging}`}>
                              {c.trend}
                            </span>
                          </div>
                          <p className="text-xs text-studio-text-muted leading-snug">{c.context}</p>
                          <p className="text-xs text-studio-text-muted/50 mt-0.5 font-mono">{c.hex}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Popular Sizes */}
              {colorTrends.popular_sizes?.length > 0 && (
                <div>
                  <h3 className="text-xs uppercase tracking-widest text-studio-text-muted mb-3 flex items-center gap-2">
                    <Maximize2 size={12} /> Popular Sizes
                  </h3>
                  <div className="grid grid-cols-2 gap-3">
                    {colorTrends.popular_sizes.map((s, i) => (
                      <div key={i} className="card">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-studio-text font-medium">{s.label}</span>
                          <span className={`text-xs px-1.5 py-0.5 rounded capitalize font-medium ${TREND_BADGE[s.trend] ?? TREND_BADGE.emerging}`}>
                            {s.trend}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="tag font-mono">{s.dimensions}</span>
                          <span className="tag">{s.medium}</span>
                        </div>
                        <p className="text-xs text-studio-text-muted leading-snug">{s.context}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sources */}
              {colorTrends.sources?.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  <span className="text-xs text-studio-text-muted">Sources:</span>
                  {colorTrends.sources.slice(0, 6).map((url: string) => (
                    <a key={url} href={url} target="_blank" rel="noopener noreferrer"
                      className="text-xs text-studio-accent hover:underline flex items-center gap-0.5">
                      <ExternalLink size={10} />
                      {(() => { try { return new URL(url).hostname.replace("www.", ""); } catch { return url; } })()}
                    </a>
                  ))}
                </div>
              )}
            </div>
          ) : !colorScanning ? (
            <EmptyState
              icon={Palette}
              message="No color & size trends yet"
              sub="Click 'Scan Color & Size Trends' to analyse contemporary art paintings, photography, and prints"
            />
          ) : null}
        </>
      )}
    </div>
  );
}
