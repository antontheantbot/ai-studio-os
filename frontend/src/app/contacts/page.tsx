"use client";
import { useState } from "react";
import useSWR from "swr";
import {
  Users, GraduationCap, PenLine, Landmark, Building2, Plus, X,
  RefreshCw, Check, Mail, Globe, AlertCircle, Search,
} from "lucide-react";
import PageHeader from "@/components/PageHeader";
import {
  getCurators, getCollectors, getJournalists, getInstitutions, getCorporations,
  addCuratorsFromText, addCollectorsFromText, addJournalistsFromText,
  addInstitutionsFromText, addCorporationsFromText,
  parseContacts, confirmContacts, scanAllContacts,
  type Curator, type Collector, type Journalist, type Institution,
  type Corporation, type ParsedContact,
} from "@/lib/api";

// ─── Types ────────────────────────────────────────────────────────────────────

type Tab = "all" | "curators" | "journalists" | "institutions" | "collectors" | "corporations" | "add";

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: "all",          label: "All",          icon: Users },
  { id: "curators",     label: "Curators",     icon: GraduationCap },
  { id: "journalists",  label: "Journalists",  icon: PenLine },
  { id: "institutions", label: "Institutions", icon: Landmark },
  { id: "collectors",   label: "Collectors",   icon: Users },
  { id: "corporations", label: "Corporations", icon: Building2 },
  { id: "add",          label: "+ Add Contact", icon: Plus },
];

const CATEGORY_LABELS: Record<ParsedContact["category"], string> = {
  curator: "Curator",
  journalist: "Journalist",
  institution: "Institution",
  collector: "Collector",
  corporation: "Corporation",
};

const CATEGORY_COLOURS: Record<ParsedContact["category"], string> = {
  curator:     "bg-purple-900/40 text-purple-300 border border-purple-700/40",
  journalist:  "bg-blue-900/40 text-blue-300 border border-blue-700/40",
  institution: "bg-amber-900/40 text-amber-300 border border-amber-700/40",
  collector:   "bg-green-900/40 text-green-300 border border-green-700/40",
  corporation: "bg-rose-900/40 text-rose-300 border border-rose-700/40",
};

// ─── Normaliser ───────────────────────────────────────────────────────────────

interface NormalisedContact {
  id: string;
  name: string;
  role: string | null;
  organization: string | null;
  email: string | null;
  location: string | null;
  country: string | null;
  website: string | null;
  tags: string[];
  category: ParsedContact["category"];
  created_at: string;
}

function normaliseCurator(c: Curator): NormalisedContact {
  return { id: c.id, name: c.name, role: c.role, organization: c.institution, email: c.contact_email, location: c.location, country: c.country, website: c.contact_url, tags: c.focus_areas ?? [], category: "curator", created_at: c.created_at };
}
function normaliseJournalist(j: Journalist): NormalisedContact {
  return { id: j.id, name: j.name, role: null, organization: j.publications?.[0] ?? null, email: j.email, location: j.location, country: j.country, website: j.social_links?.website ?? null, tags: j.beats ?? [], category: "journalist", created_at: j.created_at };
}
function normaliseInstitution(i: Institution): NormalisedContact {
  return { id: i.id, name: i.name, role: i.type, organization: null, email: null, location: i.city, country: i.country, website: i.website, tags: i.focus_areas ?? [], category: "institution", created_at: i.created_at };
}
function normaliseCollector(c: Collector): NormalisedContact {
  return { id: c.id, name: c.name, role: null, organization: c.institutions?.[0] ?? null, email: c.contact_email, location: c.location, country: c.country, website: c.contact_url, tags: c.interests ?? [], category: "collector", created_at: c.created_at };
}
function normaliseCorporation(c: Corporation): NormalisedContact {
  return { id: c.id, name: c.name, role: c.type, organization: c.contact_name, email: c.email, location: c.city, country: c.country, website: c.website, tags: c.focus_areas ?? [], category: "corporation", created_at: c.created_at };
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function ContactCard({ contact }: { contact: NormalisedContact }) {
  const colourClass = CATEGORY_COLOURS[contact.category];
  return (
    <div className="card hover:border-studio-muted transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-0.5">
            <h3 className="text-sm font-medium text-studio-text">{contact.name}</h3>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${colourClass}`}>
              {CATEGORY_LABELS[contact.category]}
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

          {contact.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {contact.tags.slice(0, 4).map(t => <span key={t} className="tag">{t}</span>)}
            </div>
          )}
        </div>

        <div className="flex-shrink-0 flex flex-col items-end gap-1.5">
          {contact.email ? (
            <a href={`mailto:${contact.email}`}
              className="flex items-center gap-1 text-xs text-studio-accent hover:underline max-w-[180px] truncate">
              <Mail size={11} className="flex-shrink-0" />
              <span className="truncate">{contact.email}</span>
            </a>
          ) : null}
          {contact.website && (
            <a href={contact.website} target="_blank" rel="noopener noreferrer"
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
  const [expanded, setExpanded] = useState(false);
  const colourClass = CATEGORY_COLOURS[contact.category];
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
            {/* Category selector */}
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
            {[
              ["role", contact.role, "Role / Title"],
              ["organization", contact.organization, "Organisation"],
              ["email", contact.email, "Email"],
              ["location", contact.location, "City"],
            ].map(([field, val, placeholder]) => (
              <input
                key={field as string}
                value={(val as string) ?? ""}
                onChange={e => onChange(index, { ...contact, [field as string]: e.target.value || null })}
                placeholder={placeholder as string}
                className="bg-transparent text-studio-text-muted border-0 outline-none border-b border-transparent hover:border-studio-border focus:border-studio-accent placeholder:text-studio-text-muted/30"
              />
            ))}
          </div>

          {contact.bio && (
            <p className="text-xs text-studio-text-muted/70 mt-1.5 line-clamp-2">{contact.bio}</p>
          )}

          {contact.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {contact.tags.slice(0, 5).map(t => <span key={t} className="tag">{t}</span>)}
            </div>
          )}
        </div>

        <button onClick={() => onRemove(index)}
          className="text-studio-text-muted hover:text-red-400 flex-shrink-0 mt-0.5">
          <X size={13} />
        </button>
      </div>
    </div>
  );
}

// ─── Category paste panels ────────────────────────────────────────────────────

function CategoryPastePanel({
  category, label, mutate,
}: {
  category: Tab;
  label: string;
  mutate: () => void;
}) {
  const [pasteText, setPasteText] = useState("");
  const [adding, setAdding] = useState(false);
  const [result, setResult] = useState<{ message: string } | null>(null);


  const addFns: Record<string, (t: string) => Promise<{ added: number; skipped: number; message: string }>> = {
    curators:     addCuratorsFromText,
    journalists:  addJournalistsFromText,
    institutions: addInstitutionsFromText,
    collectors:   addCollectorsFromText,
    corporations: addCorporationsFromText,
  };

  const handleAdd = async () => {
    if (!pasteText.trim()) return;
    setAdding(true);
    setResult(null);
    try {
      const res = await addFns[category]!(pasteText);
      setResult(res);
      if (res.added > 0) { mutate(); setPasteText(""); }
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="card mb-4 border-studio-accent/20">
      <p className="text-xs text-studio-text-muted mb-3">
        Paste anything — names, bios, emails, LinkedIn profiles, lists. Claude will extract and add them automatically.
      </p>
      <textarea
        value={pasteText}
        onChange={e => setPasteText(e.target.value)}
        placeholder={`Paste ${label.toLowerCase()} info here...`}
        className="w-full h-32 bg-studio-bg border border-studio-border rounded text-xs text-studio-text p-3 resize-none focus:outline-none focus:border-studio-accent placeholder:text-studio-text-muted/40"
      />
      <div className="flex items-center justify-between mt-3">
        {result ? (
          <div className="flex items-center gap-2 text-xs">
            <Check size={12} className="text-studio-accent" />
            <span className="text-studio-text">{result.message}</span>
          </div>
        ) : <div />}
        <button onClick={handleAdd} disabled={adding || !pasteText.trim()} className="btn-primary flex items-center gap-2">
          {adding ? <RefreshCw size={12} className="animate-spin" /> : <Plus size={12} />}
          {adding ? "Processing..." : "Add to Database"}
        </button>
      </div>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function ContactsPage() {
  const [tab, setTab] = useState<Tab>("all");
  const [query, setQuery] = useState("");
  const [scanning, setScanning] = useState(false);
  const [scanMsg, setScanMsg] = useState<string | null>(null);

  // Add Contact flow
  const [pasteText, setPasteText] = useState("");
  const [parsing, setParsing] = useState(false);
  const [parsedContacts, setParsedContacts] = useState<ParsedContact[] | null>(null);
  const [parseError, setParseError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveResult, setSaveResult] = useState<{ message: string } | null>(null);

  // Data fetches
  const { data: curators,     mutate: mutateCurators }     = useSWR(["curators",     query], () => getCurators(query || undefined));
  const { data: journalists,  mutate: mutateJournalists }  = useSWR(["journalists",  query], () => getJournalists(query || undefined));
  const { data: institutions, mutate: mutateInstitutions } = useSWR(["institutions", query], () => getInstitutions(query || undefined));
  const { data: collectors,   mutate: mutateCollectors }   = useSWR(["collectors",   query], () => getCollectors(query || undefined));
  const { data: corporations, mutate: mutateCorporations } = useSWR(["corporations", query], () => getCorporations(query || undefined));

  const mutateAll = () => { mutateCurators(); mutateJournalists(); mutateInstitutions(); mutateCollectors(); mutateCorporations(); };

  // Normalised + merged
  const allContacts: NormalisedContact[] = [
    ...(curators     ?? []).map(normaliseCurator),
    ...(journalists  ?? []).map(normaliseJournalist),
    ...(institutions ?? []).map(normaliseInstitution),
    ...(collectors   ?? []).map(normaliseCollector),
    ...(corporations ?? []).map(normaliseCorporation),
  ].sort((a, b) => a.name.localeCompare(b.name));

  const tabContacts: Record<string, NormalisedContact[]> = {
    all:          allContacts,
    curators:     (curators     ?? []).map(normaliseCurator),
    journalists:  (journalists  ?? []).map(normaliseJournalist),
    institutions: (institutions ?? []).map(normaliseInstitution),
    collectors:   (collectors   ?? []).map(normaliseCollector),
    corporations: (corporations ?? []).map(normaliseCorporation),
  };

  const visibleContacts = tabContacts[tab] ?? [];
  const missingEmail = visibleContacts.filter(c => !c.email).length;

  const handleScan = async () => {
    setScanning(true);
    setScanMsg(null);
    try {
      await scanAllContacts();
      setScanMsg("Scanning all categories in background — check back in ~5 minutes");
      setTimeout(() => setScanMsg(null), 8000);
    } finally {
      setScanning(false);
    }
  };

  const handleParse = async () => {
    if (!pasteText.trim()) return;
    setParsing(true);
    setParsedContacts(null);
    setParseError(null);
    setSaveResult(null);
    try {
      const res = await parseContacts(pasteText);
      if (res.contacts.length === 0) {
        setParseError(res.error ?? "No contacts found — try adding more detail (names, roles, emails, organisations).");
      } else {
        setParsedContacts(res.contacts);
      }
    } finally {
      setParsing(false);
    }
  };

  const handleConfirm = async () => {
    if (!parsedContacts?.length) return;
    setSaving(true);
    try {
      const res = await confirmContacts(parsedContacts);
      setSaveResult(res);
      if (res.added > 0) {
        mutateAll();
        setParsedContacts(null);
        setPasteText("");
      }
    } finally {
      setSaving(false);
    }
  };

  const updateParsed = (i: number, updated: ParsedContact) => {
    setParsedContacts(prev => prev ? prev.map((c, idx) => idx === i ? updated : c) : prev);
  };
  const removeParsed = (i: number) => {
    setParsedContacts(prev => prev ? prev.filter((_, idx) => idx !== i) : prev);
  };

  return (
    <div>
      <PageHeader
        title="Contacts"
        description="Curators, journalists, institutions, collectors and corporate partners — all in one place"
        actions={
          <button onClick={handleScan} disabled={scanning} className="btn-primary flex items-center gap-2">
            <RefreshCw size={13} className={scanning ? "animate-spin" : ""} />
            {scanning ? "Scanning..." : "Scan Web"}
          </button>
        }
      />

      {scanMsg && (
        <div className="fixed bottom-6 right-6 z-50 bg-studio-surface border border-studio-accent/40 rounded-lg px-4 py-3 shadow-lg flex items-center gap-3 text-sm">
          <Check size={14} className="text-studio-accent flex-shrink-0" />
          <span className="text-studio-text text-xs">{scanMsg}</span>
          <button onClick={() => setScanMsg(null)} className="text-studio-text-muted hover:text-studio-text ml-1"><X size={12} /></button>
        </div>
      )}

      {/* Tab bar */}
      <div className="flex items-center gap-0.5 mb-5 border-b border-studio-border overflow-x-auto pb-px">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => { setTab(id); if (id !== "add") { setParsedContacts(null); setSaveResult(null); } }}
            className={`flex items-center gap-1.5 px-3 py-2 text-xs whitespace-nowrap transition-colors border-b-2 -mb-px ${
              tab === id
                ? "text-studio-accent border-studio-accent"
                : "text-studio-text-muted border-transparent hover:text-studio-text"
            }`}
          >
            <Icon size={12} strokeWidth={1.5} />
            {label}
            {id !== "all" && id !== "add" && tabContacts[id]?.length > 0 && (
              <span className="text-[10px] bg-studio-surface rounded-full px-1.5 py-0.5 text-studio-text-muted ml-0.5">
                {tabContacts[id].length}
              </span>
            )}
            {id === "all" && allContacts.length > 0 && (
              <span className="text-[10px] bg-studio-surface rounded-full px-1.5 py-0.5 text-studio-text-muted ml-0.5">
                {allContacts.length}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* ── Add Contact Tab ── */}
      {tab === "add" && (
        <div>
          {!parsedContacts ? (
            <div className="card border-studio-accent/20 mb-4">
              <p className="text-xs font-medium text-studio-text mb-2">Paste contact information</p>
              <p className="text-xs text-studio-text-muted mb-3">
                Paste anything — names, bios, emails, LinkedIn profiles, press releases, website copy, or any mix.
                Claude will extract contacts and automatically assign them to the right category.
              </p>
              <textarea
                value={pasteText}
                onChange={e => setPasteText(e.target.value)}
                placeholder={"e.g.\nSarah Jones — Chief Curator, Tate Modern — sarah.jones@tate.org.uk\n\nArtforum writer covering digital art. Based in New York.\n\nLVMH Foundation — Paris — contemporary art and digital media\n\nOr paste a full bio, LinkedIn excerpt, email footer, or any list..."}
                className="w-full h-48 bg-studio-bg border border-studio-border rounded text-xs text-studio-text p-3 resize-none focus:outline-none focus:border-studio-accent placeholder:text-studio-text-muted/40"
              />
              {parseError && (
                <div className="flex items-start gap-2 mt-3 text-xs text-amber-400 bg-amber-950/20 border border-amber-700/30 rounded p-2">
                  <AlertCircle size={12} className="flex-shrink-0 mt-0.5" />
                  <span>{parseError}</span>
                </div>
              )}
              <div className="flex justify-end mt-3">
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
                  <p className="text-sm font-medium text-studio-text">
                    {parsedContacts.length} contact{parsedContacts.length !== 1 ? "s" : ""} found
                  </p>
                  <p className="text-xs text-studio-text-muted mt-0.5">
                    Review and edit below, then confirm to save
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => { setParsedContacts(null); setSaveResult(null); }}
                    className="btn-ghost flex items-center gap-1.5"
                  >
                    <X size={12} /> Start over
                  </button>
                  {parsedContacts.filter(c => c.uncertain).length > 0 && (
                    <span className="flex items-center gap-1 text-[11px] text-amber-400">
                      <AlertCircle size={11} />
                      {parsedContacts.filter(c => c.uncertain).length} need a category
                    </span>
                  )}
                  <button
                    onClick={handleConfirm}
                    disabled={saving || parsedContacts.length === 0}
                    className="btn-primary flex items-center gap-2"
                  >
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
                {parsedContacts.map((c, i) => (
                  <ParsedPreviewCard key={i} contact={c} index={i} onChange={updateParsed} onRemove={removeParsed} />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── List Tabs ── */}
      {tab !== "add" && (
        <div>
          {/* Search + stats */}
          <div className="flex items-center gap-3 mb-4">
            <div className="relative flex-1">
              <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-studio-text-muted pointer-events-none" />
              <input
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder="Search by name, organisation, location..."
                className="w-full pl-8 pr-3 py-2 bg-studio-surface border border-studio-border rounded text-xs text-studio-text placeholder:text-studio-text-muted/50 focus:outline-none focus:border-studio-accent"
              />
              {query && (
                <button onClick={() => setQuery("")}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-studio-text-muted hover:text-studio-text">
                  <X size={12} />
                </button>
              )}
            </div>
            {missingEmail > 0 && (
              <span className="flex items-center gap-1 text-[10px] text-amber-400/80 whitespace-nowrap">
                <AlertCircle size={11} />
                {missingEmail} missing email
              </span>
            )}
          </div>

          {/* Per-category paste panel (shown when not on All) */}
          {(["curators","journalists","institutions","collectors","corporations"] as Tab[]).includes(tab) && (
            <CategoryPastePanel
              key={tab}
              category={tab}
              label={TABS.find(t => t.id === tab)?.label ?? tab}
              mutate={mutateAll}
            />
          )}

          {visibleContacts.length === 0 && (
            <div className="text-center py-16 text-studio-text-muted">
              <Users size={32} strokeWidth={1} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">No contacts yet</p>
              <p className="text-xs mt-1 opacity-60">Use "Add Contact" tab or "Scan Web" to populate</p>
            </div>
          )}

          <div className="grid grid-cols-1 gap-3">
            {visibleContacts.map(c => <ContactCard key={`${c.category}-${c.id}`} contact={c} />)}
          </div>
        </div>
      )}
    </div>
  );
}
