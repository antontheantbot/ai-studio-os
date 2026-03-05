"use client";
import { useState } from "react";
import useSWR from "swr";
import { CalendarDays, Plus, X, ExternalLink } from "lucide-react";
import { format, parseISO } from "date-fns";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getExhibitions, createExhibition, getInstitutions, type Exhibition, type Institution } from "@/lib/api";

const EMPTY: Omit<Exhibition, "id" | "created_at"> = {
  title: "",
  institution_id: null,
  curator_id: null,
  start_date: null,
  end_date: null,
  type: null,
  artists: [],
  description: null,
  url: null,
};

const EX_TYPES = ["solo", "group", "survey", "retrospective", "biennial", "fair", "online"];

function dateRange(start: string | null, end: string | null) {
  if (!start && !end) return null;
  const fmt = (d: string) => format(parseISO(d), "MMM yyyy");
  if (start && end) return `${fmt(start)} – ${fmt(end)}`;
  if (start) return `From ${fmt(start)}`;
  return `Until ${fmt(end!)}`;
}

export default function ExhibitionsPage() {
  const [query, setQuery] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState(EMPTY);
  const [saving, setSaving] = useState(false);

  const { data, isLoading, mutate } = useSWR(
    ["exhibitions", query],
    () => getExhibitions(query || undefined)
  );

  const { data: institutions } = useSWR("institutions-list", () => getInstitutions());

  const instMap = Object.fromEntries(
    (institutions ?? []).map((i: Institution) => [i.id, i.name])
  );

  const set = (k: keyof typeof EMPTY) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm((f) => ({ ...f, [k]: e.target.value || null }));

  const handleSave = async () => {
    if (!form.title) return;
    setSaving(true);
    await createExhibition(form);
    setForm(EMPTY);
    setShowAdd(false);
    setSaving(false);
    mutate();
  };

  return (
    <div>
      <PageHeader
        title="Exhibitions"
        description="Exhibition history and upcoming shows"
        actions={
          <button onClick={() => setShowAdd(!showAdd)} className="btn-primary flex items-center gap-2">
            {showAdd ? <X size={13} /> : <Plus size={13} />}
            {showAdd ? "Cancel" : "Add Exhibition"}
          </button>
        }
      />

      {showAdd && (
        <div className="card mb-4">
          <h2 className="text-xs font-medium uppercase tracking-widest text-studio-text-muted mb-3">New Exhibition</h2>
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="text-xs text-studio-text-muted mb-1 block">Title *</label>
              <input value={form.title} onChange={set("title")} placeholder="Exhibition title" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Institution</label>
              <select
                value={form.institution_id ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, institution_id: e.target.value || null }))}
                className="bg-studio-surface border border-studio-border rounded px-3 py-2 text-studio-text w-full outline-none focus:border-studio-accent"
              >
                <option value="">— select institution —</option>
                {(institutions ?? []).map((i: Institution) => (
                  <option key={i.id} value={i.id}>{i.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Type</label>
              <select
                value={form.type ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, type: e.target.value || null }))}
                className="bg-studio-surface border border-studio-border rounded px-3 py-2 text-studio-text w-full outline-none focus:border-studio-accent"
              >
                <option value="">— select type —</option>
                {EX_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Start Date</label>
              <input type="date" value={form.start_date ?? ""} onChange={set("start_date")} />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">End Date</label>
              <input type="date" value={form.end_date ?? ""} onChange={set("end_date")} />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-studio-text-muted mb-1 block">Artists (comma-separated)</label>
              <input
                value={form.artists.join(", ")}
                onChange={(e) => setForm((f) => ({ ...f, artists: e.target.value.split(",").map((s) => s.trim()).filter(Boolean) }))}
                placeholder="Artist One, Artist Two"
              />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-studio-text-muted mb-1 block">Description</label>
              <textarea value={form.description ?? ""} onChange={set("description")} placeholder="Exhibition description..." rows={3} className="resize-none" />
            </div>
            <div className="col-span-2">
              <label className="text-xs text-studio-text-muted mb-1 block">URL</label>
              <input value={form.url ?? ""} onChange={set("url")} placeholder="https://" />
            </div>
          </div>
          <button onClick={handleSave} disabled={saving || !form.title} className="btn-primary w-full mt-3">
            {saving ? "Saving & Embedding..." : "Save Exhibition"}
          </button>
        </div>
      )}

      <div className="mb-4">
        <SearchBar onSearch={setQuery} placeholder="Search by title, artists, description..." loading={isLoading} />
      </div>

      {isLoading && <p className="text-studio-text-muted text-xs">Loading...</p>}

      {!isLoading && (!data || data.length === 0) && (
        <EmptyState icon={CalendarDays} message="No exhibitions yet" sub="Add exhibitions manually or via the API" />
      )}

      <div className="space-y-3">
        {(data ?? []).map((ex: Exhibition) => (
          <div key={ex.id} className="card hover:border-studio-muted transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  {ex.type && <span className="tag">{ex.type}</span>}
                  {ex.institution_id && instMap[ex.institution_id] && (
                    <span className="text-xs text-studio-accent">{instMap[ex.institution_id]}</span>
                  )}
                </div>
                <h3 className="text-sm font-medium text-studio-text mb-1">{ex.title}</h3>
                {ex.description && (
                  <p className="text-xs text-studio-text-muted line-clamp-2 mb-2">{ex.description}</p>
                )}
                {ex.artists?.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {ex.artists.slice(0, 6).map((a) => (
                      <span key={a} className="tag">{a}</span>
                    ))}
                    {ex.artists.length > 6 && (
                      <span className="tag">+{ex.artists.length - 6} more</span>
                    )}
                  </div>
                )}
              </div>
              <div className="flex-shrink-0 text-right space-y-2">
                {dateRange(ex.start_date, ex.end_date) && (
                  <div className="tag-accent text-right">{dateRange(ex.start_date, ex.end_date)}</div>
                )}
                {ex.url && (
                  <a href={ex.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center justify-end gap-1 text-xs text-studio-accent hover:underline">
                    <ExternalLink size={11} /> View
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
