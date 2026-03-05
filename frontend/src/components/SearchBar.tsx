"use client";
import { useState } from "react";
import { Search } from "lucide-react";

interface Props {
  onSearch: (q: string) => void;
  placeholder?: string;
  loading?: boolean;
}

export default function SearchBar({ onSearch, placeholder = "Semantic search...", loading }: Props) {
  const [value, setValue] = useState("");

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") onSearch(value);
  };

  return (
    <div className="relative">
      <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-studio-text-muted" />
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={loading}
        className="pl-9 pr-4"
      />
    </div>
  );
}
