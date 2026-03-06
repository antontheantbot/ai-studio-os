/**
 * openclaw-aistudioos — AI Studio OS plugin for OpenClaw
 *
 * Exposes tools:
 *   - `aistudioos_opportunities`   — search open calls, residencies, commissions, festivals, contests
 *   - `aistudioos_grants`          — search funding and grant opportunities
 *   - `aistudioos_contests`        — search art contests and competitions
 *   - `aistudioos_artists`         — search the digital artist database
 *   - `aistudioos_journalists`     — search journalists covering art, culture, architecture
 *   - `aistudioos_collectors`      — search art collectors
 *   - `aistudioos_curators`        — search curators
 *   - `aistudioos_market_brief`    — get the latest art market brief
 *   - `aistudioos_color_trends`    — get latest color & size trends in contemporary art
 *   - `aistudioos_architecture`    — search architecture locations for installations
 *   - `aistudioos_chat`            — ask the AI Studio knowledge base a strategic question
 *
 * Config (openclaw.json → plugins.entries.openclaw-aistudioos.config):
 *   baseUrl — AI Studio OS API base URL (default: http://localhost/api/v1)
 */

import { Type } from "@sinclair/typebox";

type PluginApi = {
  pluginConfig?: Record<string, unknown>;
  logger: {
    info: (msg: string) => void;
    warn: (msg: string) => void;
    error: (msg: string) => void;
  };
  registerTool: (tool: unknown, opts?: unknown) => void;
};

const DEFAULT_BASE_URL = "http://localhost/api/v1";

function resolveBaseUrl(cfg: Record<string, unknown>): string {
  return typeof cfg.baseUrl === "string" && cfg.baseUrl.trim()
    ? cfg.baseUrl.trim().replace(/\/$/, "")
    : DEFAULT_BASE_URL;
}

function ok(text: string) {
  return { content: [{ type: "text" as const, text }], details: {} };
}

function err(msg: string) {
  return { content: [{ type: "text" as const, text: `Error: ${msg}` }], details: {} };
}

async function apiFetch(base: string, path: string, options?: RequestInit): Promise<unknown> {
  const res = await fetch(`${base}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`API ${res.status}: ${body.slice(0, 200)}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const OpportunitiesSchema = Type.Object({
  query: Type.Optional(Type.String({ description: "Semantic search query, e.g. 'digital art residency Europe'" })),
  category: Type.Optional(Type.String({ description: "Filter by category: open_call, residency, commission, festival, grant, contest" })),
  limit: Type.Optional(Type.Number({ description: "Max results (default 20)", minimum: 1, maximum: 100 })),
});

const GrantsSchema = Type.Object({
  query: Type.Optional(Type.String({ description: "Search query to filter grants, e.g. 'new media foundation'" })),
  limit: Type.Optional(Type.Number({ description: "Max results (default 20)", minimum: 1, maximum: 100 })),
});

const ContestsSchema = Type.Object({
  query: Type.Optional(Type.String({ description: "Search query, e.g. 'photography prize international'" })),
  limit: Type.Optional(Type.Number({ description: "Max results (default 20)", minimum: 1, maximum: 100 })),
});

const ArtistsSchema = Type.Object({
  query: Type.Optional(Type.String({ description: "Semantic search query, e.g. 'generative AI installation'" })),
  limit: Type.Optional(Type.Number({ description: "Max results (default 20)", minimum: 1, maximum: 100 })),
});

const JournalistsSchema = Type.Object({
  query: Type.Optional(Type.String({ description: "Search query, e.g. 'architecture critic New York'" })),
  limit: Type.Optional(Type.Number({ description: "Max results (default 20)", minimum: 1, maximum: 100 })),
});

const CollectorsSchema = Type.Object({
  query: Type.Optional(Type.String({ description: "Search query, e.g. 'digital art collector Europe'" })),
  limit: Type.Optional(Type.Number({ description: "Max results (default 20)", minimum: 1, maximum: 100 })),
});

const CuratorsSchema = Type.Object({
  query: Type.Optional(Type.String({ description: "Search query, e.g. 'new media curator biennale'" })),
  limit: Type.Optional(Type.Number({ description: "Max results (default 20)", minimum: 1, maximum: 100 })),
});

const MarketBriefSchema = Type.Object({});

const ColorTrendsSchema = Type.Object({});

const ArchitectureSchema = Type.Object({
  query: Type.Optional(Type.String({ description: "Search query, e.g. 'brutalist concrete Eastern Europe'" })),
  limit: Type.Optional(Type.Number({ description: "Max results (default 15)", minimum: 1, maximum: 50 })),
});

const ChatSchema = Type.Object({
  question: Type.String({ description: "Strategic question to ask the AI Studio knowledge base, e.g. 'Which collectors in Europe buy digital installations?'" }),
});

const DailyActionSchema = Type.Object({
  generate: Type.Optional(Type.Boolean({ description: "If true, force-generate a fresh action for today (replaces existing)" })),
});

// ---------------------------------------------------------------------------
// Formatters
// ---------------------------------------------------------------------------

function formatOpportunities(items: any[]): string {
  if (!items.length) return "No opportunities found.";
  return items.map(o => {
    const parts = [`## ${o.title}`];
    const meta = [o.category, o.deadline ? `Deadline: ${o.deadline}` : null, o.award ? `Award: ${o.award}` : null].filter(Boolean);
    if (meta.length) parts.push(meta.join(" | "));
    if (o.organizer) parts.push(`Organizer: ${o.organizer}`);
    if (o.location) parts.push(`Location: ${o.location}${o.country ? `, ${o.country}` : ""}`);
    if (o.description) parts.push(o.description.slice(0, 280) + (o.description.length > 280 ? "..." : ""));
    if (o.url) parts.push(`URL: ${o.url}`);
    return parts.join("\n");
  }).join("\n\n") + `\n\n---\nTotal: ${items.length}`;
}

function formatArtists(items: any[]): string {
  if (!items.length) return "No artists found.";
  return items.map(a => {
    const parts = [`## ${a.name}${a.city || a.country ? ` — ${[a.city, a.country].filter(Boolean).join(", ")}` : ""}`];
    if (a.medium?.length) parts.push(`Medium: ${a.medium.join(", ")}`);
    if (a.bio) parts.push(a.bio.slice(0, 220) + (a.bio.length > 220 ? "..." : ""));
    if (a.website) parts.push(`Web: ${a.website}`);
    return parts.join("\n");
  }).join("\n\n") + `\n\n---\nTotal: ${items.length}`;
}

function formatJournalists(items: any[]): string {
  if (!items.length) return "No journalists found.";
  return items.map(j => {
    const parts = [`## ${j.name}${j.location ? ` — ${j.location}${j.country ? `, ${j.country}` : ""}` : ""}`];
    if (j.publications?.length) parts.push(`Writes for: ${j.publications.join(", ")}`);
    if (j.beats?.length) parts.push(`Beats: ${j.beats.join(", ")}`);
    if (j.bio) parts.push(j.bio.slice(0, 200) + (j.bio.length > 200 ? "..." : ""));
    if (j.email) parts.push(`Email: ${j.email}`);
    const socials = Object.entries(j.social_links || {}).filter(([, v]) => v).map(([k, v]) => `${k}: ${v}`);
    if (socials.length) parts.push(socials.join(" | "));
    return parts.join("\n");
  }).join("\n\n") + `\n\n---\nTotal: ${items.length}`;
}

function formatPeople(items: any[], nameField = "name"): string {
  if (!items.length) return "No results found.";
  return items.map(p => {
    const parts = [`## ${p[nameField]}`];
    if (p.institution) parts.push(`Institution: ${p.institution}`);
    if (p.role) parts.push(`Role: ${p.role}`);
    if (p.location || p.country) parts.push(`Location: ${[p.location, p.country].filter(Boolean).join(", ")}`);
    if (p.bio) parts.push(p.bio.slice(0, 220) + (p.bio.length > 220 ? "..." : ""));
    if (p.focus_areas?.length) parts.push(`Focus: ${p.focus_areas.join(", ")}`);
    if (p.interests?.length) parts.push(`Interests: ${p.interests.join(", ")}`);
    if (p.contact_email) parts.push(`Email: ${p.contact_email}`);
    return parts.join("\n");
  }).join("\n\n") + `\n\n---\nTotal: ${items.length}`;
}

function formatArchitecture(items: any[]): string {
  if (!items.length) return "No locations found.";
  return items.map(loc => {
    const parts = [`## ${loc.name}${loc.city ? ` — ${[loc.city, loc.country].filter(Boolean).join(", ")}` : ""}`];
    if (loc.style) parts.push(`Style: ${loc.style}${loc.year_built ? ` (${loc.year_built})` : ""}`);
    if (loc.architect) parts.push(`Architect: ${loc.architect}`);
    if (loc.description) parts.push(loc.description.slice(0, 220) + (loc.description.length > 220 ? "..." : ""));
    if (loc.suitability) parts.push(`Suitability: ${Array.isArray(loc.suitability) ? loc.suitability.join(", ") : loc.suitability}`);
    if (loc.source_url) parts.push(`URL: ${loc.source_url}`);
    return parts.join("\n");
  }).join("\n\n") + `\n\n---\nTotal: ${items.length}`;
}

function formatBrief(brief: any): string {
  if (!brief || !brief.brief) return "No market brief available yet. Trigger one via the Trend-to-Brief tab.";
  const lines: string[] = [`# ${brief.title}`, `Week of: ${brief.week_of}`];
  if (brief.top_mediums?.length) lines.push(`\nTrending mediums: ${brief.top_mediums.join(", ")}`);
  if (brief.top_artists?.length) lines.push(`Market momentum: ${brief.top_artists.join(", ")}`);
  if (brief.signals?.length) {
    const strong = brief.signals.filter((s: any) => s.strength === "strong").length;
    const moderate = brief.signals.filter((s: any) => s.strength === "moderate").length;
    const emerging = brief.signals.filter((s: any) => s.strength === "emerging").length;
    lines.push(`Signals: ${strong} strong, ${moderate} moderate, ${emerging} emerging`);
  }
  lines.push("\n---\n", brief.brief);
  if (brief.sources?.length) lines.push(`\n---\nSources: ${brief.sources.slice(0, 4).join(", ")}`);
  return lines.join("\n");
}

function formatDailyAction(action: any): string {
  if (!action || !action.content) return "No daily action available yet. Visit the Daily Action tab to generate one.";
  const lines: string[] = [`# Daily Action — ${action.date}`];
  if (action.goal_name) lines.push(`Goal: ${action.goal_name}`);
  lines.push("", action.content);
  return lines.join("\n");
}

function formatColorTrends(data: any): string {
  if (!data || (!data.popular_colors?.length && !data.popular_sizes?.length)) {
    return "No color & size trends yet. Trigger a scan via the Trend-to-Brief tab.";
  }
  const lines: string[] = [`# Color & Size Trends — Week of ${data.week_of}`];
  if (data.summary) lines.push(`\n${data.summary}`);
  if (data.popular_colors?.length) {
    lines.push("\n## Popular Colors");
    for (const c of data.popular_colors) {
      lines.push(`- **${c.name}** (${c.hex}) [${c.trend}] — ${c.context}`);
    }
  }
  if (data.popular_sizes?.length) {
    lines.push("\n## Popular Sizes");
    for (const s of data.popular_sizes) {
      lines.push(`- **${s.label}** ${s.dimensions} · ${s.medium} [${s.trend}] — ${s.context}`);
    }
  }
  return lines.join("\n");
}

// ---------------------------------------------------------------------------
// Plugin
// ---------------------------------------------------------------------------

function aiStudioOsPlugin(api: PluginApi) {
  const cfg = (api.pluginConfig ?? {}) as Record<string, unknown>;
  const base = resolveBaseUrl(cfg);
  api.logger.info(`[aistudioos] Connected to ${base}`);

  // ── Opportunities ──────────────────────────────────────────────────────────
  api.registerTool({
    name: "aistudioos_opportunities",
    label: "AI Studio — Opportunities",
    description:
      "Search open calls, residencies, commissions, festivals, and contests from the AI Studio OS live database. " +
      "Returns upcoming opportunities with deadlines, awards, organizers, and apply links. " +
      "Use this when asked about art opportunities, open calls, or exhibitions to apply to.",
    parameters: OpportunitiesSchema,
    async execute(_id: string, params: Record<string, unknown>) {
      try {
        const qs = new URLSearchParams({ upcoming_only: "true", limit: String(params.limit ?? 20) });
        if (typeof params.query === "string" && params.query) qs.set("q", params.query);
        let items = await apiFetch(base, `/opportunities/?${qs}`) as any[];
        if (typeof params.category === "string" && !["grant", "contest"].includes(params.category)) {
          items = items.filter((o: any) => o.category === params.category);
        }
        return ok(formatOpportunities(items));
      } catch (e: any) {
        return err(e.message);
      }
    },
  });

  // ── Grants ─────────────────────────────────────────────────────────────────
  api.registerTool({
    name: "aistudioos_grants",
    label: "AI Studio — Grants",
    description:
      "Search art grant and funding opportunities from the AI Studio OS database. " +
      "Returns grants with deadlines, award amounts, and apply links. " +
      "Use this when asked about grants, funding, or financial support for artists.",
    parameters: GrantsSchema,
    async execute(_id: string, params: Record<string, unknown>) {
      try {
        const qs = new URLSearchParams({ upcoming_only: "true", limit: String(params.limit ?? 20) });
        if (typeof params.query === "string" && params.query) qs.set("q", params.query);
        const all = await apiFetch(base, `/opportunities/?${qs}`) as any[];
        const items = all.filter((o: any) => o.category === "grant");
        if (!items.length) return ok("No grants found in the database. Try scanning for new ones via the Opportunities tab.");
        return ok(formatOpportunities(items));
      } catch (e: any) {
        return err(e.message);
      }
    },
  });

  // ── Contests ───────────────────────────────────────────────────────────────
  api.registerTool({
    name: "aistudioos_contests",
    label: "AI Studio — Contests",
    description:
      "Search art contests and competitions from the AI Studio OS database. " +
      "Returns contests with deadlines, prize amounts, and entry links. " +
      "Use this when asked about art competitions, prizes, or contests to enter.",
    parameters: ContestsSchema,
    async execute(_id: string, params: Record<string, unknown>) {
      try {
        const qs = new URLSearchParams({ upcoming_only: "true", limit: String(params.limit ?? 20) });
        if (typeof params.query === "string" && params.query) qs.set("q", params.query);
        const all = await apiFetch(base, `/opportunities/?${qs}`) as any[];
        const items = all.filter((o: any) => o.category === "contest");
        if (!items.length) return ok("No contests found in the database. Try scanning via the Opportunities tab.");
        return ok(formatOpportunities(items));
      } catch (e: any) {
        return err(e.message);
      }
    },
  });

  // ── Artists ────────────────────────────────────────────────────────────────
  api.registerTool({
    name: "aistudioos_artists",
    label: "AI Studio — Artists",
    description:
      "Search the AI Studio OS database of top digital artists. " +
      "Returns artist profiles with bio, medium, location, and website. " +
      "Use this when asked about digital artists, who works in a certain medium, or artist recommendations.",
    parameters: ArtistsSchema,
    async execute(_id: string, params: Record<string, unknown>) {
      try {
        const qs = new URLSearchParams({ limit: String(params.limit ?? 20) });
        if (typeof params.query === "string" && params.query) qs.set("q", params.query);
        const items = await apiFetch(base, `/artists/?${qs}`) as any[];
        return ok(formatArtists(items));
      } catch (e: any) {
        return err(e.message);
      }
    },
  });

  // ── Journalists ────────────────────────────────────────────────────────────
  api.registerTool({
    name: "aistudioos_journalists",
    label: "AI Studio — Journalists",
    description:
      "Search the AI Studio OS database of journalists and critics covering art, culture, photography, and architecture. " +
      "Returns profiles with publications, beats, email, and social media contacts. " +
      "Use this when asked about press contacts, art writers, or who to pitch for coverage.",
    parameters: JournalistsSchema,
    async execute(_id: string, params: Record<string, unknown>) {
      try {
        const qs = new URLSearchParams({ limit: String(params.limit ?? 20) });
        if (typeof params.query === "string" && params.query) qs.set("q", params.query);
        const items = await apiFetch(base, `/journalists/?${qs}`) as any[];
        return ok(formatJournalists(items));
      } catch (e: any) {
        return err(e.message);
      }
    },
  });

  // ── Collectors ─────────────────────────────────────────────────────────────
  api.registerTool({
    name: "aistudioos_collectors",
    label: "AI Studio — Collectors",
    description:
      "Search the AI Studio OS database of art collectors. " +
      "Returns collector profiles with interests, known works, and institutional affiliations. " +
      "Use this when asked about collectors, who buys digital art, or who to approach for acquisitions.",
    parameters: CollectorsSchema,
    async execute(_id: string, params: Record<string, unknown>) {
      try {
        const qs = new URLSearchParams({ limit: String(params.limit ?? 20) });
        if (typeof params.query === "string" && params.query) qs.set("q", params.query);
        const items = await apiFetch(base, `/collectors/?${qs}`) as any[];
        return ok(formatPeople(items));
      } catch (e: any) {
        return err(e.message);
      }
    },
  });

  // ── Curators ───────────────────────────────────────────────────────────────
  api.registerTool({
    name: "aistudioos_curators",
    label: "AI Studio — Curators",
    description:
      "Search the AI Studio OS database of curators working with digital and contemporary art. " +
      "Returns curator profiles with institution, role, focus areas, and notable shows. " +
      "Use this when asked about curators, who to approach for shows, or curatorial contacts.",
    parameters: CuratorsSchema,
    async execute(_id: string, params: Record<string, unknown>) {
      try {
        const qs = new URLSearchParams({ limit: String(params.limit ?? 20) });
        if (typeof params.query === "string" && params.query) qs.set("q", params.query);
        const items = await apiFetch(base, `/curators/?${qs}`) as any[];
        return ok(formatPeople(items));
      } catch (e: any) {
        return err(e.message);
      }
    },
  });

  // ── Market Brief ───────────────────────────────────────────────────────────
  api.registerTool({
    name: "aistudioos_market_brief",
    label: "AI Studio — Market Brief",
    description:
      "Get the latest weekly art market brief generated from Christie's, Sotheby's, Art Basel, Pace Gallery, and Artsy. " +
      "Includes market signals, trending mediums, artists with momentum, and creative project briefs. " +
      "Use this when asked about art market trends, what's selling, or strategic creative directions.",
    parameters: MarketBriefSchema,
    async execute(_id: string, _params: Record<string, unknown>) {
      try {
        const brief = await apiFetch(base, "/briefs/latest");
        return ok(formatBrief(brief));
      } catch (e: any) {
        return err(e.message);
      }
    },
  });

  // ── Color & Size Trends ────────────────────────────────────────────────────
  api.registerTool({
    name: "aistudioos_color_trends",
    label: "AI Studio — Color & Size Trends",
    description:
      "Get the latest color and artwork size trends in contemporary art (paintings, photography, prints, video — excluding sculpture and furniture). " +
      "Returns popular colors with hex codes, popular sizes with dimensions, and a summary. " +
      "Use this when asked about trending colors, popular formats, or what sizes collectors are buying.",
    parameters: ColorTrendsSchema,
    async execute(_id: string, _params: Record<string, unknown>) {
      try {
        const data = await apiFetch(base, "/briefs/color-trends/latest");
        return ok(formatColorTrends(data));
      } catch (e: any) {
        return err(e.message);
      }
    },
  });

  // ── Architecture ───────────────────────────────────────────────────────────
  api.registerTool({
    name: "aistudioos_architecture",
    label: "AI Studio — Architecture",
    description:
      "Search architecture locations scouted for digital art installations and photography. " +
      "Returns buildings and sites with style, architect, location, and suitability notes. " +
      "Use this when asked about installation venues, location scouting, or architectural settings.",
    parameters: ArchitectureSchema,
    async execute(_id: string, params: Record<string, unknown>) {
      try {
        const qs = new URLSearchParams({ limit: String(params.limit ?? 15) });
        if (typeof params.query === "string" && params.query) qs.set("q", params.query);
        const items = await apiFetch(base, `/architecture/?${qs}`) as any[];
        return ok(formatArchitecture(items));
      } catch (e: any) {
        return err(e.message);
      }
    },
  });

  // ── Daily Action ───────────────────────────────────────────────────────────
  api.registerTool({
    name: "aistudioos_daily",
    label: "AI Studio — Daily Action",
    description:
      "Get today's daily action for Ryan Koopmans and Alice Wexell — one concrete, specific task to advance their career goals. " +
      "Rotates across 8 goals: press coverage, Instagram presence, SEO, museum acquisition, revenue, gallery, Art Basel, art history. " +
      "Use this when asked what to do today, what the daily action is, or for today's career task.",
    parameters: DailyActionSchema,
    async execute(_id: string, params: Record<string, unknown>) {
      try {
        let action: any;
        if (params.generate === true) {
          action = await apiFetch(base, "/daily/generate", { method: "POST" });
        } else {
          action = await apiFetch(base, "/daily/today");
        }
        return ok(formatDailyAction(action));
      } catch (e: any) {
        return err(e.message);
      }
    },
  });

  // ── Chat / Knowledge Base ──────────────────────────────────────────────────
  api.registerTool({
    name: "aistudioos_chat",
    label: "AI Studio — Knowledge Base",
    description:
      "Ask the AI Studio OS knowledge base a strategic question. It has access to the live database of " +
      "collectors, curators, journalists, institutions, opportunities, contests, and knowledge articles. " +
      "Use this for strategic questions like 'Which collectors buy digital art in Europe?' or " +
      "'What should I focus on in the next 90 days?'",
    parameters: ChatSchema,
    async execute(_id: string, params: Record<string, unknown>) {
      try {
        const question = typeof params.question === "string" ? params.question.trim() : "";
        if (!question) return err("A question is required.");
        const data = await apiFetch(base, "/chat/", {
          method: "POST",
          body: JSON.stringify({ message: question, history: [] }),
        }) as any;
        let text = data.response ?? "No response.";
        if (data.sources?.length) text += `\n\nSources: ${data.sources.join(", ")}`;
        return ok(text);
      } catch (e: any) {
        return err(e.message);
      }
    },
  });

  api.logger.info("[aistudioos] 12 tools registered: opportunities, grants, contests, artists, journalists, collectors, curators, market_brief, color_trends, architecture, daily, chat");
}

export default aiStudioOsPlugin;
