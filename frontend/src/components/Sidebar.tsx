"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import {
  LayoutDashboard,
  Megaphone,
  Building2,
  Users,
  GraduationCap,
  Newspaper,
  FileText,
  BookOpen,
  MessageSquare,
} from "lucide-react";

const NAV = [
  { href: "/",              label: "Dashboard",    icon: LayoutDashboard },
  { href: "/opportunities", label: "Opportunities", icon: Megaphone },
  { href: "/architecture",  label: "Architecture",  icon: Building2 },
  { href: "/collectors",    label: "Collectors",    icon: Users },
  { href: "/curators",      label: "Curators",      icon: GraduationCap },
  { href: "/press",         label: "Press",         icon: Newspaper },
  { href: "/proposals",     label: "Proposals",     icon: FileText },
  { href: "/knowledge",     label: "Knowledge",     icon: BookOpen },
  { href: "/chat",          label: "Chat",          icon: MessageSquare },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-52 flex-shrink-0 bg-studio-surface border-r border-studio-border flex flex-col">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-studio-border">
        <div className="text-studio-accent font-medium text-sm tracking-widest uppercase">
          AI Studio OS
        </div>
        <div className="text-studio-text-muted text-xs mt-0.5">v0.1.0</div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 overflow-y-auto">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-3 px-4 py-2.5 text-xs transition-colors",
                active
                  ? "text-studio-accent bg-[#1a1a00] border-r-2 border-studio-accent"
                  : "text-studio-text-muted hover:text-studio-text hover:bg-white/5"
              )}
            >
              <Icon size={14} strokeWidth={1.5} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-studio-border text-xs text-studio-text-muted">
        <div className="flex items-center gap-2">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-studio-accent" />
          System online
        </div>
      </div>
    </aside>
  );
}
