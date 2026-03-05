"use client";
import { useState } from "react";
import useSWR from "swr";
import { Users } from "lucide-react";
import PageHeader from "@/components/PageHeader";
import SearchBar from "@/components/SearchBar";
import EmptyState from "@/components/EmptyState";
import { getCollectors, type Collector } from "@/lib/api";

export default function CollectorsPage() {
  const [query, setQuery] = useState("");

  const { data, isLoading } = useSWR(
    ["collectors", query],
    () => getCollectors(query || undefined)
  );

  return (
    <div>
      <PageHeader
        title="Collector Intelligence"
        description="Database of art collectors and patrons"
      />

      <div className="mb-4">
        <SearchBar onSearch={setQuery} placeholder="Search by name, interests, location..." loading={isLoading} />
      </div>

      {isLoading && <p className="text-studio-text-muted text-xs">Loading...</p>}

      {!isLoading && (!data || data.length === 0) && (
        <EmptyState icon={Users} message="No collectors yet" sub="Add collectors via the API or Telegram bot" />
      )}

      <div className="space-y-3">
        {(data ?? []).map((c: Collector) => (
          <div key={c.id} className="card hover:border-studio-muted transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <h3 className="text-sm font-medium text-studio-text mb-1">{c.name}</h3>
                <p className="text-xs text-studio-text-muted line-clamp-2 mb-2">{c.bio}</p>
                <div className="flex gap-3 text-xs text-studio-text-muted mb-2">
                  {c.location && <span>📍 {c.location}</span>}
                </div>
                <div className="flex flex-wrap gap-1">
                  {c.interests?.slice(0, 4).map((i) => (
                    <span key={i} className="tag">{i}</span>
                  ))}
                  {c.institutions?.slice(0, 2).map((i) => (
                    <span key={i} className="tag-accent">{i}</span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
