"use client";
import { useState } from "react";
import useSWR from "swr";
import { Newspaper, ExternalLink } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getPress, type PressItem } from "@/lib/api";

const CATEGORIES = ["all", "exhibition", "review", "news", "interview"];

export default function PressPage() {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [mode, setMode] = useState<"semantic" | "keyword">("semantic");

  const { data, isLoading } = useSWR(
    ["press", query, mode],
    () => getPress(query || undefined, mode)
  );

  const items = (data ?? []).filter(
    (p: PressItem) => filter === "all" || p.category === filter
  );

  return (
    <div>
      <PageHeader
        title="Press Monitor"
        description="Exhibitions, reviews and digital art news"
      />

      <div className="flex gap-3 mb-4">
        <div className="flex-1">
          <SearchBar onSearch={setQuery} placeholder="Search press..." loading={isLoading} />
        </div>
        <button
          onClick={() => setMode(mode === "semantic" ? "keyword" : "semantic")}
          className="btn-ghost text-xs"
        >
          {mode === "semantic" ? "Semantic" : "Keyword"}
        </button>
      </div>

      <div className="flex gap-1 mb-4">
        {CATEGORIES.map((c) => (
          <button
            key={c}
            onClick={() => setFilter(c)}
            className={`btn text-xs ${filter === c ? "btn-primary" : "btn-ghost"}`}
          >
            {c}
          </button>
        ))}
      </div>

      {isLoading && <p className="text-studio-text-muted text-xs">Loading...</p>}

      {!isLoading && items.length === 0 && (
        <EmptyState icon={Newspaper} message="No press items yet" sub="The press monitor runs daily at 09:00 UTC" />
      )}

      <div className="space-y-3">
        {items.map((p: PressItem) => (
          <div key={p.id} className="card hover:border-studio-muted transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="tag">{p.category}</span>
                  {p.source && <span className="text-xs text-studio-accent">{p.source}</span>}
                </div>
                <h3 className="text-sm font-medium text-studio-text mb-1">{p.title}</h3>
                <p className="text-xs text-studio-text-muted line-clamp-2">{p.summary}</p>
                {p.mentioned_artists?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {p.mentioned_artists.slice(0, 4).map((a) => (
                      <span key={a} className="tag">{a}</span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex-shrink-0 text-right space-y-2">
                {p.published_at && (
                  <div className="text-xs text-studio-text-muted">
                    {formatDistanceToNow(new Date(p.published_at), { addSuffix: true })}
                  </div>
                )}
                {p.url && (
                  <a href={p.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-studio-accent hover:underline">
                    <ExternalLink size={11} /> Read
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
