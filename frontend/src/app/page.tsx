"use client";
import useSWR from "swr";
import {
  Megaphone, Building2, Users, GraduationCap,
  Newspaper, FileText, BookOpen, RefreshCw,
} from "lucide-react";
import StatCard from "@/components/StatCard";
import PageHeader from "@/components/PageHeader";
import { triggerOpportunityScan } from "@/lib/api";
import { useState } from "react";

const fetcher = (url: string) => fetch(url).then((r) => r.json());

export default function Dashboard() {
  const { data: opportunities } = useSWR("/api/v1/opportunities/", fetcher);
  const { data: collectors } = useSWR("/api/v1/collectors/", fetcher);
  const { data: curators } = useSWR("/api/v1/curators/", fetcher);
  const { data: press } = useSWR("/api/v1/press/", fetcher);
  const { data: proposals } = useSWR("/api/v1/proposals/", fetcher);
  const { data: knowledge } = useSWR("/api/v1/knowledge/", fetcher);
  const { data: architecture } = useSWR("/api/v1/architecture/", fetcher);

  const [scanning, setScanning] = useState(false);

  const handleScan = async () => {
    setScanning(true);
    try {
      await triggerOpportunityScan();
    } finally {
      setTimeout(() => setScanning(false), 2000);
    }
  };

  const stats = [
    { label: "Open Opportunities", value: opportunities?.length ?? "—", icon: Megaphone, accent: true },
    { label: "Architecture Locations", value: architecture?.length ?? "—", icon: Building2 },
    { label: "Collectors", value: collectors?.length ?? "—", icon: Users },
    { label: "Curators", value: curators?.length ?? "—", icon: GraduationCap },
    { label: "Press Items", value: press?.length ?? "—", icon: Newspaper },
    { label: "Proposals", value: proposals?.length ?? "—", icon: FileText },
    { label: "Knowledge Items", value: knowledge?.length ?? "—", icon: BookOpen },
  ];

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Overview of your AI Studio OS"
        actions={
          <button
            onClick={handleScan}
            disabled={scanning}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw size={13} className={scanning ? "animate-spin" : ""} />
            {scanning ? "Scanning..." : "Scan Now"}
          </button>
        }
      />

      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3 mb-8">
        {stats.map((s) => (
          <StatCard key={s.label} {...s} />
        ))}
      </div>

      {/* Recent opportunities */}
      <div className="card">
        <h2 className="text-xs font-medium text-studio-text-muted uppercase tracking-widest mb-4">
          Recent Opportunities
        </h2>
        {!opportunities || opportunities.length === 0 ? (
          <p className="text-studio-text-muted text-xs">
            No opportunities yet — run a scan to populate.
          </p>
        ) : (
          <div className="divide-y divide-studio-border">
            {opportunities.slice(0, 8).map((o: any) => (
              <div key={o.id} className="py-3 flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-studio-text truncate">{o.title}</p>
                  <p className="text-xs text-studio-text-muted mt-0.5">{o.organizer} · {o.location}</p>
                </div>
                <div className="flex-shrink-0 text-right">
                  {o.deadline && (
                    <span className="tag-accent">{o.deadline}</span>
                  )}
                  {o.category && (
                    <span className="tag ml-1">{o.category}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
