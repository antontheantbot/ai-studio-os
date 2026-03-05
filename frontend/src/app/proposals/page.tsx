"use client";
import { useState } from "react";
import useSWR from "swr";
import { FileText, Loader2, Copy, Check } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import EmptyState from "@/components/EmptyState";
import { getProposals, generateProposal, type Proposal, type ProposalRequest } from "@/lib/api";

const EMPTY_FORM: ProposalRequest = {
  opportunity_title: "",
  opportunity_description: "",
  artist_statement: "",
  project_concept: "",
  budget_range: "",
};

export default function ProposalsPage() {
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<ProposalRequest>(EMPTY_FORM);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const { data: proposals, isLoading, mutate } = useSWR("proposals", getProposals);

  const set = (k: keyof ProposalRequest) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const handleGenerate = async () => {
    if (!form.opportunity_title || !form.artist_statement || !form.project_concept) return;
    setGenerating(true);
    setResult(null);
    try {
      const res = await generateProposal(form);
      setResult(res.proposal);
      mutate();
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = () => {
    if (result) {
      navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div>
      <PageHeader
        title="Proposals"
        description="Generate and manage museum-quality proposals"
        actions={
          <button onClick={() => { setShowForm(!showForm); setResult(null); }} className="btn-primary">
            {showForm ? "Close" : "+ New Proposal"}
          </button>
        }
      />

      {/* Generator form */}
      {showForm && (
        <div className="card mb-6">
          <h2 className="text-xs font-medium uppercase tracking-widest text-studio-text-muted mb-4">
            Proposal Generator
          </h2>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Opportunity Title *</label>
              <input value={form.opportunity_title} onChange={set("opportunity_title")} placeholder="e.g. Berlin Biennial Open Call 2025" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Opportunity Description *</label>
              <textarea value={form.opportunity_description} onChange={set("opportunity_description")}
                placeholder="Paste the full opportunity description..." rows={3} className="resize-none" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Your Artist Statement *</label>
              <textarea value={form.artist_statement} onChange={set("artist_statement")}
                placeholder="Your existing artist statement..." rows={4} className="resize-none" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Project Concept *</label>
              <textarea value={form.project_concept} onChange={set("project_concept")}
                placeholder="Describe the specific project idea for this opportunity..." rows={4} className="resize-none" />
            </div>
            <div>
              <label className="text-xs text-studio-text-muted mb-1 block">Budget Range (optional)</label>
              <input value={form.budget_range} onChange={set("budget_range")} placeholder="e.g. €5,000 – €15,000" />
            </div>
            <button
              onClick={handleGenerate}
              disabled={generating || !form.opportunity_title || !form.artist_statement || !form.project_concept}
              className="btn-primary flex items-center gap-2 w-full justify-center"
            >
              {generating ? <><Loader2 size={13} className="animate-spin" /> Generating...</> : "Generate Proposal"}
            </button>
          </div>

          {/* Generated output */}
          {result && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-xs font-medium uppercase tracking-widest text-studio-text-muted">Generated Proposal</h3>
                <button onClick={handleCopy} className="btn-ghost flex items-center gap-1 text-xs">
                  {copied ? <><Check size={11} /> Copied</> : <><Copy size={11} /> Copy</>}
                </button>
              </div>
              <div className="bg-studio-bg rounded border border-studio-border p-4 text-xs text-studio-text whitespace-pre-wrap leading-relaxed max-h-[60vh] overflow-y-auto">
                {result}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Proposals list */}
      {isLoading && <p className="text-studio-text-muted text-xs">Loading...</p>}

      {!isLoading && (!proposals || proposals.length === 0) && !showForm && (
        <EmptyState icon={FileText} message="No proposals yet" sub="Use the generator to create your first proposal" />
      )}

      <div className="space-y-2">
        {(proposals ?? []).map((p: Proposal) => (
          <div key={p.id} className="card flex items-center justify-between hover:border-studio-muted transition-colors">
            <div>
              <p className="text-sm text-studio-text">{p.title}</p>
              <p className="text-xs text-studio-text-muted mt-0.5">
                {new Date(p.created_at).toLocaleDateString()}
              </p>
            </div>
            <span className={`tag ${p.status === "accepted" ? "tag-accent" : ""}`}>{p.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
