"use client";
import { useState } from "react";
import useSWR from "swr";
import { Landmark, Plus, X, ExternalLink, RefreshCw, Check } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getInstitutions, addInstitutionsFromText, type Institution } from "@/lib/api";

export default function InstitutionsPage() {
  const [query, setQuery] = useState("");
  const [digitalOnly, setDigitalOnly] = useState(false);
  const [showPaste, setShowPaste] = useState(false);
  const [pasteText, setPasteText] = useState("");
  const [adding, setAdding] = useState(false);
  const [addResult, setAddResult] = useState<{ added: number; skipped: number; message: string } | null>(null);

  const { data, isLoading, mutate } = useSWR(
    ["institutions", query, digitalOnly],
    () => getInstitutions(query || undefined, digitalOnly || undefined)
  );

  const handleAdd = async () => {
    if (!pasteText.trim()) return;
    setAdding(true);
    setAddResult(null);
    try {
      const result = await addInstitutionsFromText(pasteText);
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
        title="Institutions"
        description="Museums, galleries, kunsthalles and art foundations"
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
            <p className="text-xs font-medium text-studio-text">Paste institution info</p>
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
            placeholder={"e.g.\nHauser & Wirth — hauser-wirth.com — London, New York, Los Angeles\nGallery focused on contemporary and modern art\n\nOr paste a full description, website text, or any list of names..."}
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


      <div className="flex gap-3 mb-4">
        <div className="flex-1">
          <SearchBar onSearch={setQuery} placeholder="Search by name, type, focus area..." loading={isLoading} />
        </div>
        <button
          onClick={() => setDigitalOnly(!digitalOnly)}
          className={`btn text-xs ${digitalOnly ? "btn-primary" : "btn-ghost"}`}
        >
          Digital art only
        </button>
      </div>

      {isLoading && <p className="text-studio-text-muted text-xs">Loading...</p>}

      {!isLoading && (!data || data.length === 0) && (
        <EmptyState icon={Landmark} message="No institutions yet" sub="Add institutions manually or via the API" />
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {(data ?? []).map((inst: Institution) => (
          <div key={inst.id} className="card hover:border-studio-muted transition-colors">
            <div className="flex items-start justify-between gap-2 mb-2">
              <div>
                <h3 className="text-sm font-medium text-studio-text">{inst.name}</h3>
                {(inst.city || inst.country) && (
                  <p className="text-xs text-studio-text-muted mt-0.5">
                    📍 {[inst.city, inst.country].filter(Boolean).join(", ")}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                {inst.digital_art_program && <span className="tag-accent">Digital</span>}
                {inst.website && (
                  <a href={inst.website} target="_blank" rel="noopener noreferrer"
                    className="text-studio-text-muted hover:text-studio-accent">
                    <ExternalLink size={13} />
                  </a>
                )}
              </div>
            </div>

            <div className="flex flex-wrap gap-1 mb-2">
              {inst.type && <span className="tag">{inst.type}</span>}
              {inst.focus_areas?.slice(0, 4).map((f) => (
                <span key={f} className="tag">{f}</span>
              ))}
            </div>

            {inst.annual_budget && (
              <p className="text-xs text-studio-text-muted">Budget: {inst.annual_budget}</p>
            )}

            {inst.notes && (
              <p className="text-xs text-studio-text-muted mt-1 line-clamp-2 border-t border-studio-border pt-2">{inst.notes}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
