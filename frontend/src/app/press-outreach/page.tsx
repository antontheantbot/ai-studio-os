// @ts-nocheck
"use client";
import { useState, useMemo, useEffect, useRef, useCallback } from "react";

const STORAGE_KEY = "press-outreach-contacts-v1";

const INITIAL_CONTACTS = [
  {
    id: 1,
    name: "Allyson Shiffman",
    title: "Features Editor",
    publication: "Vogue Scandinavia",
    tier: "TIER 1",
    category: "Fashion & Culture",
    email: "allyson@voguescandinavia.com",
    pitchDate: "2026-03-06",
    followUpDate: "2026-03-13",
    status: "PITCHED",
    notes: "Pitched The Wild Within series. Referenced Christie's, Sotheby's, Francisco Carolinum, Albanian Biennial 2024, Dubai solo show (featured Vogue Arabia), upcoming NYC 2026.",
    pitchSubject: "Ryan Koopmans & Alice Wexell — The Wild Within",
  },
];

const TIERS = ["TIER 1", "TIER 2", "TIER 3"];
const STATUSES = ["NOT CONTACTED", "PITCHED", "FOLLOWED UP", "IN CONVERSATION", "CONFIRMED", "PASSED"];
const CATEGORIES = ["Fashion & Culture", "Contemporary Art", "Architecture", "Luxury & Lifestyle", "Scandinavian Press", "International Art", "Photography", "Digital Art"];

const STATUS_COLORS = {
  "NOT CONTACTED": "#555",
  "PITCHED": "#c9a84c",
  "FOLLOWED UP": "#e8b84b",
  "IN CONVERSATION": "#7eb8a4",
  "CONFIRMED": "#5aaa82",
  "PASSED": "#774444",
};

const TIER_COLORS = {
  "TIER 1": "#c9a84c",
  "TIER 2": "#8a8a8a",
  "TIER 3": "#555",
};

const PITCH_TEMPLATES = [
  {
    label: "Initial Pitch",
    subject: "Ryan Koopmans & Alice Wexell — The Wild Within",
    body: `Dear [NAME],

I'm reaching out on behalf of Ryan Koopmans and Alice Wexell, whose collaborative series The Wild Within has garnered international recognition across Christie's, Sotheby's, and major institutions including Francisco Carolinum and the Albanian Biennial 2024.

Following a critically acclaimed solo presentation in Dubai (covered by Vogue Arabia), Ryan and Alice are bringing The Wild Within to New York in 2026 — and I'd love to explore coverage in [PUBLICATION].

The work sits at the intersection of landscape, technology, and the sublime — a natural fit for your readership.

Would you be open to a preview or studio conversation?

Warm regards`,
  },
  {
    label: "Follow-up",
    subject: "Following up — Ryan Koopmans & Alice Wexell",
    body: `Dear [NAME],

I wanted to follow up on my note from [DATE] regarding Ryan Koopmans and Alice Wexell's The Wild Within.

With the NYC debut approaching in 2026, we're now confirming editorial partnerships and I wanted to make sure this crossed your desk at the right moment.

Happy to send high-resolution imagery, press materials, or arrange a conversation with the artists directly.

Best`,
  },
  {
    label: "NYC Show Announcement",
    subject: "Exhibition Preview — The Wild Within, New York 2026",
    body: `Dear [NAME],

We're pleased to announce that Ryan Koopmans and Alice Wexell will present The Wild Within in New York in 2026.

The series — which has been exhibited at Francisco Carolinum, the Albanian Biennial, and presented at Christie's and Sotheby's — arrives in New York following its Dubai debut, which was featured in Vogue Arabia.

We would be delighted to offer [PUBLICATION] an exclusive preview opportunity. Please let me know if you'd like press materials or to schedule time with the artists.`,
  },
];

// Defined at module scope so all components can reference it
const inputStyle = {
  width: "100%",
  background: "#0a0a0a",
  border: "1px solid #2a2a2a",
  color: "#e0d4b0",
  padding: "10px 12px",
  fontFamily: "'Courier New', monospace",
  fontSize: "12px",
  outline: "none",
  boxSizing: "border-box",
};

function getToday() {
  return new Date().toISOString().split("T")[0];
}

function getDaysUntil(dateStr, today) {
  if (!dateStr || !today) return null;
  return Math.ceil((new Date(dateStr) - new Date(today)) / (1000 * 60 * 60 * 24));
}

function useLocalStorage(key, fallback) {
  const [value, setValue] = useState(() => {
    try {
      const stored = localStorage.getItem(key);
      return stored ? JSON.parse(stored) : fallback;
    } catch {
      return fallback;
    }
  });

  const set = useCallback((v) => {
    setValue(prev => {
      const next = typeof v === "function" ? v(prev) : v;
      try { localStorage.setItem(key, JSON.stringify(next)); } catch {}
      return next;
    });
  }, [key]);

  return [value, set];
}

function Badge({ label, color, small }) {
  return (
    <span style={{
      display: "inline-block",
      padding: small ? "2px 8px" : "3px 10px",
      borderRadius: "2px",
      border: `1px solid ${color}`,
      color,
      fontSize: small ? "9px" : "10px",
      fontFamily: "'Courier New', monospace",
      letterSpacing: "0.12em",
      fontWeight: "600",
      whiteSpace: "nowrap",
    }}>{label}</span>
  );
}

function Toast({ message, onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 2200);
    return () => clearTimeout(t);
  }, [onDone]);
  return (
    <div style={{
      position: "fixed", bottom: "32px", left: "50%", transform: "translateX(-50%)",
      background: "#1a1a0e", border: "1px solid #c9a84c", color: "#e8d9a0",
      padding: "10px 24px", fontSize: "11px", fontFamily: "'Courier New', monospace",
      letterSpacing: "0.12em", zIndex: 600, boxShadow: "0 8px 32px rgba(0,0,0,0.8)",
      animation: "fadeSlideUp 0.25s ease", pointerEvents: "none",
    }}>{message}</div>
  );
}

function AlertBanner({ contacts, today }) {
  const overdue = contacts.filter(c => {
    const d = getDaysUntil(c.followUpDate, today);
    return d !== null && d < 0 && c.status !== "CONFIRMED" && c.status !== "PASSED";
  });
  const urgent = contacts.filter(c => {
    const d = getDaysUntil(c.followUpDate, today);
    return d !== null && d >= 0 && d <= 7 && c.status !== "CONFIRMED" && c.status !== "PASSED";
  });
  if (!overdue.length && !urgent.length) return null;
  return (
    <div style={{ marginBottom: "24px", display: "flex", flexDirection: "column", gap: "8px" }}>
      {overdue.length > 0 && (
        <div style={{ background: "linear-gradient(90deg,#1a0808,#0e0e0e)", border: "1px solid #774444", borderLeft: "3px solid #aa5555", padding: "12px 20px", display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap" }}>
          <span style={{ color: "#aa5555", fontSize: "10px", letterSpacing: "0.15em", fontFamily: "'Courier New', monospace", fontWeight: "700" }}>⚠ OVERDUE</span>
          {overdue.map(c => (
            <span key={c.id} style={{ color: "#cc8888", fontSize: "12px", fontFamily: "'Courier New', monospace" }}>
              {c.name} ({c.publication}) — {Math.abs(getDaysUntil(c.followUpDate, today))}d ago
            </span>
          ))}
        </div>
      )}
      {urgent.length > 0 && (
        <div style={{ background: "linear-gradient(90deg,#1a1200,#0e0e0e)", border: "1px solid #c9a84c", borderLeft: "3px solid #c9a84c", padding: "12px 20px", display: "flex", alignItems: "center", gap: "16px", flexWrap: "wrap" }}>
          <span style={{ color: "#c9a84c", fontSize: "10px", letterSpacing: "0.15em", fontFamily: "'Courier New', monospace", fontWeight: "700" }}>⚡ FOLLOW-UP DUE</span>
          {urgent.map(c => {
            const d = getDaysUntil(c.followUpDate, today);
            return (
              <span key={c.id} style={{ color: "#e8d9a0", fontSize: "12px", fontFamily: "'Courier New', monospace" }}>
                {c.name} ({c.publication}) — {d === 0 ? "TODAY" : `in ${d}d`}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value, accent, sublabel }) {
  return (
    <div style={{ background: "#0e0e0e", border: "1px solid #222", padding: "16px 20px", flex: "1", minWidth: "120px" }}>
      <div style={{ color: accent || "#c9a84c", fontSize: "26px", fontFamily: "'Playfair Display', Georgia, serif", fontWeight: "700", lineHeight: 1 }}>{value}</div>
      <div style={{ color: "#555", fontSize: "9px", letterSpacing: "0.15em", fontFamily: "'Courier New', monospace", marginTop: "6px", textTransform: "uppercase" }}>{label}</div>
      {sublabel && <div style={{ color: "#3a3a3a", fontSize: "9px", fontFamily: "'Courier New', monospace", marginTop: "3px" }}>{sublabel}</div>}
    </div>
  );
}

function StatusDropdown({ contact, onUpdate }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    if (!open) return;
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  return (
    <div ref={ref} style={{ position: "relative", display: "inline-block" }}>
      <span
        onClick={e => { e.stopPropagation(); setOpen(o => !o); }}
        title="Click to change status"
        style={{
          display: "inline-block", padding: "2px 8px", borderRadius: "2px",
          border: `1px solid ${STATUS_COLORS[contact.status]}`,
          color: STATUS_COLORS[contact.status],
          fontSize: "9px", fontFamily: "'Courier New', monospace",
          letterSpacing: "0.12em", fontWeight: "600",
          whiteSpace: "nowrap", cursor: "pointer", userSelect: "none",
        }}
      >
        {contact.status} ▾
      </span>
      {open && (
        <div style={{ position: "absolute", top: "calc(100% + 4px)", left: 0, background: "#111", border: "1px solid #2a2a2a", zIndex: 400, minWidth: "170px", boxShadow: "0 8px 32px rgba(0,0,0,0.9)" }}>
          {STATUSES.map(s => (
            <div
              key={s}
              onClick={e => { e.stopPropagation(); onUpdate({ ...contact, status: s }); setOpen(false); }}
              style={{ padding: "9px 14px", fontSize: "10px", fontFamily: "'Courier New', monospace", letterSpacing: "0.1em", color: STATUS_COLORS[s], cursor: "pointer", background: s === contact.status ? "#1a1a1a" : "transparent", borderBottom: "1px solid #1a1a1a" }}
              onMouseEnter={e => e.currentTarget.style.background = "#1e1e1e"}
              onMouseLeave={e => e.currentTarget.style.background = s === contact.status ? "#1a1a1a" : "transparent"}
            >
              {s === contact.status ? "✓ " : "  "}{s}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function SortHeader({ label, sortKey, currentSort, onSort }) {
  const active = currentSort.key === sortKey;
  return (
    <th onClick={() => onSort(sortKey)} style={{ padding: "10px 16px", textAlign: "left", color: active ? "#c9a84c" : "#444", fontSize: "9px", letterSpacing: "0.15em", fontFamily: "'Courier New', monospace", fontWeight: "600", cursor: "pointer", userSelect: "none", whiteSpace: "nowrap" }}>
      {label}{active && <span style={{ marginLeft: "4px" }}>{currentSort.dir === "asc" ? "↑" : "↓"}</span>}
    </th>
  );
}

function ContactRow({ contact, onEdit, onSelect, isSelected, onStatusUpdate, today }) {
  const days = getDaysUntil(contact.followUpDate, today);
  const isUrgent = days !== null && days >= 0 && days <= 7;
  const isOverdue = days !== null && days < 0;

  return (
    <tr
      onClick={() => onSelect(contact)}
      style={{ cursor: "pointer", background: isSelected ? "#141209" : "transparent", borderBottom: "1px solid #1a1a1a", transition: "background 0.15s" }}
      onMouseEnter={e => { if (!isSelected) e.currentTarget.style.background = "#111"; }}
      onMouseLeave={e => { if (!isSelected) e.currentTarget.style.background = "transparent"; }}
    >
      <td style={{ padding: "14px 16px", verticalAlign: "middle" }}>
        <div style={{ color: "#f0e6c8", fontSize: "13px", fontFamily: "'Playfair Display', Georgia, serif", fontWeight: "600" }}>{contact.name}</div>
        <div style={{ color: "#666", fontSize: "11px", fontFamily: "'Courier New', monospace", marginTop: "2px" }}>{contact.title}</div>
      </td>
      <td style={{ padding: "14px 16px", verticalAlign: "middle" }}>
        <div style={{ color: "#c9a84c", fontSize: "12px", fontFamily: "'Courier New', monospace", fontWeight: "600" }}>{contact.publication}</div>
        <div style={{ color: "#555", fontSize: "10px", fontFamily: "'Courier New', monospace", marginTop: "2px" }}>{contact.category}</div>
      </td>
      <td style={{ padding: "14px 16px", verticalAlign: "middle" }}>
        <Badge label={contact.tier} color={TIER_COLORS[contact.tier]} small />
      </td>
      <td style={{ padding: "14px 16px", verticalAlign: "middle" }} onClick={e => e.stopPropagation()}>
        <StatusDropdown contact={contact} onUpdate={onStatusUpdate} />
      </td>
      <td style={{ padding: "14px 16px", verticalAlign: "middle" }}>
        {contact.followUpDate ? (
          <span style={{ color: isOverdue ? "#aa5555" : isUrgent ? "#e8b84b" : "#555", fontSize: "11px", fontFamily: "'Courier New', monospace", fontWeight: (isUrgent || isOverdue) ? "700" : "400" }}>
            {contact.followUpDate}
            {isUrgent && <span style={{ marginLeft: "6px", fontSize: "9px" }}>⚡{days === 0 ? "TODAY" : `${days}d`}</span>}
            {isOverdue && <span style={{ marginLeft: "6px", fontSize: "9px" }}>⚠ {Math.abs(days)}d ago</span>}
          </span>
        ) : <span style={{ color: "#333", fontSize: "11px", fontFamily: "'Courier New', monospace" }}>—</span>}
      </td>
      <td style={{ padding: "14px 16px", verticalAlign: "middle" }}>
        <button
          onClick={e => { e.stopPropagation(); onEdit(contact); }}
          style={{ background: "transparent", border: "1px solid #333", color: "#888", fontSize: "10px", padding: "4px 10px", cursor: "pointer", fontFamily: "'Courier New', monospace", letterSpacing: "0.1em" }}
        >EDIT</button>
      </td>
    </tr>
  );
}

function DetailPanel({ contact, onClose, onEdit }) {
  if (!contact) return null;
  return (
    <div style={{ position: "fixed", right: 0, top: 0, bottom: 0, width: "400px", background: "#0a0a0a", borderLeft: "1px solid #222", padding: "32px 28px", overflowY: "auto", zIndex: 100, boxShadow: "-20px 0 60px rgba(0,0,0,0.8)" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "28px" }}>
        <div>
          <div style={{ color: "#555", fontSize: "9px", letterSpacing: "0.2em", fontFamily: "'Courier New', monospace", marginBottom: "6px" }}>CONTACT RECORD</div>
          <div style={{ color: "#f0e6c8", fontSize: "20px", fontFamily: "'Playfair Display', Georgia, serif", fontWeight: "700", lineHeight: 1.2 }}>{contact.name}</div>
          <div style={{ color: "#c9a84c", fontSize: "12px", fontFamily: "'Courier New', monospace", marginTop: "4px" }}>{contact.publication}</div>
        </div>
        <button onClick={onClose} style={{ background: "transparent", border: "none", color: "#555", cursor: "pointer", fontSize: "20px", lineHeight: 1, padding: "0" }}>×</button>
      </div>
      <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", marginBottom: "24px" }}>
        <Badge label={contact.tier} color={TIER_COLORS[contact.tier]} />
        <Badge label={contact.status} color={STATUS_COLORS[contact.status]} />
        <Badge label={contact.category} color="#444" />
      </div>
      {[["Title", contact.title], ["Email", contact.email], ["Pitch Date", contact.pitchDate], ["Follow-up Due", contact.followUpDate], ["Subject Line", contact.pitchSubject]].map(([label, val]) => val ? (
        <div key={label} style={{ marginBottom: "16px", borderBottom: "1px solid #151515", paddingBottom: "16px" }}>
          <div style={{ color: "#555", fontSize: "9px", letterSpacing: "0.15em", fontFamily: "'Courier New', monospace", marginBottom: "4px" }}>{label.toUpperCase()}</div>
          <div style={{ color: "#aaa", fontSize: "12px", fontFamily: "'Courier New', monospace", lineHeight: 1.5 }}>{val}</div>
        </div>
      ) : null)}
      {contact.notes && (
        <div style={{ marginBottom: "24px" }}>
          <div style={{ color: "#555", fontSize: "9px", letterSpacing: "0.15em", fontFamily: "'Courier New', monospace", marginBottom: "8px" }}>PITCH NOTES</div>
          <div style={{ color: "#888", fontSize: "12px", fontFamily: "'Courier New', monospace", lineHeight: 1.7, background: "#0d0d0d", padding: "14px", border: "1px solid #1a1a1a" }}>{contact.notes}</div>
        </div>
      )}
      <button onClick={() => onEdit(contact)} style={{ width: "100%", background: "transparent", border: "1px solid #c9a84c", color: "#c9a84c", padding: "12px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "11px", letterSpacing: "0.15em", fontWeight: "600" }}>EDIT RECORD</button>
    </div>
  );
}

function Modal({ title, onClose, children, wide }) {
  const handleBackdrop = (e) => { if (e.target === e.currentTarget) onClose(); };
  return (
    <div onClick={handleBackdrop} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.85)", zIndex: 200, display: "flex", alignItems: "center", justifyContent: "center", padding: "20px" }}>
      <div style={{ background: "#0e0e0e", border: "1px solid #2a2a2a", width: "100%", maxWidth: wide ? "780px" : "580px", padding: "32px", maxHeight: "90vh", overflowY: "auto", boxShadow: "0 40px 100px rgba(0,0,0,0.9)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "28px" }}>
          <div style={{ color: "#f0e6c8", fontSize: "16px", fontFamily: "'Playfair Display', Georgia, serif", fontWeight: "700" }}>{title}</div>
          <button onClick={onClose} style={{ background: "transparent", border: "none", color: "#555", cursor: "pointer", fontSize: "20px", lineHeight: 1, padding: "0" }}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: "18px" }}>
      <label style={{ display: "block", color: "#555", fontSize: "9px", letterSpacing: "0.15em", fontFamily: "'Courier New', monospace", marginBottom: "6px" }}>{label}</label>
      {children}
    </div>
  );
}

function ContactForm({ initial, onSave, onClose, onDelete }) {
  const empty = { name: "", title: "", publication: "", tier: "TIER 1", category: "Contemporary Art", email: "", pitchDate: "", followUpDate: "", status: "NOT CONTACTED", notes: "", pitchSubject: "" };
  const [form, setForm] = useState(initial ? { ...initial } : empty);
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 16px" }}>
        <Field label="FULL NAME"><input style={inputStyle} value={form.name} onChange={e => set("name", e.target.value)} /></Field>
        <Field label="TITLE / ROLE"><input style={inputStyle} value={form.title} onChange={e => set("title", e.target.value)} /></Field>
        <Field label="PUBLICATION"><input style={inputStyle} value={form.publication} onChange={e => set("publication", e.target.value)} /></Field>
        <Field label="EMAIL"><input style={inputStyle} value={form.email} onChange={e => set("email", e.target.value)} /></Field>
        <Field label="TIER">
          <select style={inputStyle} value={form.tier} onChange={e => set("tier", e.target.value)}>
            {TIERS.map(t => <option key={t}>{t}</option>)}
          </select>
        </Field>
        <Field label="CATEGORY">
          <select style={inputStyle} value={form.category} onChange={e => set("category", e.target.value)}>
            {CATEGORIES.map(c => <option key={c}>{c}</option>)}
          </select>
        </Field>
        <Field label="STATUS">
          <select style={inputStyle} value={form.status} onChange={e => set("status", e.target.value)}>
            {STATUSES.map(s => <option key={s}>{s}</option>)}
          </select>
        </Field>
        <Field label="PITCH DATE"><input type="date" style={inputStyle} value={form.pitchDate} onChange={e => set("pitchDate", e.target.value)} /></Field>
        <Field label="FOLLOW-UP DATE"><input type="date" style={inputStyle} value={form.followUpDate} onChange={e => set("followUpDate", e.target.value)} /></Field>
        <Field label="PITCH SUBJECT LINE"><input style={inputStyle} value={form.pitchSubject} onChange={e => set("pitchSubject", e.target.value)} /></Field>
      </div>
      <Field label="PITCH NOTES">
        <textarea style={{ ...inputStyle, height: "100px", resize: "vertical" }} value={form.notes} onChange={e => set("notes", e.target.value)} />
      </Field>
      <div style={{ display: "flex", gap: "10px", justifyContent: "space-between", marginTop: "8px" }}>
        {onDelete && (
          <button
            onClick={() => { if (window.confirm("Delete this contact? This cannot be undone.")) onDelete(form.id); }}
            style={{ background: "transparent", border: "1px solid #774444", color: "#aa5555", padding: "10px 16px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "10px", letterSpacing: "0.1em" }}
          >DELETE</button>
        )}
        <div style={{ display: "flex", gap: "10px", marginLeft: "auto" }}>
          <button onClick={onClose} style={{ background: "transparent", border: "1px solid #333", color: "#666", padding: "10px 20px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "10px", letterSpacing: "0.1em" }}>CANCEL</button>
          <button onClick={() => onSave(form)} style={{ background: "#c9a84c", border: "none", color: "#000", padding: "10px 24px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "10px", letterSpacing: "0.1em", fontWeight: "700" }}>SAVE RECORD</button>
        </div>
      </div>
    </div>
  );
}

function TemplatesModal() {
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [copied, setCopied] = useState(null);

  const copy = (text, label) => {
    const fallback = () => {
      const ta = document.createElement("textarea");
      ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select(); document.execCommand("copy"); document.body.removeChild(ta);
      setCopied(label); setTimeout(() => setCopied(null), 1800);
    };
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => { setCopied(label); setTimeout(() => setCopied(null), 1800); }).catch(fallback);
    } else { fallback(); }
  };

  const tpl = PITCH_TEMPLATES[selectedIdx];

  return (
    <div>
      <div style={{ display: "flex", gap: "8px", marginBottom: "24px", flexWrap: "wrap" }}>
        {PITCH_TEMPLATES.map((t, i) => (
          <button key={i} onClick={() => setSelectedIdx(i)} style={{ background: selectedIdx === i ? "#c9a84c" : "transparent", border: `1px solid ${selectedIdx === i ? "#c9a84c" : "#333"}`, color: selectedIdx === i ? "#000" : "#888", padding: "8px 16px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "10px", letterSpacing: "0.1em", fontWeight: selectedIdx === i ? "700" : "400" }}>{t.label}</button>
        ))}
      </div>
      <div style={{ marginBottom: "16px" }}>
        <div style={{ color: "#555", fontSize: "9px", letterSpacing: "0.15em", fontFamily: "'Courier New', monospace", marginBottom: "6px" }}>SUBJECT LINE</div>
        <div style={{ background: "#0a0a0a", border: "1px solid #1a1a1a", padding: "10px 14px", color: "#c9a84c", fontSize: "12px", fontFamily: "'Courier New', monospace", display: "flex", justifyContent: "space-between", alignItems: "center", gap: "12px" }}>
          <span>{tpl.subject}</span>
          <button onClick={() => copy(tpl.subject, "subject")} style={{ background: "transparent", border: "1px solid #333", color: copied === "subject" ? "#5aaa82" : "#666", padding: "4px 10px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "9px", whiteSpace: "nowrap" }}>{copied === "subject" ? "✓ COPIED" : "COPY"}</button>
        </div>
      </div>
      <div style={{ marginBottom: "20px" }}>
        <div style={{ color: "#555", fontSize: "9px", letterSpacing: "0.15em", fontFamily: "'Courier New', monospace", marginBottom: "6px" }}>BODY</div>
        <div style={{ position: "relative" }}>
          <textarea readOnly value={tpl.body} style={{ ...inputStyle, height: "260px", resize: "none", color: "#888", lineHeight: 1.7 }} />
          <button onClick={() => copy(tpl.body, "body")} style={{ position: "absolute", top: "10px", right: "10px", background: "#0e0e0e", border: "1px solid #333", color: copied === "body" ? "#5aaa82" : "#666", padding: "5px 12px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "9px", letterSpacing: "0.1em" }}>{copied === "body" ? "✓ COPIED" : "COPY BODY"}</button>
        </div>
      </div>
      <div style={{ color: "#333", fontSize: "10px", fontFamily: "'Courier New', monospace" }}>Replace [NAME], [PUBLICATION], [DATE] with contact-specific details before sending.</div>
    </div>
  );
}

function ExportModal({ contacts, onClose, today }) {
  const [copied, setCopied] = useState(false);

  const buildCSV = () => {
    const rows = [
      ["Name", "Title", "Publication", "Category", "Tier", "Status", "Email", "Pitch Date", "Follow-up Date", "Subject", "Notes"],
      ...contacts.map(c => [c.name, c.title, c.publication, c.category, c.tier, c.status, c.email, c.pitchDate, c.followUpDate, c.pitchSubject, (c.notes || "").replace(/\n/g, " ")]),
    ];
    return rows.map(row => row.map(cell => `"${(cell || "").replace(/"/g, '""')}"`).join(",")).join("\n");
  };

  const downloadCSV = () => {
    const a = document.createElement("a");
    a.href = "data:text/csv;charset=utf-8," + encodeURIComponent(buildCSV());
    a.download = `press-outreach-${today}.csv`;
    document.body.appendChild(a); a.click(); document.body.removeChild(a);
  };

  const copyCSV = () => {
    const csv = buildCSV();
    const fallback = () => {
      const ta = document.createElement("textarea"); ta.value = csv; ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select(); document.execCommand("copy"); document.body.removeChild(ta);
      setCopied(true); setTimeout(() => setCopied(false), 1800);
    };
    if (navigator.clipboard) { navigator.clipboard.writeText(csv).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1800); }).catch(fallback); } else { fallback(); }
  };

  return (
    <div>
      <div style={{ marginBottom: "20px", color: "#666", fontSize: "12px", fontFamily: "'Courier New', monospace", lineHeight: 1.6 }}>
        Export {contacts.length} contact{contacts.length !== 1 ? "s" : ""} as CSV — compatible with Excel, Google Sheets, and most CRM tools.
      </div>
      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap" }}>
        <button onClick={downloadCSV} style={{ background: "#c9a84c", border: "none", color: "#000", padding: "12px 24px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "11px", letterSpacing: "0.12em", fontWeight: "700" }}>↓ DOWNLOAD CSV</button>
        <button onClick={copyCSV} style={{ background: "transparent", border: "1px solid #333", color: copied ? "#5aaa82" : "#888", padding: "12px 20px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "11px", letterSpacing: "0.1em" }}>{copied ? "✓ COPIED" : "COPY TO CLIPBOARD"}</button>
        <button onClick={onClose} style={{ background: "transparent", border: "1px solid #333", color: "#666", padding: "12px 20px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "11px", letterSpacing: "0.1em", marginLeft: "auto" }}>CLOSE</button>
      </div>
    </div>
  );
}

function ImportModal({ onImport, onClose }) {
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const fileRef = useRef(null);

  const parseCSV = (raw) => {
    const lines = raw.trim().split("\n").filter(l => l.trim());
    if (lines.length < 2) throw new Error("CSV must have a header row and at least one data row.");

    const parseRow = (line) => {
      const cells = []; let cur = "", inQ = false;
      for (const ch of line) {
        if (ch === '"') { inQ = !inQ; }
        else if (ch === ',' && !inQ) { cells.push(cur.trim()); cur = ""; }
        else { cur += ch; }
      }
      cells.push(cur.trim());
      return cells;
    };

    const normalise = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, "");
    const headers = parseRow(lines[0]).map(normalise);
    const colFor = (...aliases) => { for (const a of aliases) { const i = headers.indexOf(normalise(a)); if (i !== -1) return i; } return -1; };

    const cols = {
      name: colFor("name", "fullname"),
      title: colFor("title", "role", "titlerole"),
      publication: colFor("publication"),
      category: colFor("category"),
      tier: colFor("tier"),
      status: colFor("status"),
      email: colFor("email"),
      pitchDate: colFor("pitchdate", "pitchdate", "pitched"),
      followUpDate: colFor("followupdate", "followup", "followupdue", "followupdate"),
      pitchSubject: colFor("subject", "pitchsubject", "pitchsubjectline"),
      notes: colFor("notes", "pitchnotes"),
    };

    if (cols.name === -1) throw new Error("Could not find a 'Name' column in the CSV header.");

    return lines.slice(1).map(line => {
      const cells = parseRow(line);
      const get = (col) => col !== -1 ? (cells[col] || "") : "";
      return {
        id: Date.now() + Math.random(),
        name: get(cols.name),
        title: get(cols.title),
        publication: get(cols.publication),
        category: CATEGORIES.includes(get(cols.category)) ? get(cols.category) : "Contemporary Art",
        tier: TIERS.includes(get(cols.tier)) ? get(cols.tier) : "TIER 3",
        status: STATUSES.includes(get(cols.status)) ? get(cols.status) : "NOT CONTACTED",
        email: get(cols.email),
        pitchDate: get(cols.pitchDate),
        followUpDate: get(cols.followUpDate),
        pitchSubject: get(cols.pitchSubject),
        notes: get(cols.notes),
      };
    }).filter(c => c.name.trim());
  };

  const handleFile = (e) => {
    const file = e.target.files[0]; if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => { setText(ev.target.result); setError(""); };
    reader.readAsText(file);
    e.target.value = ""; // allow re-selecting same file
  };

  const handleImport = () => {
    setError("");
    try {
      const imported = parseCSV(text);
      if (!imported.length) throw new Error("No valid contacts found in the CSV.");
      onImport(imported);
    } catch (e) { setError(e.message); }
  };

  return (
    <div>
      <div style={{ marginBottom: "16px", color: "#666", fontSize: "12px", fontFamily: "'Courier New', monospace", lineHeight: 1.6 }}>
        Import contacts from a CSV. Include a header row with columns: Name, Title, Publication, Email, Tier, Status, Follow-up Date, etc.
      </div>
      <div style={{ marginBottom: "16px", display: "flex", gap: "10px", alignItems: "center" }}>
        <button onClick={() => fileRef.current?.click()} style={{ background: "transparent", border: "1px solid #333", color: "#888", padding: "10px 18px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "10px", letterSpacing: "0.1em" }}>SELECT FILE</button>
        <input ref={fileRef} type="file" accept=".csv,.txt" onChange={handleFile} style={{ display: "none" }} />
        <span style={{ color: "#444", fontSize: "11px", fontFamily: "'Courier New', monospace" }}>or paste CSV below</span>
      </div>
      <Field label="CSV CONTENT">
        <textarea
          style={{ ...inputStyle, height: "200px", resize: "vertical", lineHeight: 1.5, fontSize: "11px" }}
          value={text}
          onChange={e => { setText(e.target.value); setError(""); }}
          placeholder={"Name,Title,Publication,Email,Tier,Status\nJane Smith,Editor,Vogue,jane@vogue.com,TIER 1,NOT CONTACTED"}
        />
      </Field>
      {error && <div style={{ color: "#aa5555", fontSize: "11px", fontFamily: "'Courier New', monospace", marginBottom: "12px" }}>⚠ {error}</div>}
      <div style={{ display: "flex", gap: "10px", justifyContent: "flex-end" }}>
        <button onClick={onClose} style={{ background: "transparent", border: "1px solid #333", color: "#666", padding: "10px 20px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "10px", letterSpacing: "0.1em" }}>CANCEL</button>
        <button
          onClick={handleImport}
          disabled={!text.trim()}
          style={{ background: text.trim() ? "#c9a84c" : "#2a2a1a", border: "none", color: text.trim() ? "#000" : "#555", padding: "10px 24px", cursor: text.trim() ? "pointer" : "default", fontFamily: "'Courier New', monospace", fontSize: "10px", letterSpacing: "0.1em", fontWeight: "700" }}
        >IMPORT CONTACTS</button>
      </div>
    </div>
  );
}

export default function PressOutreachPage() {
  // Reactive date — refreshes every minute so overdue states stay accurate
  const [today, setToday] = useState(getToday);
  useEffect(() => {
    const id = setInterval(() => setToday(getToday()), 60000);
    return () => clearInterval(id);
  }, []);

  const [contacts, setContacts] = useLocalStorage(STORAGE_KEY, INITIAL_CONTACTS);
  const [selected, setSelected] = useState(null);
  const [editing, setEditing] = useState(null);
  const [adding, setAdding] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showExport, setShowExport] = useState(false);
  const [showImport, setShowImport] = useState(false);
  const [filterStatus, setFilterStatus] = useState("ALL");
  const [filterTier, setFilterTier] = useState("ALL");
  const [filterCategory, setFilterCategory] = useState("ALL");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState({ key: "followUpDate", dir: "asc" });
  const [toast, setToast] = useState(null);

  const showToast = useCallback((msg) => setToast(msg), []);

  const handleSort = (key) => setSort(s => s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: "asc" });

  const sorted = useMemo(() => {
    const TIER_ORDER = { "TIER 1": 0, "TIER 2": 1, "TIER 3": 2 };
    const STATUS_ORDER = { "IN CONVERSATION": 0, "FOLLOWED UP": 1, "PITCHED": 2, "NOT CONTACTED": 3, "CONFIRMED": 4, "PASSED": 5 };
    return [...contacts].sort((a, b) => {
      const dir = sort.dir === "asc" ? 1 : -1;
      const k = sort.key;
      if (k === "tier") return dir * ((TIER_ORDER[a.tier] ?? 9) - (TIER_ORDER[b.tier] ?? 9));
      if (k === "status") return dir * ((STATUS_ORDER[a.status] ?? 9) - (STATUS_ORDER[b.status] ?? 9));
      if (k === "followUpDate" || k === "pitchDate") {
        if (!a[k] && !b[k]) return 0; if (!a[k]) return 1; if (!b[k]) return -1;
        return dir * a[k].localeCompare(b[k]);
      }
      return dir * (a[k] || "").localeCompare(b[k] || "");
    });
  }, [contacts, sort]);

  const filtered = useMemo(() => sorted.filter(c => {
    if (filterStatus !== "ALL" && c.status !== filterStatus) return false;
    if (filterTier !== "ALL" && c.tier !== filterTier) return false;
    if (filterCategory !== "ALL" && c.category !== filterCategory) return false;
    if (search) {
      const hay = [c.name, c.publication, c.title, c.category, c.notes, c.pitchSubject, c.email].join(" ").toLowerCase();
      if (!hay.includes(search.toLowerCase())) return false;
    }
    return true;
  }), [sorted, filterStatus, filterTier, filterCategory, search]);

  const stats = useMemo(() => ({
    total: contacts.length,
    tier1: contacts.filter(c => c.tier === "TIER 1").length,
    pitched: contacts.filter(c => c.status === "PITCHED").length,
    followedUp: contacts.filter(c => c.status === "FOLLOWED UP").length,
    inConversation: contacts.filter(c => c.status === "IN CONVERSATION").length,
    confirmed: contacts.filter(c => c.status === "CONFIRMED").length,
    urgent: contacts.filter(c => { const d = getDaysUntil(c.followUpDate, today); return d !== null && d >= 0 && d <= 7 && c.status !== "CONFIRMED" && c.status !== "PASSED"; }).length,
    overdue: contacts.filter(c => { const d = getDaysUntil(c.followUpDate, today); return d !== null && d < 0 && c.status !== "CONFIRMED" && c.status !== "PASSED"; }).length,
  }), [contacts, today]);

  const saveContact = (form) => {
    if (form.id) {
      const updated = { ...form };
      setContacts(cs => cs.map(c => c.id === updated.id ? updated : c));
      setSelected(prev => prev?.id === updated.id ? updated : prev);
      showToast("Record updated");
    } else {
      setContacts(cs => [...cs, { ...form, id: Date.now() }]);
      showToast("Contact added");
    }
    setEditing(null); setAdding(false);
  };

  const deleteContact = (id) => {
    setContacts(cs => cs.filter(c => c.id !== id));
    setEditing(null);
    setSelected(prev => prev?.id === id ? null : prev);
    showToast("Contact deleted");
  };

  const updateStatus = useCallback((updated) => {
    setContacts(cs => cs.map(c => c.id === updated.id ? updated : c));
    setSelected(prev => prev?.id === updated.id ? updated : prev);
    showToast(`Status → ${updated.status}`);
  }, [setContacts, showToast]);

  const handleImport = (newContacts) => {
    setContacts(cs => [...cs, ...newContacts]);
    setShowImport(false);
    showToast(`Imported ${newContacts.length} contact${newContacts.length !== 1 ? "s" : ""}`);
  };

  const filtersActive = filterStatus !== "ALL" || filterTier !== "ALL" || filterCategory !== "ALL" || search;
  const clearFilters = () => { setFilterStatus("ALL"); setFilterTier("ALL"); setFilterCategory("ALL"); setSearch(""); };

  return (
    <div style={{ minHeight: "100vh", background: "#080808", color: "#e0d4b0", fontFamily: "'Courier New', monospace", paddingRight: selected ? "400px" : "0", transition: "padding-right 0.3s ease" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;900&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: #080808; }
        ::-webkit-scrollbar-thumb { background: #2a2a2a; }
        select option { background: #0e0e0e; color: #e0d4b0; }
        input[type="date"]::-webkit-calendar-picker-indicator { filter: invert(0.3); }
        @keyframes fadeSlideUp { from { opacity:0; transform:translateX(-50%) translateY(8px); } to { opacity:1; transform:translateX(-50%) translateY(0); } }
      `}</style>

      {/* Header */}
      <div style={{ borderBottom: "1px solid #1a1a1a", padding: "24px 40px 20px", background: "#080808", position: "sticky", top: 0, zIndex: 50 }}>
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <div style={{ color: "#444", fontSize: "9px", letterSpacing: "0.3em", fontFamily: "'Courier New', monospace", marginBottom: "4px" }}>RYAN KOOPMANS × ALICE WEXELL</div>
            <div style={{ color: "#f0e6c8", fontSize: "24px", fontFamily: "'Playfair Display', Georgia, serif", fontWeight: "900", letterSpacing: "0.02em", lineHeight: 1 }}>
              Press Outreach<span style={{ color: "#c9a84c" }}> Command</span>
            </div>
          </div>
          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            <button onClick={() => setShowTemplates(true)} style={{ background: "transparent", border: "1px solid #333", color: "#888", padding: "10px 16px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "10px", letterSpacing: "0.12em" }}>TEMPLATES</button>
            <button onClick={() => setShowImport(true)} style={{ background: "transparent", border: "1px solid #333", color: "#888", padding: "10px 16px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "10px", letterSpacing: "0.12em" }}>IMPORT</button>
            <button onClick={() => setShowExport(true)} style={{ background: "transparent", border: "1px solid #333", color: "#888", padding: "10px 16px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "10px", letterSpacing: "0.12em" }}>EXPORT</button>
            <button onClick={() => setAdding(true)} style={{ background: "#c9a84c", border: "none", color: "#000", padding: "10px 20px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "11px", letterSpacing: "0.15em", fontWeight: "700" }}>+ ADD CONTACT</button>
          </div>
        </div>
      </div>

      <div style={{ padding: "28px 40px" }}>
        <AlertBanner contacts={contacts} today={today} />

        {/* Stats */}
        <div style={{ display: "flex", gap: "8px", marginBottom: "28px", flexWrap: "wrap" }}>
          <StatCard label="Total Contacts" value={stats.total} />
          <StatCard label="Tier 1" value={stats.tier1} accent="#c9a84c" />
          <StatCard label="Pitched" value={stats.pitched} accent="#c9a84c" sublabel={stats.followedUp > 0 ? `+${stats.followedUp} followed up` : undefined} />
          <StatCard label="In Conversation" value={stats.inConversation} accent="#7eb8a4" />
          <StatCard label="Confirmed" value={stats.confirmed} accent="#5aaa82" />
          <StatCard label="Overdue / Due Soon" value={`${stats.overdue} / ${stats.urgent}`} accent={stats.overdue > 0 ? "#aa5555" : stats.urgent > 0 ? "#e8b84b" : "#555"} />
        </div>

        {/* Filters */}
        <div style={{ display: "flex", gap: "8px", marginBottom: "20px", flexWrap: "wrap", alignItems: "center" }}>
          <input placeholder="Search contacts, notes, subjects..." value={search} onChange={e => setSearch(e.target.value)} style={{ ...inputStyle, width: "260px", padding: "8px 12px", fontSize: "11px" }} />
          {[
            { val: filterStatus, set: setFilterStatus, opts: ["ALL", ...STATUSES] },
            { val: filterTier, set: setFilterTier, opts: ["ALL", ...TIERS] },
            { val: filterCategory, set: setFilterCategory, opts: ["ALL", ...CATEGORIES] },
          ].map(({ val, set, opts }, i) => (
            <select key={i} value={val} onChange={e => set(e.target.value)} style={{ ...inputStyle, width: "auto", padding: "8px 12px", fontSize: "10px" }}>
              {opts.map(o => <option key={o}>{o}</option>)}
            </select>
          ))}
          {filtersActive && (
            <button onClick={clearFilters} style={{ background: "transparent", border: "1px solid #333", color: "#666", padding: "8px 12px", cursor: "pointer", fontFamily: "'Courier New', monospace", fontSize: "9px", letterSpacing: "0.1em" }}>CLEAR</button>
          )}
          <span style={{ color: "#444", fontSize: "10px", marginLeft: "auto", fontFamily: "'Courier New', monospace" }}>
            {filtersActive ? `${filtered.length} of ${contacts.length}` : contacts.length} records
          </span>
        </div>

        {/* Table */}
        <div style={{ border: "1px solid #1a1a1a", overflow: "hidden" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #1a1a1a", background: "#0a0a0a" }}>
                <SortHeader label="CONTACT" sortKey="name" currentSort={sort} onSort={handleSort} />
                <SortHeader label="PUBLICATION" sortKey="publication" currentSort={sort} onSort={handleSort} />
                <SortHeader label="TIER" sortKey="tier" currentSort={sort} onSort={handleSort} />
                <SortHeader label="STATUS" sortKey="status" currentSort={sort} onSort={handleSort} />
                <SortHeader label="FOLLOW-UP" sortKey="followUpDate" currentSort={sort} onSort={handleSort} />
                <th style={{ padding: "10px 16px" }} />
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={6} style={{ padding: "48px", textAlign: "center", color: "#333", fontSize: "12px", fontFamily: "'Courier New', monospace" }}>
                  {contacts.length === 0 ? "No contacts yet — add your first contact above" : "No contacts match your filters"}
                </td></tr>
              ) : filtered.map(c => (
                <ContactRow
                  key={c.id}
                  contact={c}
                  onEdit={setEditing}
                  onSelect={c2 => setSelected(prev => prev?.id === c2.id ? null : c2)}
                  isSelected={selected?.id === c.id}
                  onStatusUpdate={updateStatus}
                  today={today}
                />
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div style={{ marginTop: "20px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ color: "#2a2a2a", fontSize: "9px", letterSpacing: "0.1em" }}>thewildwithin.xyz — data saved locally</div>
          <div style={{ color: "#2a2a2a", fontSize: "9px", letterSpacing: "0.1em" }}>{today}</div>
        </div>
      </div>

      <DetailPanel contact={selected} onClose={() => setSelected(null)} onEdit={setEditing} />

      {editing && <Modal title="Edit Contact" onClose={() => setEditing(null)}><ContactForm initial={editing} onSave={saveContact} onClose={() => setEditing(null)} onDelete={deleteContact} /></Modal>}
      {adding && <Modal title="New Press Contact" onClose={() => setAdding(false)}><ContactForm onSave={saveContact} onClose={() => setAdding(false)} /></Modal>}
      {showTemplates && <Modal title="Pitch Templates" onClose={() => setShowTemplates(false)} wide><TemplatesModal /></Modal>}
      {showExport && <Modal title="Export Contacts" onClose={() => setShowExport(false)}><ExportModal contacts={contacts} onClose={() => setShowExport(false)} today={today} /></Modal>}
      {showImport && <Modal title="Import Contacts" onClose={() => setShowImport(false)}><ImportModal onImport={handleImport} onClose={() => setShowImport(false)} /></Modal>}

      {toast && <Toast message={toast} onDone={() => setToast(null)} />}
    </div>
  );
}
