const BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

// ── Opportunities ────────────────────────────────────────────────────────────
export const getOpportunities = (q?: string) =>
  request<Opportunity[]>(`/opportunities/?upcoming_only=true${q ? `&q=${encodeURIComponent(q)}` : ""}&limit=100`);

export const triggerOpportunityScan = () =>
  request<{ task_id: string }>("/opportunities/scan", { method: "POST" });

// ── Architecture ─────────────────────────────────────────────────────────────
export const getArchitecture = (q?: string) =>
  request<ArchitectureLocation[]>(`/architecture/${q ? `?q=${encodeURIComponent(q)}` : ""}`);

export const triggerArchitectureScan = () =>
  request<{ status: string }>("/architecture/scan", { method: "POST" });

// ── Collectors ───────────────────────────────────────────────────────────────
export const getCollectors = (q?: string) =>
  request<Collector[]>(`/collectors/${q ? `?q=${encodeURIComponent(q)}` : ""}`);

// ── Curators ─────────────────────────────────────────────────────────────────
export const getCurators = (q?: string) =>
  request<Curator[]>(`/curators/${q ? `?q=${encodeURIComponent(q)}` : ""}`);

// ── Press ────────────────────────────────────────────────────────────────────
export const getPress = (q?: string, mode: "semantic" | "keyword" = "semantic") =>
  request<PressItem[]>(`/press/${q ? `?q=${encodeURIComponent(q)}&mode=${mode}` : ""}`);

// ── Proposals ────────────────────────────────────────────────────────────────
export const getProposals = () => request<Proposal[]>("/proposals/");

export const generateProposal = (body: ProposalRequest) =>
  request<{ proposal: string; request: ProposalRequest }>("/proposals/generate", {
    method: "POST",
    body: JSON.stringify(body),
  });

// ── Knowledge ────────────────────────────────────────────────────────────────
export const getKnowledge = () => request<KnowledgeItem[]>("/knowledge/");

export const searchKnowledge = (q: string) =>
  request<KnowledgeItem[]>(`/knowledge/search?q=${encodeURIComponent(q)}`);

export const createNote = (body: { title: string; content: string; tags: string[] }) =>
  request<{ id: string; title: string }>("/knowledge/notes", {
    method: "POST",
    body: JSON.stringify(body),
  });

export const deleteKnowledge = (id: string) =>
  request<{ deleted: string }>(`/knowledge/${id}`, { method: "DELETE" });

// ── Artists ──────────────────────────────────────────────────────────────────
export const getArtists = (q?: string) =>
  request<Artist[]>(`/artists/${q ? `?q=${encodeURIComponent(q)}` : ""}`);

export const createArtist = (body: Omit<Artist, "id" | "created_at">) =>
  request<{ id: string; name: string }>("/artists/", {
    method: "POST",
    body: JSON.stringify(body),
  });

// ── Artworks ──────────────────────────────────────────────────────────────────
export const getArtworks = (q?: string, artist_id?: string) =>
  request<Artwork[]>(
    `/artworks/${q ? `?q=${encodeURIComponent(q)}` : artist_id ? `?artist_id=${artist_id}` : ""}`
  );

export const createArtwork = (body: Omit<Artwork, "id" | "created_at" | "artist_name">) =>
  request<{ id: string; title: string }>("/artworks/", {
    method: "POST",
    body: JSON.stringify(body),
  });

// ── Institutions ─────────────────────────────────────────────────────────────
export const getInstitutions = (q?: string, digital_only?: boolean) =>
  request<Institution[]>(
    `/institutions/${q ? `?q=${encodeURIComponent(q)}` : digital_only ? "?digital_only=true" : ""}`
  );

export const createInstitution = (body: Omit<Institution, "id" | "created_at">) =>
  request<{ id: string; name: string }>("/institutions/", {
    method: "POST",
    body: JSON.stringify(body),
  });

// ── Exhibitions ───────────────────────────────────────────────────────────────
export const getExhibitions = (q?: string, institution_id?: string) =>
  request<Exhibition[]>(
    `/exhibitions/${q ? `?q=${encodeURIComponent(q)}` : institution_id ? `?institution_id=${institution_id}` : ""}`
  );

export const createExhibition = (body: Omit<Exhibition, "id" | "created_at">) =>
  request<{ id: string; title: string }>("/exhibitions/", {
    method: "POST",
    body: JSON.stringify(body),
  });

// ── Market Briefs ─────────────────────────────────────────────────────────────
export const getBriefs = () => request<MarketBrief[]>("/briefs/");
export const getLatestBrief = () => request<MarketBrief>("/briefs/latest");
export const getLatestColorTrends = () => request<ColorSizeTrend>("/briefs/color-trends/latest");
export const scanColorTrends = () => request<{ status: string }>("/briefs/color-trends/scan", { method: "POST" });
export const scanMarket = () => request<{ status: string }>("/briefs/scan", { method: "POST" });

// ── Journalists ───────────────────────────────────────────────────────────────
export const getJournalists = (q?: string) =>
  request<Journalist[]>(`/journalists/?limit=1000${q ? `&q=${encodeURIComponent(q)}` : ""}`);
export const scanJournalists = () =>
  request<{ status: string }>("/journalists/scan", { method: "POST" });
export const addJournalistsFromText = (text: string) =>
  request<{ added: number; skipped: number; message: string }>("/journalists/add", {
    method: "POST",
    body: JSON.stringify({ text }),
  });

// ── Daily Action ──────────────────────────────────────────────────────────────
export const getDailyAction = () => request<DailyAction>("/daily/today");
export const generateDailyAction = () => request<DailyAction>("/daily/generate", { method: "POST" });
export const getDailyHistory = () => request<DailyAction[]>("/daily/history");

// ── Chat ─────────────────────────────────────────────────────────────────────
export const chat = (message: string, history: ChatMessage[]) =>
  request<{ response: string; sources: string[] }>("/chat/", {
    method: "POST",
    body: JSON.stringify({ message, history }),
  });

// ── Types ────────────────────────────────────────────────────────────────────
export interface Opportunity {
  id: string;
  title: string;
  description: string;
  category: string;
  organizer: string;
  location: string;
  country: string;
  deadline: string | null;
  fee: string | null;
  award: string | null;
  url: string;
  tags: string[];
  is_active: boolean;
  created_at: string;
}

export interface ArchitectureLocation {
  id: string;
  name: string;
  description: string;
  architect: string;
  city: string;
  country: string;
  style: string;
  year_built: number | null;
  suitability: string[];
  source_url: string;
  created_at: string;
}

export interface Collector {
  id: string;
  name: string;
  bio: string;
  location: string;
  country: string;
  interests: string[];
  institutions: string[];
  created_at: string;
}

export interface Curator {
  id: string;
  name: string;
  bio: string;
  institution: string;
  role: string;
  location: string;
  focus_areas: string[];
  notable_shows: string[];
  created_at: string;
}

export interface PressItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  author: string;
  url: string;
  published_at: string;
  category: string;
  tags: string[];
  mentioned_artists: string[];
}

export interface Proposal {
  id: string;
  title: string;
  status: string;
  created_at: string;
}

export interface ProposalRequest {
  opportunity_title: string;
  opportunity_description: string;
  artist_statement: string;
  project_concept: string;
  budget_range?: string;
}

export interface KnowledgeItem {
  id: string;
  title: string;
  content: string;
  summary: string;
  source_type: string;
  tags: string[];
  created_at: string;
  similarity?: number;
}

export interface Artist {
  id: string;
  name: string;
  country: string | null;
  city: string | null;
  bio: string | null;
  medium: string[];
  website: string | null;
  instagram: string | null;
  represented_by: string[];
  created_at: string;
}

export interface Artwork {
  id: string;
  title: string;
  artist_id: string | null;
  artist_name?: string;
  year: number | null;
  medium: string | null;
  dimensions: string | null;
  description: string | null;
  image_urls: string[];
  collection: string | null;
  exhibition_history: string[];
  created_at: string;
}

export interface Institution {
  id: string;
  name: string;
  city: string | null;
  country: string | null;
  type: string | null;
  website: string | null;
  focus_areas: string[];
  annual_budget: string | null;
  digital_art_program: boolean;
  notes: string | null;
  created_at: string;
}

export interface Exhibition {
  id: string;
  title: string;
  institution_id: string | null;
  curator_id: string | null;
  start_date: string | null;
  end_date: string | null;
  type: string | null;
  artists: string[];
  description: string | null;
  url: string | null;
  created_at: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface MarketBrief {
  id: string;
  week_of: string;
  title: string;
  signals: { signal: string; source: string; url: string; category: string; strength: string }[];
  trends: { category: string; signal: string; strength: string }[];
  top_artists: string[];
  top_mediums: string[];
  brief: string;
  sources: string[];
  created_at: string;
  updated_at: string;
}

export interface DailyAction {
  id: string;
  date: string;
  goal_index: number;
  goal_name: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface Journalist {
  id: string;
  name: string;
  bio: string;
  publications: string[];
  beats: string[];
  email: string | null;
  social_links: { twitter?: string; instagram?: string; linkedin?: string; website?: string };
  location: string | null;
  country: string | null;
  notes: string | null;
  created_at: string;
}

export interface ColorSizeTrend {
  id: string;
  week_of: string;
  popular_colors: { name: string; hex: string; trend: "rising" | "dominant" | "emerging"; context: string }[];
  popular_sizes: { label: string; dimensions: string; medium: string; trend: "rising" | "dominant" | "emerging"; context: string }[];
  summary: string;
  sources: string[];
  created_at: string;
  updated_at: string;
}
