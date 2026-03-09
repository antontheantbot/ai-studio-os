// @ts-nocheck
"use client";
import { useState, useEffect } from "react";

const API = "/api/v1";

const SENTIMENT_COLOR = {
  positive: "#5aaa82",
  neutral: "#8a8a8a",
  negative: "#aa5a5a",
};

const TIER_LABELS = { 1: "TIER 1", 2: "TIER 2", 3: "TIER 3", 4: "TIER 4" };

const STATUS_COLORS = {
  not_pitched: "#555",
  pitched: "#c9a84c",
  follow_up_due: "#e8b84b",
  in_discussion: "#7eb8a4",
  declined: "#774444",
  published: "#5aaa82",
};

function RelevanceBar({ score }: { score: number }) {
  const filled = Math.round(score * 10);
  return (
    <span style={{ fontFamily: "monospace", color: "#c9a84c", fontSize: 11 }}>
      {"["}
      {"█".repeat(filled)}
      {"░".repeat(10 - filled)}
      {"] "}
      {score.toFixed(2)}
    </span>
  );
}

export default function PressMonitorPage() {
  const [tab, setTab] = useState<"brief" | "coverage" | "journalists" | "opportunities">("brief");
  const [coverage, setCoverage] = useState([]);
  const [journalists, setJournalists] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [followUps, setFollowUps] = useState([]);
  const [latestBrief, setLatestBrief] = useState(null);
  const [scanning, setScanning] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const [cov, jour, opps, fups, brief] = await Promise.all([
        fetch(`${API}/press-monitor/coverage?days=14`).then(r => r.json()).catch(() => []),
        fetch(`${API}/press-monitor/journalists`).then(r => r.json()).catch(() => []),
        fetch(`${API}/press-monitor/opportunities?actionable_only=false`).then(r => r.json()).catch(() => []),
        fetch(`${API}/press-monitor/follow-ups`).then(r => r.json()).catch(() => []),
        fetch(`${API}/press-monitor/briefs/latest`).then(r => r.json()).catch(() => null),
      ]);
      setCoverage(Array.isArray(cov) ? cov : []);
      setJournalists(Array.isArray(jour) ? jour : []);
      setOpportunities(Array.isArray(opps) ? opps : []);
      setFollowUps(Array.isArray(fups) ? fups : []);
      setLatestBrief(brief);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function triggerScan(type: string) {
    setScanning(type);
    try {
      await fetch(`${API}/press-monitor/scan/${type}`, { method: "POST" });
      setTimeout(() => { load(); setScanning(null); }, 3000);
    } catch {
      setScanning(null);
    }
  }

  async function markActioned(articleId: number) {
    await fetch(`${API}/press-monitor/opportunities/${articleId}/action`, { method: "POST" });
    load();
  }

  const today = new Date().toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });

  return (
    <div style={{ background: "#0a0a00", minHeight: "100vh", color: "#d4d0c8", fontFamily: "monospace" }}>
      {/* Header */}
      <div style={{ borderBottom: "1px solid #2a2a1a", padding: "20px 32px 16px" }}>
        <div style={{ fontSize: 10, color: "#666", letterSpacing: 3, marginBottom: 4 }}>PRESS MONITOR V2</div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
          <h1 style={{ fontSize: 18, fontWeight: 600, color: "#e8e0c8", margin: 0 }}>
            {"// PRESS BRIEF"}
          </h1>
          <span style={{ fontSize: 11, color: "#666" }}>{today}</span>
        </div>
        {/* Stats row */}
        <div style={{ display: "flex", gap: 24, marginTop: 12 }}>
          {[
            { label: "COVERAGE", value: coverage.length, color: "#c9a84c" },
            { label: "OPPORTUNITIES", value: opportunities.filter(o => o.is_actionable && !o.actioned).length, color: "#7eb8a4" },
            { label: "FOLLOW-UPS DUE", value: followUps.length, color: "#e8b84b" },
            { label: "JOURNALISTS", value: journalists.length, color: "#8a8a8a" },
          ].map(s => (
            <div key={s.label} style={{ display: "flex", alignItems: "baseline", gap: 6 }}>
              <span style={{ fontSize: 20, fontWeight: 700, color: s.color }}>{s.value}</span>
              <span style={{ fontSize: 9, color: "#555", letterSpacing: 1 }}>{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs + Scan Buttons */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "0 32px", borderBottom: "1px solid #1a1a0a" }}>
        <div style={{ display: "flex" }}>
          {(["brief", "coverage", "opportunities", "journalists"] as const).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              style={{
                padding: "10px 16px",
                fontSize: 10,
                letterSpacing: 1.5,
                background: "none",
                border: "none",
                borderBottom: tab === t ? "2px solid #c9a84c" : "2px solid transparent",
                color: tab === t ? "#c9a84c" : "#555",
                cursor: "pointer",
                textTransform: "uppercase",
              }}
            >
              {t}
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {["coverage", "journalists", "brief"].map(type => (
            <button
              key={type}
              onClick={() => triggerScan(type)}
              disabled={!!scanning}
              style={{
                padding: "5px 10px",
                fontSize: 9,
                letterSpacing: 1,
                background: scanning === type ? "#1a1a0a" : "#111100",
                border: "1px solid #2a2a1a",
                color: scanning === type ? "#c9a84c" : "#666",
                cursor: scanning ? "not-allowed" : "pointer",
                borderRadius: 2,
              }}
            >
              {scanning === type ? "SCANNING..." : `SCAN ${type.toUpperCase()}`}
            </button>
          ))}
        </div>
      </div>

      <div style={{ padding: "24px 32px", maxWidth: 1100 }}>
        {loading ? (
          <div style={{ color: "#555", fontSize: 12 }}>Loading...</div>
        ) : (
          <>
            {/* BRIEF TAB */}
            {tab === "brief" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                {/* Follow-ups */}
                <Section title={`FOLLOW-UPS DUE TODAY (${followUps.length})`}>
                  {followUps.length === 0 ? (
                    <Empty>No follow-ups due</Empty>
                  ) : followUps.map(j => (
                    <Row key={j.id}>
                      <div style={{ fontWeight: 600, color: "#e8b84b" }}>{j.name}</div>
                      <div style={{ fontSize: 11, color: "#888" }}>{j.publication} · {j.email}</div>
                      <div style={{ fontSize: 10, color: j.days_until <= 0 ? "#e8b84b" : "#666", marginTop: 2 }}>
                        {j.days_until <= 0 ? `Overdue by ${Math.abs(j.days_until)}d` : `Due in ${j.days_until}d`}
                      </div>
                      {j.notes && <div style={{ fontSize: 11, color: "#666", marginTop: 4 }}>{j.notes}</div>}
                    </Row>
                  ))}
                </Section>

                {/* Warm outreach */}
                <Section title={`WARM OUTREACH OPPORTUNITIES (${opportunities.filter(o => o.is_actionable && !o.actioned).length})`}>
                  {opportunities.filter(o => o.is_actionable && !o.actioned).length === 0 ? (
                    <Empty>No actionable opportunities</Empty>
                  ) : opportunities.filter(o => o.is_actionable && !o.actioned).map(opp => (
                    <Row key={opp.id}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                        <div>
                          <span style={{ fontWeight: 600, color: "#e8e0c8" }}>{opp.journalist_name || "—"}</span>
                          <span style={{ color: "#555", margin: "0 6px" }}>@</span>
                          <span style={{ color: "#888" }}>{opp.journalist_publication || "—"}</span>
                        </div>
                        <RelevanceBar score={opp.relevance_score || 0} />
                      </div>
                      {opp.title && <div style={{ fontSize: 11, color: "#aaa", marginTop: 4 }}>Wrote: {opp.title}</div>}
                      {opp.warm_pitch_angle && (
                        <div style={{ fontSize: 11, color: "#7eb8a4", marginTop: 6 }}>
                          ANGLE: {opp.warm_pitch_angle}
                        </div>
                      )}
                      <button
                        onClick={() => markActioned(opp.id)}
                        style={{ marginTop: 8, padding: "3px 8px", fontSize: 9, background: "#1a1a0a", border: "1px solid #2a2a1a", color: "#666", cursor: "pointer", borderRadius: 2 }}
                      >
                        MARK ACTIONED
                      </button>
                    </Row>
                  ))}
                </Section>

                {/* New mentions */}
                <Section title={`NEW MENTIONS (${coverage.length})`}>
                  {coverage.length === 0 ? (
                    <Empty>No recent coverage</Empty>
                  ) : coverage.slice(0, 5).map(m => (
                    <Row key={m.id}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ color: SENTIMENT_COLOR[m.sentiment] || "#888" }}>
                          {m.sentiment === "positive" ? "[+]" : m.sentiment === "negative" ? "[-]" : "[~]"}
                        </span>
                        <span style={{ color: "#888", fontSize: 10 }}>{TIER_LABELS[m.publication_tier] || ""}</span>
                        <span style={{ fontWeight: 600, color: "#e8e0c8" }}>{m.source}</span>
                      </div>
                      {m.title && <div style={{ fontSize: 11, color: "#aaa", marginTop: 4 }}>{m.title}</div>}
                      {m.url && (
                        <a href={m.url} target="_blank" rel="noreferrer" style={{ fontSize: 10, color: "#555", marginTop: 4, display: "block" }}>
                          {m.url.slice(0, 60)}...
                        </a>
                      )}
                    </Row>
                  ))}
                </Section>
              </div>
            )}

            {/* COVERAGE TAB */}
            {tab === "coverage" && (
              <Section title={`COVERAGE MENTIONS (${coverage.length})`}>
                {coverage.length === 0 ? <Empty>No coverage yet — run a scan</Empty> : coverage.map(m => (
                  <Row key={m.id}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <span style={{ color: SENTIMENT_COLOR[m.sentiment] || "#888", fontSize: 11 }}>
                          {m.sentiment === "positive" ? "[+]" : m.sentiment === "negative" ? "[-]" : "[~]"}
                        </span>
                        <span style={{ fontWeight: 600, color: "#e8e0c8" }}>{m.source}</span>
                        <span style={{ fontSize: 10, color: "#555" }}>{TIER_LABELS[m.publication_tier]}</span>
                      </div>
                      <span style={{ fontSize: 10, color: "#444" }}>
                        {m.published_at ? new Date(m.published_at).toLocaleDateString() : ""}
                      </span>
                    </div>
                    {m.title && <div style={{ fontSize: 12, color: "#aaa", marginTop: 4 }}>{m.title}</div>}
                    {m.summary && <div style={{ fontSize: 11, color: "#666", marginTop: 4 }}>{m.summary}</div>}
                    {m.url && (
                      <a href={m.url} target="_blank" rel="noreferrer" style={{ fontSize: 10, color: "#555", marginTop: 4, display: "block" }}>
                        {m.url}
                      </a>
                    )}
                  </Row>
                ))}
              </Section>
            )}

            {/* OPPORTUNITIES TAB */}
            {tab === "opportunities" && (
              <Section title={`JOURNALIST ARTICLE OPPORTUNITIES (${opportunities.length})`}>
                {opportunities.length === 0 ? <Empty>No opportunities yet — run a journalist scan</Empty> : opportunities.map(opp => (
                  <Row key={opp.id} style={{ opacity: opp.actioned ? 0.4 : 1 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <div>
                        <span style={{ fontWeight: 600, color: "#e8e0c8" }}>{opp.journalist_name || "—"}</span>
                        <span style={{ color: "#555", margin: "0 6px" }}>·</span>
                        <span style={{ color: "#888" }}>{opp.journalist_publication || "—"}</span>
                        {opp.is_actionable && !opp.actioned && (
                          <span style={{ marginLeft: 8, fontSize: 9, color: "#7eb8a4", letterSpacing: 1 }}>ACTIONABLE</span>
                        )}
                        {opp.actioned && (
                          <span style={{ marginLeft: 8, fontSize: 9, color: "#555", letterSpacing: 1 }}>ACTIONED</span>
                        )}
                      </div>
                      <RelevanceBar score={opp.relevance_score || 0} />
                    </div>
                    {opp.title && <div style={{ fontSize: 11, color: "#aaa", marginTop: 4 }}>"{opp.title}"</div>}
                    {opp.warm_pitch_angle && (
                      <div style={{ fontSize: 11, color: "#7eb8a4", marginTop: 6 }}>ANGLE: {opp.warm_pitch_angle}</div>
                    )}
                    {!opp.actioned && opp.is_actionable && (
                      <button
                        onClick={() => markActioned(opp.id)}
                        style={{ marginTop: 8, padding: "3px 8px", fontSize: 9, background: "#1a1a0a", border: "1px solid #2a2a1a", color: "#666", cursor: "pointer", borderRadius: 2 }}
                      >
                        MARK ACTIONED
                      </button>
                    )}
                  </Row>
                ))}
              </Section>
            )}

            {/* JOURNALISTS TAB */}
            {tab === "journalists" && (
              <Section title={`TARGET JOURNALISTS (${journalists.length})`}>
                {journalists.length === 0 ? <Empty>No journalists yet</Empty> : journalists.map(j => (
                  <Row key={j.id}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <div>
                        <span style={{ fontWeight: 600, color: "#e8e0c8" }}>{j.name}</span>
                        <span style={{ color: "#555", margin: "0 6px" }}>·</span>
                        <span style={{ color: "#888" }}>{j.publication}</span>
                        {j.role && <span style={{ color: "#555", fontSize: 10, marginLeft: 8 }}>{j.role}</span>}
                      </div>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <span style={{ fontSize: 9, letterSpacing: 1, color: "#555" }}>{TIER_LABELS[j.tier_level]}</span>
                        <span style={{
                          fontSize: 9, padding: "2px 6px", borderRadius: 2,
                          background: "#1a1a0a", border: `1px solid ${STATUS_COLORS[j.pitch_status] || "#333"}`,
                          color: STATUS_COLORS[j.pitch_status] || "#666", letterSpacing: 1,
                        }}>
                          {(j.pitch_status || "").replace(/_/g, " ").toUpperCase()}
                        </span>
                      </div>
                    </div>
                    {j.beats && j.beats.length > 0 && (
                      <div style={{ fontSize: 10, color: "#555", marginTop: 4 }}>
                        {j.beats.join(" · ")}
                      </div>
                    )}
                    {j.email && <div style={{ fontSize: 10, color: "#444", marginTop: 2 }}>{j.email}</div>}
                    {j.follow_up_date && (
                      <div style={{ fontSize: 10, color: "#e8b84b", marginTop: 4 }}>
                        Follow-up: {new Date(j.follow_up_date).toLocaleDateString()}
                      </div>
                    )}
                    {j.notes && <div style={{ fontSize: 11, color: "#666", marginTop: 4 }}>{j.notes}</div>}
                  </Row>
                ))}
              </Section>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div style={{ fontSize: 9, letterSpacing: 2, color: "#555", marginBottom: 8, borderBottom: "1px solid #1a1a0a", paddingBottom: 6 }}>
        {title}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {children}
      </div>
    </div>
  );
}

function Row({ children, style = {} }: { children: React.ReactNode; style?: object }) {
  return (
    <div style={{ background: "#0f0f00", border: "1px solid #1a1a0a", padding: "12px 14px", borderRadius: 2, ...style }}>
      {children}
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <div style={{ color: "#444", fontSize: 11 }}>{children}</div>;
}
