"use client";
import { useState } from "react";
import useSWR from "swr";
import { Building2, ExternalLink } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getArchitecture, type ArchitectureLocation } from "@/lib/api";

export default function ArchitecturePage() {
  const [query, setQuery] = useState("");

  const { data, isLoading } = useSWR(
    ["architecture", query],
    () => getArchitecture(query || undefined)
  );

  return (
    <div>
      <PageHeader
        title="Architecture Scout"
        description="Locations scouted for photography and installations"
      />

      <div className="mb-4">
        <SearchBar onSearch={setQuery} placeholder="Search by style, city, suitability..." loading={isLoading} />
      </div>

      {isLoading && <p className="text-studio-text-muted text-xs">Loading...</p>}

      {!isLoading && (!data || data.length === 0) && (
        <EmptyState icon={Building2} message="No locations scouted yet" sub="The scout agent runs weekly — trigger it manually via API" />
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
