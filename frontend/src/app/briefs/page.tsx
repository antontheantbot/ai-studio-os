"use client";
import { useState, useEffect, useRef } from "react";
import useSWR from "swr";
import { TrendingUp, RefreshCw, ExternalLink, ChevronDown, ChevronRight } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import { getBriefs, getLatestBrief, scanMarket, type MarketBrief } from "@/lib/api";

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

export default function BriefsPage() {
  const [scanning, setScanning] = useState(false);
  const [stepIdx, setStepIdx] = useState(0);
  const [expanded, setExpanded] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const stepRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const { data: latest, mutate: mutateLatest } = useSWR("briefs/latest", getLatestBrief);
  const { data: briefs, isLoading, mutate: mutateBriefs } = useSWR("briefs", getBriefs);

  useEffect(() => () => {
    if (pollRef.current) clearInterval(pollRef.current);
    if (stepRef.current) clearInterval(stepRef.current);
  }, []);

  const handleScan = async () => {
    setScanning(true);
    setStepIdx(0);
    const prevId = latest?.id;

    await scanMarket();

    // Cycle through status messages every 20s
    stepRef.current = setInterval(() => {
      setStepIdx(i => Math.min(i + 1, SCAN_STEPS.length - 1));
    }, 20000);

    // Poll every 10s until a new brief appears
    pollRef.current = setInterval(async () => {
      const fresh = await getLatestBrief();
      if (fresh?.id && fresh.id !== prevId && fresh.brief) {
        clearInterval(pollRef.current!);
        clearInterval(stepRef.current!);
        setScanning(false);
        mutateLatest();
        mutateBriefs();
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
          <button onClick={handleScan} disabled={scanning} className="btn-primary flex items-center gap-2">
            <RefreshCw size={13} className={scanning ? "animate-spin" : ""} />
            {scanning ? "Scanning..." : "Scan & Generate Brief"}
          </button>
        }
      />

      {/* Scanning progress */}
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

      {/* Latest brief — hero display */}
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

          {/* Signals summary row */}
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

          {/* Brief text */}
          <div className="bg-studio-bg rounded border border-studio-border p-4 text-xs text-studio-text whitespace-pre-wrap leading-relaxed max-h-[60vh] overflow-y-auto font-mono">
            {latest.brief}
          </div>

          {/* Sources */}
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

      {/* Empty state */}
      {!isLoading && !latest?.brief && (
        <EmptyState
          icon={TrendingUp}
          message="No market briefs yet"
          sub="Click 'Scan & Generate Brief' to scan Christie's, Sotheby's, Art Basel, Pace & Artsy"
        />
      )}

      {/* Past briefs */}
      {(briefs ?? []).length > 1 && (
        <div>
          <h3 className="text-xs uppercase tracking-widest text-studio-text-muted mb-3">Past Briefs</h3>
          <div className="space-y-2">
            {(briefs ?? []).slice(1).map((b: MarketBrief) => (
              <div key={b.id} className="card hover:border-studio-muted transition-colors">
                <button
                  onClick={() => toggle(b.id)}
                  className="w-full flex items-center justify-between text-left"
                >
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
    </div>
  );
}
