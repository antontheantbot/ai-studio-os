"use client";
import { useState } from "react";
import useSWR from "swr";
import {
  Users, GraduationCap, PenLine, Landmark, Building2, Plus, X,
  RefreshCw, Check, Mail, Globe, AlertCircle, Search,
} from "lucide-react";
import PageHeader from "@/components/PageHeader";
import {
  getContacts, parseContacts, confirmContacts, scanAllContacts,
  type Contact, type ParsedContact,
} from "@/lib/api";

const CATEGORIES = ["all", "curator", "journalist", "institution", "collector", "corporation"] as const;
type CategoryFilter = typeof CATEGORIES[number];

const CATEGORY_LABELS: Record<string, string> = {
  curator: "Curator", journalist: "Journalist", institution: "Institution",
  collector: "Collector", corporation: "Corporation", unknown: "Unknown",
};

const CATEGORY_COLOURS: Record<string, string> = {
  curator:     "bg-purple-900/40 text-purple-300 border border-purple-700/40",
  journalist:  "bg-blue-900/40 text-blue-300 border border-blue-700/40",
  institution: "bg-amber-900/40 text-amber-300 border border-amber-700/40",
  collector:   "bg-green-900/40 text-green-300 border border-green-700/40",
  corporation: "bg-rose-900/40 text-rose-300 border border-rose-700/40",
  unknown:     "bg-gray-900/40 text-gray-300 border border-gray-700/40",
};

function ContactCard({ contact }: { contact: Contact }) {
  const colourClass = CATEGORY_COLOURS[contact.category] ?? CATEGORY_COLOURS.unknown;
  const website = contact.website || (contact.social_links as Record<string,string>)?.website;
  return (
    <div className="card hover:border-studio-muted transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-0.5">
            <h3 className="text-sm font-medium text-studio-text">{contact.name}</h3>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${colourClass}`}>
              {CATEGORY_LABELS[contact.category] ?? contact.category}
            </span>
            {!contact.email && (
              <span className="flex items-center gap-0.5 text-[10px] text-studio-text-muted/60 italic">
                <AlertCircle size={9} /> no email
              </span>
            )}
          </div>
          {(contact.role || contact.organization) && (
            <p className="text-xs text-studio-text-muted mb-1">
              {[contact.role, contact.organization].filter(Boolean).join(" · ")}
            </p>
          )}
          {(contact.location || contact.country) && (
            <p className="text-xs text-studio-text-muted/70">
              📍 {[contact.location, contact.country].filter(Boolean).join(", ")}
            </p>
          )}
          {contact.tags && contact.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {contact.tags.slice(0, 4).map(t => <span key={t} className="tag">{t}</span>)}
            </div>
          )}
        </div>
        <div className="flex-shrink-0 flex flex-col items-end gap-1.5">
          {contact.email && (
            <a href={`mailto:${contact.email}`}
              className="flex items-center gap-1 text-xs text-studio-accent hover:underline max-w-[180px] truncate">
              <Mail size={11} className="flex-shrink-0" />
              <span className="truncate">{contact.email}</span>
            </a>
          )}
          {website && (
            <a href={website} target="_blank" rel="noopener noreferrer"
              className="text-studio-text-muted hover:text-studio-accent" title="Website">
              <Globe size={12} />
            </a>
          )}
          <span className="text-[10px] text-studio-text-muted/40 mt-1">
            {new Date(contact.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}
          </span>
        </div>
      </div>
    </div>
  );
}

function ParsedPreviewCard({
  contact, index, onChange, onRemove,
}: {
  contact: ParsedContact;
  index: number;
  onChange: (i: number, updated: ParsedContact) => void;
  onRemove: (i: number) => void;
}) {
  const colourClass = CATEGORY_COLOURS[contact.category] ?? CATEGORY_COLOURS.unknown;
  const isUncertain = contact.uncertain;
  return (
    <div className={`card ${isUncertain ? "border-amber-500/50 bg-amber-950/10" : "border-studio-accent/20"}`}>
      {isUncertain && (
        <div className="flex items-center gap-1.5 text-amber-400 text-[11px] mb-2">
          <AlertCircle size={12} className="flex-shrink-0" />
          <span>Couldn't confidently determine category — please select one below before saving.</span>
        </div>
      )}
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <select
              value={contact.category}
              onChange={e => onChange(index, { ...contact, category: e.target.value as ParsedContact["category"], uncertain: false })}
              className={`text-[10px] px-1.5 py-0.5 rounded font-medium border-0 outline-none cursor-pointer ${isUncertain ? "bg-amber-900/40 text-amber-300 border border-amber-500/60" : colourClass + " bg-transparent"}`}
            >
              {(["curator","journalist","institution","collector","corporation"] as const).map(c => (
                <option key={c} value={c}>{CATEGORY_LABELS[c]}</option>
              ))}
            </select>
            <input
              value={contact.name}
              onChange={e => onChange(index, { ...contact, name: e.target.value })}
              className="bg-transparent text-sm font-medium text-studio-text border-0 outline-none border-b border-transparent hover:border-studio-border focus:border-studio-accent flex-1 min-w-0"
            />
          </div>
          <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
            {([ ["role", contact.role, "Role / Title"], ["organization", contact.organization, "Organisation"], ["email", contact.email, "Email"], ["location", contact.location, "City"] ] as [string, string|null, string][]).map(([field, val, placeholder]) => (
              <input key={field} value={val ?? ""} onChange={e => onChange(index, { ...contact, [field]: e.target.value || null })}
                placeholder={placeholder}
                className="bg-transparent text-studio-text-muted border-0 outline-none border-b border-transparent hover:border-studio-border focus:border-studio-accent placeholder:text-studio-text-muted/30"
              />
            ))}
          </div>
          {contact.bio && <p className="text-xs text-studio-text-muted/70 mt-1.5 line-clamp-2">{contact.bio}</p>}
          {contact.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {contact.tags.slice(0, 5).map(t => <span key={t} className="tag">{t}</span>)}
            </div>
          )}
        </div>
        <button onClick={() => onRemove(index)} className="text-studio-text-muted hover:text-red-400 flex-shrink-0 mt-0.5">
          <X size={13} />
        </button>
      </div>
    </div>
  );
}

export default function ContactsPage() {
  const [categoryFilter, setCategoryFilter] = useState<CategoryFilter>("all");
  const [query, setQuery] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [scanMsg, setScanMsg] = useState<string | null>(null);

  const [pasteText, setPasteText] = useState("");
  const [parsing, setParsing] = useState(false);
  const [parsedContacts, setParsedContacts] = useState<ParsedContact[] | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState<{ message: string } | null>(null);

  const { data: contacts, mutate } = useSWR(
    ["contacts", query, categoryFilter],
    () => getContacts(query || undefined, categoryFilter === "all" ? undefined : categoryFilter)
  );

  const missingEmail = (contacts ?? []).filter(c => !c.email).length;

  const handleScan = async () => {
    setScanning(true); setScanMsg(null);
    try {
      await scanAllContacts();
      setScanMsg("Scanning all categories in background — check back in ~5 minutes");
      setTimeout(() => setScanMsg(null), 8000);
    } finally { setScanning(false); }
  };

  const handleParse = async () => {
    if (!pasteText.trim()) return;
    setParsing(true); setParsedContacts(null); setParseError(null); setSaveResult(null);
    try {
      const res = await parseContacts(pasteText);
      if (res.contacts.length === 0) setParseError(res.error ?? "No contacts found — try adding more detail.");
      else setParsedContacts(res.contacts);
    } finally { setParsing(false); }
  };

  const handleConfirm = async () => {
    if (!parsedContacts?.length) return;
    setSaving(true);
    try {
      const res = await confirmContacts(parsedContacts);
      setSaveResult(res);
      if (res.added > 0) { mutate(); setParsedContacts(null); setPasteText(""); }
    } finally { setSaving(false); }
  };

  const updateParsed = (i: number, updated: ParsedContact) =>
    setParsedContacts(prev => prev ? prev.map((c, idx) => idx === i ? updated : c) : prev);
  const removeParsed = (i: number) =>
    setParsedContacts(prev => prev ? prev.filter((_, idx) => idx !== i) : prev);

  return (
    <div>
      <PageHeader
        title="Contacts"
        description="Curators, journalists, institutions, collectors and corporate partners — all in one place"
        actions={
          <div className="flex items-center gap-2">
            <button onClick={() => setShowAdd(v => !v)} className="btn-ghost flex items-center gap-2">
              <Plus size={13} /> Add Contact
            </button>
            <button onClick={handleScan} disabled={scanning} className="btn-primary flex items-center gap-2">
              <RefreshCw size={13} className={scanning ? "animate-spin" : ""} />
              {scanning ? "Scanning..." : "Scan Web"}
            </button>
          </div>
        }
      />

      {scanMsg && (
        <div className="fixed bottom-6 right-6 z-50 bg-studio-surface border border-studio-accent/40 rounded-lg px-4 py-3 shadow-lg flex items-center gap-3 text-sm">
          <Check size={14} className="text-studio-accent flex-shrink-0" />
          <span className="text-studio-text text-xs">{scanMsg}</span>
          <button onClick={() => setScanMsg(null)} className="text-studio-text-muted hover:text-studio-text ml-1"><X size={12} /></button>
        </div>
      )}

      {/* Add Contact panel */}
      {showAdd && (
        <div className="card border-studio-accent/20 mb-5">
          {!parsedContacts ? (
            <div>
              <p className="text-xs font-medium text-studio-text mb-2">Paste contact information</p>
              <p className="text-xs text-studio-text-muted mb-3">
                Paste anything — names, bios, emails, LinkedIn profiles, press releases, website copy, or any mix.
                Claude will extract contacts and automatically assign them to the right category.
              </p>
              <textarea
                value={pasteText}
                onChange={e => setPasteText(e.target.value)}
                placeholder={"e.g.\nSarah Jones — Chief Curator, Tate Modern — sarah.jones@tate.org.uk\n\nArtforum writer covering digital art. Based in New York."}
                className="w-full h-40 bg-studio-bg border border-studio-border rounded text-xs text-studio-text p-3 resize-none focus:outline-none focus:border-studio-accent placeholder:text-studio-text-muted/40"
              />
              {parseError && (
                <div className="flex items-start gap-2 mt-3 text-xs text-amber-400 bg-amber-950/20 border border-amber-700/30 rounded p-2">
                  <AlertCircle size={12} className="flex-shrink-0 mt-0.5" /><span>{parseError}</span>
                </div>
              )}
              <div className="flex justify-between mt-3">
                <button onClick={() => { setShowAdd(false); setPasteText(""); setParseError(null); }} className="btn-ghost flex items-center gap-1.5"><X size={12} /> Cancel</button>
                <button onClick={handleParse} disabled={parsing || !pasteText.trim()} className="btn-primary flex items-center gap-2">
                  {parsing ? <RefreshCw size={12} className="animate-spin" /> : <Search size={12} />}
                  {parsing ? "Extracting contacts..." : "Extract Contacts"}
                </button>
              </div>
            </div>
          ) : (
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm font-medium text-studio-text">{parsedContacts.length} contact{parsedContacts.length !== 1 ? "s" : ""} found</p>
                  <p className="text-xs text-studio-text-muted mt-0.5">Review and edit below, then confirm to save</p>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => { setParsedContacts(null); setSaveResult(null); }} className="btn-ghost flex items-center gap-1.5"><X size={12} /> Start over</button>
                  {parsedContacts.filter(c => c.uncertain).length > 0 && (
                    <span className="flex items-center gap-1 text-[11px] text-amber-400">
                      <AlertCircle size={11} />{parsedContacts.filter(c => c.uncertain).length} need a category
                    </span>
                  )}
                  <button onClick={handleConfirm} disabled={saving || parsedContacts.length === 0} className="btn-primary flex items-center gap-2">
                    {saving ? <RefreshCw size={12} className="animate-spin" /> : <Check size={12} />}
                    {saving ? "Saving..." : `Save ${parsedContacts.length} Contact${parsedContacts.length !== 1 ? "s" : ""}`}
                  </button>
                </div>
              </div>
              {saveResult && (
                <div className="card mb-4 border-studio-accent/30 flex items-center gap-2 text-xs">
                  <Check size={13} className="text-studio-accent flex-shrink-0" />
                  <span className="text-studio-text">{saveResult.message}</span>
                </div>
              )}
              <div className="grid grid-cols-1 gap-3">
                {parsedContacts.map((c, i) => <ParsedPreviewCard key={i} contact={c} index={i} onChange={updateParsed} onRemove={removeParsed} />)}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3 mb-4">
        <div className="relative flex-1">
          <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-studio-text-muted pointer-events-none" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search by name, organisation, location, tags..."
            className="w-full pl-8 pr-3 py-2 bg-studio-surface border border-studio-border rounded text-xs text-studio-text placeholder:text-studio-text-muted/50 focus:outline-none focus:border-studio-accent"
          />
          {query && <button onClick={() => setQuery("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-studio-text-muted hover:text-studio-text"><X size={12} /></button>}
        </div>
        <select
          value={categoryFilter}
          onChange={e => setCategoryFilter(e.target.value as CategoryFilter)}
          className="bg-studio-surface border border-studio-border rounded text-xs text-studio-text px-3 py-2 focus:outline-none focus:border-studio-accent"
        >
          {CATEGORIES.map(c => (
            <option key={c} value={c}>{c === "all" ? `All (${(contacts ?? []).length})` : `${CATEGORY_LABELS[c]} (${(contacts ?? []).filter(x => x.category === c).length})`}</option>
          ))}
        </select>
        {missingEmail > 0 && (
          <span className="flex items-center gap-1 text-[10px] text-amber-400/80 whitespace-nowrap">
            <AlertCircle size={11} />{missingEmail} missing email
          </span>
        )}
      </div>

      {/* Contact list */}
      {(contacts ?? []).length === 0 ? (
        <div className="text-center py-16 text-studio-text-muted">
          <Users size={32} strokeWidth={1} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">No contacts yet</p>
          <p className="text-xs mt-1 opacity-60">Use "Add Contact" or "Scan Web" to populate</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3">
          {(contacts ?? []).map(c => <ContactCard key={c.id} contact={c} />)}
        </div>
      )}
    </div>
  );
}
