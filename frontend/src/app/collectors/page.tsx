"use client";
import { useState } from "react";
import useSWR from "swr";
import { Users, Plus, X, RefreshCw, Check } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getCollectors, addCollectorsFromText, type Collector } from "@/lib/api";

export default function CollectorsPage() {
  const [query, setQuery] = useState("");
  const [showPaste, setShowPaste] = useState(false);
  const [pasteText, setPasteText] = useState("");
  const [adding, setAdding] = useState(false);
  const [addResult, setAddResult] = useState<{ added: number; skipped: number; message: string } | null>(null);

  const { data, isLoading, mutate } = useSWR(
    ["collectors", query],
    () => getCollectors(query || undefined)
  );

  const handleAdd = async () => {
    if (!pasteText.trim()) return;
    setAdding(true);
    setAddResult(null);
    try {
      const result = await addCollectorsFromText(pasteText);
      setAddResult(result);
      if (result.added > 0) {
        mutate();
        setPasteText("");
      }
    } finally {
      setAdding(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Collector Intelligence"
        description="Database of art collectors and patrons"
        actions={
          <button
            onClick={() => { setShowPaste(!showPaste); setAddResult(null); }}
            className="btn-primary flex items-center gap-2"
          >
            <Plus size={13} />
            Add Entry
          </button>
        }
      />

      {/* Paste panel */}
      {showPaste && (
        <div className="card mb-6 border-studio-accent/20">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-medium text-studio-text">Paste collector info</p>
            <button onClick={() => { setShowPaste(false); setAddResult(null); }}
              className="text-studio-text-muted hover:text-studio-text">
              <X size={13} />
            </button>
          </div>
          <p className="text-xs text-studio-text-muted mb-3">
            Paste anything — names, bios, emails, LinkedIn profiles, lists. Claude will extract and add them automatically.
          </p>
          <textarea
            value={pasteText}
            onChange={e => setPasteText(e.target.value)}
            placeholder={"e.g.\nFrançois Pinault — collects contemporary art, founder of Palazzo Grassi\nBased in Paris\n\nOr paste a full bio, LinkedIn excerpt, or any list of names..."}
            className="w-full h-36 bg-studio-bg border border-studio-border rounded text-xs text-studio-text p-3 resize-none focus:outline-none focus:border-studio-accent placeholder:text-studio-text-muted/40"
          />
          <div className="flex items-center justify-between mt-3">
            {addResult ? (
              <div className="flex items-center gap-2 text-xs">
                <Check size={12} className="text-studio-accent" />
                <span className="text-studio-text">{addResult.message}</span>
              </div>
            ) : <div />}
            <button
              onClick={handleAdd}
              disabled={adding || !pasteText.trim()}
              className="btn-primary flex items-center gap-2"
            >
              {adding ? <RefreshCw size={12} className="animate-spin" /> : <Plus size={12} />}
              {adding ? "Processing..." : "Add to Database"}
            </button>
          </div>
        </div>
      )}

      <div className="mb-4">
        <SearchBar onSearch={setQuery} placeholder="Search by name, interests, location..." loading={isLoading} />
      </div>

      {isLoading && <p className="text-studio-text-muted text-xs">Loading...</p>}

      {!isLoading && (!data || data.length === 0) && (
        <EmptyState icon={Users} message="No collectors yet" sub="Add collectors via the API or Telegram bot" />
      )}

      <div className="space-y-3">
        {(data ?? []).map((c: Collector) => (
          <div key={c.id} className="card hover:border-studio-muted transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h3 className="text-sm font-medium text-studio-text mb-1">{c.name}</h3>
                <p className="text-xs text-studio-text-muted line-clamp-2 mb-2">{c.bio}</p>
                <div className="flex gap-3 text-xs text-studio-text-muted mb-2">
                  {c.location && <span>📍 {c.location}</span>}
                </div>
                <div className="flex flex-wrap gap-1">
                  {c.interests?.slice(0, 4).map((i) => (
                    <span key={i} className="tag">{i}</span>
                  ))}
                  {c.institutions?.slice(0, 2).map((i) => (
                    <span key={i} className="tag-accent">{i}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
