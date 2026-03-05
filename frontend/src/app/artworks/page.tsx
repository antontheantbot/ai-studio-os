"use client";
import { useState } from "react";
import useSWR from "swr";
import { Frame, Plus, X, Image as ImageIcon } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getArtworks, getArtists, createArtwork, type Artwork, type Artist } from "@/lib/api";

const EMPTY = {
  title: "",
  artist_id: null as string | null,
  year: null as number | null,
  medium: null as string | null,
  dimensions: null as string | null,
  description: null as string | null,
  image_urls: [] as string[],
  collection: null as string | null,
  exhibition_history: [] as string[],
};

export default function ArtworksPage() {
  const [query, setQuery] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  const { data, isLoading, mutate } = useSWR(
    ["artworks", query],
    () => getArtworks(query || undefined)
  );

  const { data: artists } = useSWR("artists-list", () => getArtists());

  const set = (k: keyof typeof EMPTY) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      const val = e.target.value;
      setForm((f) => ({ ...f, [k]: val || null }));
    };

  const handleSave = async () => {
    if (!form.title) return;
    setSaving(true);
    await createArtwork({
      ...form,
      year: form.year ? Number(form.year) : null,
    });
    setForm(EMPTY);
    setShowAdd(false);
    setSaving(false);
    mutate();
  };

  const artistMap = Object.fromEntries((artists ?? []).map((a: Artist) => [a.id, a.name]));

  return (
    <div>
      <PageHeader
        title="Artworks"
        description="Artwork catalogue and exhibition history"
        actions={
          <button onClick={() => setShowAdd(!showAdd)} className="btn-primary flex items-center gap-2">
            {showAdd ? <X size={13} /> : <Plus size={13} />}
            {showAdd ? "Cancel" : "Add Artwork"}
          </button>
        }
      />

      {showAdd && (
        <div className="card mb-4">
          <h2 className="text-xs font-medium uppercase tracking-widest text-studio-text-muted mb-3">New Artwork</h2>
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="text-xs text-studio-text-muted mb-1 block">Title *</label>
              <input value={form.title} onChange={set("title")} placeholder="Artwork title" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Artist</label>
              <select
                value={form.artist_id ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, artist_id: e.target.value || null }))}
                className="bg-studio-surface border border-studio-border rounded px-3 py-2 text-studio-text w-full outline-none focus:border-studio-accent"
              >
                <option value="">— select artist —</option>
                {(artists ?? []).map((a: Artist) => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Year</label>
              <input
                type="number"
                value={form.year ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, year: e.target.value ? Number(e.target.value) : null }))}
                placeholder="2024"
              />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Medium</label>
              <input value={form.medium ?? ""} onChange={set("medium")} placeholder="Video installation, 4K" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Dimensions</label>
              <input value={form.dimensions ?? ""} onChange={set("dimensions")} placeholder="Variable / 3 × 2 m" />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-studio-text-muted mb-1 block">Description</label>
              <textarea value={form.description ?? ""} onChange={set("description")} placeholder="Work description..." rows={3} className="resize-none" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Collection</label>
              <input value={form.collection ?? ""} onChange={set("collection")} placeholder="Private collection / MoMA" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Exhibition history (comma-separated)</label>
              <input
                value={form.exhibition_history.join(", ")}
                onChange={(e) => setForm((f) => ({ ...f, exhibition_history: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) }))}
                placeholder="Ars Electronica 2023, Venice Biennale 2024"
              />
            </div>
          </div>
          <button
            onClick={handleSave}
            disabled={saving || !form.title}
            className="btn-primary w-full mt-3"
          >
            {saving ? "Saving & Embedding..." : "Save Artwork"}
          </button>
        </div>
      )}

      <div className="mb-4">
        <SearchBar onSearch={setQuery} placeholder="Search by title, medium, description..." loading={isLoading} />
      </div>

      {isLoading && <p className="text-studio-text-muted text-xs">Loading...</p>}

      {!isLoading && (!data || data.length === 0) && (
        <EmptyState icon={Frame} message="No artworks yet" sub="Add artworks manually or via the API" />
      )}

      <div className="space-y-3">
        {(data ?? []).map((w: Artwork) => (
          <div key={w.id} className="card hover:border-studio-muted transition-colors">
            <div className="flex items-start gap-4">
              {/* Thumbnail placeholder */}
              {w.image_urls?.length > 0 ? (
                <img
                  src={w.image_urls[0]}
                  alt={w.title}
                  className="w-16 h-16 object-cover rounded flex-shrink-0 border border-studio-border"
                />
              ) : (
                <div className="w-16 h-16 rounded flex-shrink-0 border border-studio-border bg-studio-bg flex items-center justify-center">
                  <ImageIcon size={18} strokeWidth={1} className="text-studio-border" />
                </div>
              )}

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2 mb-1">
                  <h3 className="text-sm font-medium text-studio-text">{w.title}</h3>
                  {w.year && <span className="tag flex-shrink-0">{w.year}</span>}
                </div>

                {w.artist_id && artistMap[w.artist_id] && (
                  <p className="text-xs text-studio-accent mb-1">{artistMap[w.artist_id]}</p>
                )}

                <div className="flex flex-wrap gap-3 text-xs text-studio-text-muted mb-2">
                  {w.medium && <span>{w.medium}</span>}
                  {w.dimensions && <span>{w.dimensions}</span>}
                  {w.collection && <span>📦 {w.collection}</span>}
                </div>

                {w.description && (
                  <p className="text-xs text-studio-text-muted line-clamp-2 mb-2">{w.description}</p>
                )}

                {w.exhibition_history?.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {w.exhibition_history.slice(0, 3).map((e) => (
                      <span key={e} className="tag">{e}</span>
                    ))}
                    {w.exhibition_history.length > 3 && (
                      <span className="tag">+{w.exhibition_history.length - 3} more</span>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
