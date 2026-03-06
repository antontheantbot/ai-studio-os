"use client";
import { useState } from "react";
import useSWR from "swr";
import { Target, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import { getDailyAction, generateDailyAction, getDailyHistory, type DailyAction } from "@/lib/api";

function ActionCard({ action, featured = false }: { action: DailyAction; featured?: boolean }) {
  return (
    <div className={`card ${featured ? "border-studio-accent/40 bg-[#1a1a00]/40" : ""}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Target size={13} className={featured ? "text-studio-accent" : "text-studio-text-muted"} />
          <span className={`text-xs font-medium ${featured ? "text-studio-accent" : "text-studio-text-muted"}`}>
            {featured ? "TODAY'S ACTION" : action.date}
          </span>
        </div>
        {featured && (
          <span className="text-xs text-studio-text-muted">{action.date}</span>
        )}
      </div>

      {action.goal_name && (
        <div className="mb-3">
          <span className="tag-accent text-xs">{action.goal_name}</span>
        </div>
      )}

      <pre className="text-xs text-studio-text leading-relaxed whitespace-pre-wrap font-sans">
        {action.content}
      </pre>
    </div>
  );
}

export default function DailyPage() {
  const [generating, setGenerating] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const { data: today, isLoading, mutate } = useSWR("daily-today", getDailyAction);
  const { data: history, mutate: mutateHistory } = useSWR(
    showHistory ? "daily-history" : null,
    getDailyHistory
  );

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      await generateDailyAction();
      await mutate();
      if (showHistory) await mutateHistory();
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Daily Action"
        description="One concrete action per day to move toward your goals — rotates across all 8 goals"
        actions={
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw size={13} className={generating ? "animate-spin" : ""} />
            {generating ? "Generating..." : "Generate Today's Action"}
          </button>
        }
      />

      {isLoading && (
        <p className="text-studio-text-muted text-xs">Loading today's action...</p>
      )}

      {!isLoading && !today && (
        <EmptyState
          icon={Target}
          message="No action for today yet"
          sub="Click 'Generate Today's Action' to get started"
        />
      )}

      {today && (
        <div className="mb-6">
          <ActionCard action={today} featured />
        </div>
      )}

      {/* History toggle */}
      <button
        onClick={() => setShowHistory(!showHistory)}
        className="flex items-center gap-2 text-xs text-studio-text-muted hover:text-studio-text transition-colors mb-4"
      >
        {showHistory ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
        {showHistory ? "Hide" : "Show"} past actions
      </button>

      {showHistory && (
        <>
          {!history && <p className="text-studio-text-muted text-xs">Loading...</p>}
          {history && (() => {
            const past = history.filter((a) => !today || a.id !== today.id);
            return past.length > 0
              ? <div className="grid grid-cols-1 gap-3">{past.map((a) => <ActionCard key={a.id} action={a} />)}</div>
              : <p className="text-studio-text-muted text-xs">No past actions yet — they'll appear here as you generate more over the coming days.</p>;
          })()}
        </>
      )}
    </div>
  );
}
