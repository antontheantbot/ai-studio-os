import clsx from "clsx";
import type { LucideIcon } from "lucide-react";

interface Props {
  label: string;
  value: string | number;
  icon: LucideIcon;
  accent?: boolean;
  sub?: string;
}

export default function StatCard({ label, value, icon: Icon, accent, sub }: Props) {
  return (
    <div className={clsx("card flex items-start gap-4", accent && "border-studio-accent/40")}>
      <div className={clsx(
        "p-2 rounded",
        accent ? "bg-studio-accent/10 text-studio-accent" : "bg-white/5 text-studio-text-muted"
      )}>
        <Icon size={16} strokeWidth={1.5} />
      </div>
      <div>
        <div className="text-2xl font-medium text-studio-text">{value}</div>
        <div className="text-xs text-studio-text-muted mt-0.5">{label}</div>
        {sub && <div className="text-xs text-studio-accent mt-1">{sub}</div>}
      </div>
    </div>
  );
}
