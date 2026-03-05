"use client";
import { useState } from "react";
import useSWR from "swr";
import { Megaphone, ExternalLink, RefreshCw } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getOpportunities, triggerOpportunityScan, type Opportunity } from "@/lib/api";

const CATEGORIES = ["all", "open_call", "residency", "commission", "festival", "grant", "contest"];

export default function OpportunitiesPage() {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const [scanning, setScanning] = useState(false);

  const { data, isLoading, mutate } = useSWR(
    ["opportunities", query],
    () => getOpportunities(query || undefined)
  );

  const handleScan = async () => {
    setScanning(true);
    await triggerOpportunityScan();
    setTimeout(() => { setScanning(false); mutate(); }, 3000);
  };

  const today = new Date().toISOString().split("T")[0];
  const items = (data ?? []).filter(
    (o: Opportunity) =>
      (filter === "all" || o.category === filter) &&
      (!o.deadline || o.deadline >= today)
  );

  return (
    <div>
      <PageHeader
        title="Opportunities"
        description="Open calls, residencies, commissions and festivals"
        actions={
          <button onClick={handleScan} disabled={scanning} className="btn-primary flex items-center gap-2">
            <RefreshCw size={13} className={scanning ? "animate-spin" : ""} />
            {scanning ? "Scanning..." : "Scan"}
          </button>
        }
      />

      <div className="flex gap-3 mb-4">
        <div className="flex-1">
          <SearchBar onSearch={setQuery} placeholder="Search opportunities semantically..." loading={isLoading} />
        </div>
        <div className="flex gap-1">
          {CATEGORIES.map((c) => (
            <button
              key={c}
              onClick={() => setFilter(c)}
              className={`btn text-xs ${filter === c ? "btn-primary" : "btn-ghost"}`}
            >
              {c === "all" ? "All" : c.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      {isLoading && <p className="text-studio-text-muted text-xs">Loading...</p>}

      {!isLoading && items.length === 0 && (
        <EmptyState icon={Megaphone} message="No opportunities found" sub="Try scanning or adjusting your search" />
      )}

      <div className="space-y-3">
        {items.map((o: Opportunity) => (
          <div key={o.id} className="card hover:border-studio-muted transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="tag">{o.category?.replace("_", " ")}</span>
                  {o.is_active && <span className="tag-accent">Active</span>}
                </div>
                <h3 className="text-sm font-medium text-studio-text">{o.title}</h3>
                <p className="text-xs text-studio-text-muted mt-1 line-clamp-2">{o.description}</p>
                <div className="flex gap-4 mt-2 text-xs text-studio-text-muted">
                  {o.organizer && <span>{o.organizer}</span>}
                  {o.location && <span>📍 {o.location}{o.country ? `, ${o.country}` : ""}</span>}
                  {o.award && <span className="text-studio-accent">🏆 {o.award}</span>}
                </div>
                {o.tags?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {o.tags.slice(0, 5).map((t) => (
                      <span key={t} className="tag">{t}</span>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex-shrink-0 text-right space-y-2">
                {o.deadline && (
                  <div>
                    <div className="text-xs text-studio-text-muted">Deadline</div>
                    <div className="tag-accent">{o.deadline}</div>
                  </div>
                )}
                {o.fee && <div className="text-xs text-studio-text-muted">Fee: {o.fee}</div>}
                {o.url && (
                  <a href={o.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-studio-accent hover:underline">
                    <ExternalLink size={11} /> Apply
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
