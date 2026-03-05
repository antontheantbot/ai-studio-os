"use client";
import { useState } from "react";
import useSWR from "swr";
import { Landmark, Plus, X, ExternalLink } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getInstitutions, createInstitution, type Institution } from "@/lib/api";

const INSTITUTION_TYPES = ["museum", "gallery", "kunsthalle", "biennial", "foundation", "residency", "university", "festival"];

const EMPTY: Omit<Institution, "id" | "created_at"> = {
  name: "",
  city: null,
  country: null,
  type: null,
  website: null,
  focus_areas: [],
  annual_budget: null,
  digital_art_program: false,
  notes: null,
};

export default function InstitutionsPage() {
  const [query, setQuery] = useState("");
  const [digitalOnly, setDigitalOnly] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  const { data, isLoading, mutate } = useSWR(
    ["institutions", query, digitalOnly],
    () => getInstitutions(query || undefined, digitalOnly || undefined)
  );

  const set = (k: keyof typeof EMPTY) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value || null }));

  const handleSave = async () => {
    if (!form.name) return;
    setSaving(true);
    await createInstitution(form);
    setForm(EMPTY);
    setShowAdd(false);
    setSaving(false);
    mutate();
  };

  return (
    <div>
      <PageHeader
        title="Institutions"
        description="Museums, galleries, kunsthalles and art foundations"
        actions={
          <button onClick={() => setShowAdd(!showAdd)} className="btn-primary flex items-center gap-2">
            {showAdd ? <X size={13} /> : <Plus size={13} />}
            {showAdd ? "Cancel" : "Add Institution"}
          </button>
        }
      />

      {showAdd && (
        <div className="card mb-4">
          <h2 className="text-xs font-medium uppercase tracking-widest text-studio-text-muted mb-3">New Institution</h2>
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="text-xs text-studio-text-muted mb-1 block">Name *</label>
              <input value={form.name} onChange={set("name")} placeholder="Institution name" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Type</label>
              <select
                value={form.type ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, type: e.target.value || null }))}
                className="bg-studio-surface border border-studio-border rounded px-3 py-2 text-studio-text w-full outline-none focus:border-studio-accent"
              >
                <option value="">— select type —</option>
                {INSTITUTION_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Website</label>
              <input value={form.website ?? ""} onChange={set("website")} placeholder="https://" />
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
              <label className="text-xs text-studio-text-muted mb-1 block">Focus Areas (comma-separated)</label>
              <input
                value={form.focus_areas.join(", ")}
                onChange={(e) => setForm((f) => ({ ...f, focus_areas: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) }))}
                placeholder="digital art, new media, video, performance"
              />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Annual Budget</label>
              <input value={form.annual_budget ?? ""} onChange={set("annual_budget")} placeholder="€2M" />
            </div>
            <div className="flex items-center gap-2 pt-5">
              <input
                type="checkbox"
                id="digital_art_program"
                checked={form.digital_art_program}
                onChange={(e) => setForm((f) => ({ ...f, digital_art_program: e.target.checked }))}
                className="w-4 h-4 accent-studio-accent"
              />
              <label htmlFor="digital_art_program" className="text-xs text-studio-text-muted cursor-pointer">
                Has digital art program
              </label>
            </div>
            <div className="col-span-2">
              <label className="text-xs text-studio-text-muted mb-1 block">Notes</label>
              <textarea value={form.notes ?? ""} onChange={set("notes")} placeholder="Internal notes..." rows={2} className="resize-none" />
            </div>
          </div>
          <button onClick={handleSave} disabled={saving || !form.name} className="btn-primary w-full mt-3">
            {saving ? "Saving & Embedding..." : "Save Institution"}
          </button>
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
