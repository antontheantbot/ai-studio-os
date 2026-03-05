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
  request<Opportunity[]>(`/opportunities/${q ? `?q=${encodeURIComponent(q)}` : ""}`);

export const triggerOpportunityScan = () =>
  request<{ task_id: string }>("/opportunities/scan", { method: "POST" });

// ── Architecture ─────────────────────────────────────────────────────────────
export const getArchitecture = (q?: string) =>
  request<ArchitectureLocation[]>(`/architecture/${q ? `?q=${encodeURIComponent(q)}` : ""}`);

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

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}
