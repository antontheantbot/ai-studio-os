import type { LucideIcon } from "lucide-react";

interface Props {
  icon: LucideIcon;
  message: string;
  sub?: string;
}

export default function EmptyState({ icon: Icon, message, sub }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <Icon size={32} strokeWidth={1} className="text-studio-border mb-4" />
      <p className="text-studio-text-muted text-sm">{message}</p>
      {sub && <p className="text-studio-border text-xs mt-1">{sub}</p>}
    </div>
  );
}
