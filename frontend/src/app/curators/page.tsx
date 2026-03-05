"use client";
import { useState } from "react";
import useSWR from "swr";
import { GraduationCap } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getCurators, type Curator } from "@/lib/api";

export default function CuratorsPage() {
  const [query, setQuery] = useState("");

  const { data, isLoading } = useSWR(
    ["curators", query],
    () => getCurators(query || undefined)
  );

  return (
    <div>
      <PageHeader
        title="Curator Intelligence"
        description="Database of curators and institutions"
      />

      <div className="mb-4">
        <SearchBar onSearch={setQuery} placeholder="Search by name, institution, focus..." loading={isLoading} />
      </div>

      {isLoading && <p className="text-studio-text-muted text-xs">Loading...</p>}

      {!isLoading && (!data || data.length === 0) && (
        <EmptyState icon={GraduationCap} message="No curators yet" sub="Add curators via the API or Telegram bot" />
      )}

      <div className="space-y-3">
        {(data ?? []).map((c: Curator) => (
          <div key={c.id} className="card hover:border-studio-muted transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-medium text-studio-text">{c.name}</h3>
                  {c.role && <span className="tag">{c.role}</span>}
                </div>
                {c.institution && (
                  <p className="text-xs text-studio-accent mb-1">{c.institution}</p>
                )}
                <p className="text-xs text-studio-text-muted line-clamp-2 mb-2">{c.bio}</p>
                <div className="flex flex-wrap gap-1">
                  {c.focus_areas?.slice(0, 5).map((f) => (
                    <span key={f} className="tag">{f}</span>
                  ))}
                </div>
                {c.notable_shows?.length > 0 && (
                  <div className="mt-2 text-xs text-studio-text-muted">
                    Shows: {c.notable_shows.slice(0, 3).join(" · ")}
                  </div>
                )}
              </div>
              {c.location && (
                <span className="text-xs text-studio-text-muted flex-shrink-0">📍 {c.location}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
