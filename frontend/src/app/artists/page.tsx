"use client";
import { useState } from "react";
import useSWR from "swr";
import { Palette, Plus, X, ExternalLink, Instagram } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getArtists, createArtist, type Artist } from "@/lib/api";

const EMPTY: Omit<Artist, "id" | "created_at"> = {
  name: "",
  country: null,
  city: null,
  bio: null,
  medium: [],
  website: null,
  instagram: null,
  represented_by: [],
};

export default function ArtistsPage() {
  const [query, setQuery] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  const { data, isLoading, mutate } = useSWR(
    ["artists", query],
    () => getArtists(query || undefined)
  );

  const set = (k: keyof typeof EMPTY) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value || null }));

  const handleSave = async () => {
    if (!form.name) return;
    setSaving(true);
    await createArtist({
      ...form,
      medium: form.medium,
      represented_by: form.represented_by,
    });
    setForm(EMPTY);
    setShowAdd(false);
    setSaving(false);
    mutate();
  };

  return (
    <div>
      <PageHeader
        title="Artists"
        description="Artist profiles and research"
        actions={
          <button onClick={() => setShowAdd(!showAdd)} className="btn-primary flex items-center gap-2">
            {showAdd ? <X size={13} /> : <Plus size={13} />}
            {showAdd ? "Cancel" : "Add Artist"}
          </button>
        }
      />

      {showAdd && (
        <div className="card mb-4">
          <h2 className="text-xs font-medium uppercase tracking-widest text-studio-text-muted mb-3">New Artist</h2>
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="text-xs text-studio-text-muted mb-1 block">Name *</label>
              <input value={form.name} onChange={set("name")} placeholder="Artist name" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">City</label>
              <input value={form.city ?? ""} onChange={set("city")} placeholder="City" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Country</label>
              <input value={form.country ?? ""} onChange={set("country")} placeholder="Country" />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-studio-text-muted mb-1 block">Bio</label>
              <textarea value={form.bio ?? ""} onChange={set("bio")} placeholder="Short bio..." rows={3} className="resize-none" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Medium (comma-separated)</label>
              <input
                value={form.medium.join(", ")}
                onChange={(e) => setForm((f) => ({ ...f, medium: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) }))}
                placeholder="video, installation, photography"
              />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Represented by (comma-separated)</label>
              <input
                value={form.represented_by.join(", ")}
                onChange={(e) => setForm((f) => ({ ...f, represented_by: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) }))}
                placeholder="Gallery name, Gallery name"
              />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Website</label>
              <input value={form.website ?? ""} onChange={set("website")} placeholder="https://" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Instagram</label>
              <input value={form.instagram ?? ""} onChange={set("instagram")} placeholder="@handle" />
            </div>
          </div>
          <button
            onClick={handleSave}
            disabled={saving || !form.name}
            className="btn-primary w-full mt-3"
          >
            {saving ? "Saving & Embedding..." : "Save Artist"}
          </button>
        </div>
      )}

      <div className="mb-4">
        <SearchBar onSearch={setQuery} placeholder="Search by name, medium, location..." loading={isLoading} />
      </div>

      {isLoading && <p className="text-studio-text-muted text-xs">Loading...</p>}

      {!isLoading && (!data || data.length === 0) && (
        <EmptyState icon={Palette} message="No artists yet" sub="Add artists manually or via the API" />
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {(data ?? []).map((a: Artist) => (
          <div key={a.id} className="card hover:border-studio-muted transition-colors">
            <div className="flex items-start justify-between gap-2 mb-2">
              <h3 className="text-sm font-medium text-studio-text">{a.name}</h3>
              <div className="flex gap-2 flex-shrink-0">
                {a.instagram && (
                  <a href={`https://instagram.com/${a.instagram.replace("@", "")}`} target="_blank" rel="noopener noreferrer"
                    className="text-studio-text-muted hover:text-studio-accent">
                    <Instagram size={13} />
                  </a>
                )}
                {a.website && (
                  <a href={a.website} target="_blank" rel="noopener noreferrer"
                    className="text-studio-text-muted hover:text-studio-accent">
                    <ExternalLink size={13} />
                  </a>
                )}
              </div>
            </div>

            {(a.city || a.country) && (
              <p className="text-xs text-studio-text-muted mb-2">
                📍 {[a.city, a.country].filter(Boolean).join(", ")}
              </p>
            )}

            {a.bio && (
              <p className="text-xs text-studio-text-muted line-clamp-2 mb-2">{a.bio}</p>
            )}

            <div className="flex flex-wrap gap-1">
              {a.medium?.map((m) => <span key={m} className="tag-accent">{m}</span>)}
              {a.represented_by?.map((g) => <span key={g} className="tag">{g}</span>)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
