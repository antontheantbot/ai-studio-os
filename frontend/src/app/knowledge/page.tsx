"use client";
import { useState } from "react";
import useSWR from "swr";
import { BookOpen, Plus, X } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getKnowledge, searchKnowledge, createNote, type KnowledgeItem } from "@/lib/api";

const SOURCE_COLORS: Record<string, string> = {
  note: "text-studio-accent",
  article: "text-blue-400",
  pdf: "text-red-400",
  url: "text-purple-400",
  reference: "text-orange-400",
};

export default function KnowledgePage() {
  const [query, setQuery] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [note, setNote] = useState({ title: "", content: "", tags: "" });
  const [saving, setSaving] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data: all, mutate } = useSWR("knowledge", getKnowledge);
  const { data: results, isLoading } = useSWR(
    query ? ["knowledge-search", query] : null,
    () => searchKnowledge(query)
  );

  const items: KnowledgeItem[] = query ? (results ?? []) : (all ?? []);

  const handleSave = async () => {
    if (!note.title || !note.content) return;
    setSaving(true);
    await createNote({
      title: note.title,
      content: note.content,
      tags: note.tags.split(",").map((t) => t.trim()).filter(Boolean),
    });
    setNote({ title: "", content: "", tags: "" });
    setShowAdd(false);
    setSaving(false);
    mutate();
  };

  return (
    <div>
      <PageHeader
        title="Knowledge Base"
        description="Articles, notes, references and research"
        actions={
          <button onClick={() => setShowAdd(!showAdd)} className="btn-primary flex items-center gap-2">
            {showAdd ? <X size={13} /> : <Plus size={13} />}
            {showAdd ? "Cancel" : "Add Note"}
          </button>
        }
      />

      {showAdd && (
        <div className="card mb-4">
          <h2 className="text-xs font-medium uppercase tracking-widest text-studio-text-muted mb-3">New Note</h2>
          <div className="space-y-3">
            <input
              value={note.title}
              onChange={(e) => setNote((n) => ({ ...n, title: e.target.value }))}
              placeholder="Title"
            />
            <textarea
              value={note.content}
              onChange={(e) => setNote((n) => ({ ...n, content: e.target.value }))}
              placeholder="Content..."
              rows={6}
              className="resize-none"
            />
            <input
              value={note.tags}
              onChange={(e) => setNote((n) => ({ ...n, tags: e.target.value }))}
              placeholder="Tags (comma-separated)"
            />
            <button
              onClick={handleSave}
              disabled={saving || !note.title || !note.content}
              className="btn-primary w-full"
            >
              {saving ? "Saving & Embedding..." : "Save Note"}
            </button>
          </div>
        </div>
      )}

      <div className="mb-4">
        <SearchBar onSearch={setQuery} placeholder="Semantic search across all knowledge..." loading={isLoading} />
      </div>

      {!isLoading && items.length === 0 && (
        <EmptyState icon={BookOpen} message="No knowledge items yet" sub="Add notes or ingest URLs via the API" />
      )}

      <div className="space-y-3">
        {items.map((k: KnowledgeItem) => {
          const isExpanded = expandedId === k.id;
          return (
            <div
              key={k.id}
              className="card hover:border-studio-muted transition-colors cursor-pointer"
              onClick={() => setExpandedId(isExpanded ? null : k.id)}
            >
              <div className="flex items-start justify-between gap-4 mb-2">
                <h3 className="text-sm font-medium text-studio-text">{k.title}</h3>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {k.similarity !== undefined && (
                    <span className="text-xs text-studio-accent">{(k.similarity * 100).toFixed(0)}%</span>
                  )}
                  <span className={`text-xs ${SOURCE_COLORS[k.source_type] ?? "text-studio-text-muted"}`}>
                    {k.source_type}
                  </span>
                </div>
              </div>
              <p className={`text-xs text-studio-text-muted mb-2 whitespace-pre-wrap ${isExpanded ? "" : "line-clamp-3"}`}>
                {isExpanded ? (k.content || k.summary) : (k.summary || k.content)}
              </p>
              {k.tags?.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {k.tags.slice(0, 6).map((t) => <span key={t} className="tag">{t}</span>)}
                </div>
              )}
              <div className="text-xs text-studio-border mt-2">
                {new Date(k.created_at).toLocaleDateString()}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
