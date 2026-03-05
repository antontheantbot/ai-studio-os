"use client";
import { useState } from "react";
import useSWR from "swr";
import { PenLine, RefreshCw, Mail, Twitter, Instagram, Linkedin, Globe, Plus, X, Check } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getJournalists, scanJournalists, addJournalistsFromText, type Journalist } from "@/lib/api";

export default function JournalistsPage() {
  const [query, setQuery] = useState("");
  const [scanning, setScanning] = useState(false);
  const [showPaste, setShowPaste] = useState(false);
  const [pasteText, setPasteText] = useState("");
  const [adding, setAdding] = useState(false);
  const [addResult, setAddResult] = useState<{ added: number; skipped: number; message: string } | null>(null);

  const { data, isLoading, mutate } = useSWR(
    ["journalists", query],
    () => getJournalists(query || undefined)
  );

  const handleScan = async () => {
    setScanning(true);
    await scanJournalists();
    setTimeout(() => { setScanning(false); mutate(); }, 120000);
  };

  const handleAdd = async () => {
    if (!pasteText.trim()) return;
    setAdding(true);
    setAddResult(null);
    try {
      const result = await addJournalistsFromText(pasteText);
      setAddResult(result);
      if (result.added > 0) {
        mutate();
        setPasteText("");
      }
    } finally {
      setAdding(false);
    }
  };

  const items: Journalist[] = data ?? [];

  return (
    <div>
      <PageHeader
        title="Journalists"
        description="Writers covering art, culture, photography and architecture — auto-updated weekly"
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => { setShowPaste(!showPaste); setAddResult(null); }}
              className="btn-ghost flex items-center gap-2"
            >
              <Plus size={13} />
              Add Entry
            </button>
            <button onClick={handleScan} disabled={scanning} className="btn-primary flex items-center gap-2">
              <RefreshCw size={13} className={scanning ? "animate-spin" : ""} />
              {scanning ? "Scanning..." : "Scan Web"}
            </button>
          </div>
        }
      />

      {/* Paste panel */}
      {showPaste && (
        <div className="card mb-6 border-studio-accent/20">
          <div className="flex items-center justify-between mb-3">
            <p className="text-xs font-medium text-studio-text">Paste journalist info</p>
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
            placeholder={"e.g.\nJessica Morgan — frieze.com — @jessicamorgan\nWrites about contemporary art and new media\njessica@frieze.com\n\nOr paste a full bio, LinkedIn excerpt, or any list of names..."}
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
        <SearchBar onSearch={setQuery} placeholder="Search journalists by name, beat or publication..." loading={isLoading} />
      </div>

      {isLoading && <p className="text-studio-text-muted text-xs">Loading...</p>}

      {!isLoading && items.length === 0 && (
        <EmptyState
          icon={PenLine}
          message="No journalists yet"
          sub="Click 'Scan Web' to find journalists, or use 'Add Entry' to paste in names manually"
        />
      )}

      <div className="grid grid-cols-1 gap-3">
        {items.map((j) => (
          <div key={j.id} className="card hover:border-studio-muted transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-medium text-studio-text">{j.name}</h3>
                  {j.location && (
                    <span className="text-xs text-studio-text-muted">
                      {j.location}{j.country ? `, ${j.country}` : ""}
                    </span>
                  )}
                </div>

                {j.bio && (
                  <p className="text-xs text-studio-text-muted mt-0.5 line-clamp-2 leading-relaxed">{j.bio}</p>
                )}

                {j.publications?.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1 mt-2">
                    <span className="text-xs text-studio-text-muted mr-1">Writes for:</span>
                    {j.publications.map((p) => (
                      <span key={p} className="tag-accent">{p}</span>
                    ))}
                  </div>
                )}

                {j.beats?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {j.beats.map((b) => (
                      <span key={b} className="tag">{b}</span>
                    ))}
                  </div>
                )}

                {j.notes && (
                  <p className="text-xs text-studio-text-muted/70 mt-1.5 italic">{j.notes}</p>
                )}
              </div>

              <div className="flex-shrink-0 flex flex-col items-end gap-2">
                {j.email ? (
                  <a href={`mailto:${j.email}`}
                    className="flex items-center gap-1.5 text-xs text-studio-accent hover:underline">
                    <Mail size={11} />
                    {j.email}
                  </a>
                ) : (
                  <span className="text-xs text-studio-text-muted/50 italic">No email found</span>
                )}

                <div className="flex items-center gap-2">
                  {j.social_links?.twitter && (
                    <a href={j.social_links.twitter} target="_blank" rel="noopener noreferrer"
                      className="text-studio-text-muted hover:text-studio-accent transition-colors" title="Twitter / X">
                      <Twitter size={13} />
                    </a>
                  )}
                  {j.social_links?.instagram && (
                    <a href={j.social_links.instagram} target="_blank" rel="noopener noreferrer"
                      className="text-studio-text-muted hover:text-studio-accent transition-colors" title="Instagram">
                      <Instagram size={13} />
                    </a>
                  )}
                  {j.social_links?.linkedin && (
                    <a href={j.social_links.linkedin} target="_blank" rel="noopener noreferrer"
                      className="text-studio-text-muted hover:text-studio-accent transition-colors" title="LinkedIn">
                      <Linkedin size={13} />
                    </a>
                  )}
                  {j.social_links?.website && (
                    <a href={j.social_links.website} target="_blank" rel="noopener noreferrer"
                      className="text-studio-text-muted hover:text-studio-accent transition-colors" title="Website">
                      <Globe size={13} />
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
