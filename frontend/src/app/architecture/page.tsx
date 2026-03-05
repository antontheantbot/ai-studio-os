"use client";
import { useState } from "react";
import useSWR from "swr";
import { Building2, ExternalLink, RefreshCw } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getArchitecture, triggerArchitectureScan, type ArchitectureLocation } from "@/lib/api";

export default function ArchitecturePage() {
  const [query, setQuery] = useState("");
  const [scanning, setScanning] = useState(false);

  const { data, isLoading, mutate } = useSWR(
    ["architecture", query],
    () => getArchitecture(query || undefined)
  );

  const handleScan = async () => {
    setScanning(true);
    await triggerArchitectureScan();
    setTimeout(() => { setScanning(false); mutate(); }, 3000);
  };

  return (
    <div>
      <PageHeader
        title="Architecture Scout"
        description="Locations scouted for photography and installations"
        actions={
          <button onClick={handleScan} disabled={scanning} className="btn-primary flex items-center gap-2">
            <RefreshCw size={13} className={scanning ? "animate-spin" : ""} />
            {scanning ? "Scanning..." : "Scan Web"}
          </button>
        }
      />

      <div className="mb-4">
        <SearchBar onSearch={setQuery} placeholder="Search by style, city, suitability..." loading={isLoading} />
      </div>

      {isLoading && <p className="text-studio-text-muted text-xs">Loading...</p>}

      {!isLoading && (!data || data.length === 0) && (
        <EmptyState icon={Building2} message="No locations scouted yet" sub="Click Scan Web to search the internet for architecture locations" />
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {(data ?? []).map((loc: ArchitectureLocation) => (
          <div key={loc.id} className="card hover:border-studio-muted transition-colors">
            <div className="flex items-start justify-between gap-2 mb-2">
              <h3 className="text-sm font-medium text-studio-text">{loc.name}</h3>
              {loc.source_url && (
                <a href={loc.source_url} target="_blank" rel="noopener noreferrer"
                  className="text-studio-text-muted hover:text-studio-accent">
                  <ExternalLink size={12} />
                </a>
              )}
            </div>
            <p className="text-xs text-studio-text-muted line-clamp-2 mb-3">{loc.description}</p>
            <div className="flex flex-wrap gap-2 text-xs text-studio-text-muted mb-3">
              {loc.city && <span>📍 {loc.city}{loc.country ? `, ${loc.country}` : ""}</span>}
              {loc.architect && <span>🏛 {loc.architect}</span>}
              {loc.year_built && <span>{loc.year_built}</span>}
            </div>
            <div className="flex flex-wrap gap-1">
              {loc.style && <span className="tag">{loc.style}</span>}
              {loc.suitability?.map((s) => (
                <span key={s} className="tag-accent">{s}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
