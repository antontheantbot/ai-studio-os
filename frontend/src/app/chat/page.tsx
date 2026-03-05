"use client";
import { useState, useRef, useEffect } from "react";
import { Send, Loader2, Bot, User } from "lucide-react";
import clsx from "clsx";
import { chat, type ChatMessage } from "@/lib/api";

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((m) => [...m, userMsg]);
    setLoading(true);
    try {
      const res = await chat(text, messages);
      const assistantMsg: ChatMessage = { role: "assistant", content: res.response };
      setMessages((m) => [...m, assistantMsg]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", content: "Error: could not reach the API." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-3rem)]">
      <div className="mb-4">
        <h1 className="text-lg font-medium text-studio-text">Studio Assistant</h1>
        <p className="text-xs text-studio-text-muted mt-1">
          Ask about opportunities, collectors, curators, press, or your knowledge base
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <div className="text-center py-20">
            <Bot size={32} strokeWidth={1} className="text-studio-border mx-auto mb-3" />
            <p className="text-studio-text-muted text-sm">How can I help with your studio today?</p>
            <div className="mt-4 flex flex-col items-center gap-2">
              {[
                "Find open calls with no fee deadline this month",
                "Which collectors focus on digital art?",
                "Summarise recent Artforum coverage",
                "Help me write a proposal for a residency in Berlin",
              ].map((hint) => (
                <button
                  key={hint}
                  onClick={() => { setInput(hint); }}
                  className="text-xs text-studio-text-muted border border-studio-border rounded px-3 py-1.5 hover:border-studio-muted hover:text-studio-text transition-colors"
                >
                  {hint}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={clsx("flex gap-3", m.role === "user" ? "justify-end" : "justify-start")}>
            {m.role === "assistant" && (
              <div className="w-6 h-6 rounded bg-studio-accent/10 flex items-center justify-center flex-shrink-0 mt-1">
                <Bot size={12} className="text-studio-accent" />
              </div>
            )}
            <div className={clsx(
              "max-w-[75%] rounded-lg px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
              m.role === "user"
                ? "bg-studio-accent text-black"
                : "bg-studio-surface border border-studio-border text-studio-text"
            )}>
              {m.content}
            </div>
            {m.role === "user" && (
              <div className="w-6 h-6 rounded bg-white/10 flex items-center justify-center flex-shrink-0 mt-1">
                <User size={12} className="text-studio-text" />
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="w-6 h-6 rounded bg-studio-accent/10 flex items-center justify-center flex-shrink-0">
              <Bot size={12} className="text-studio-accent" />
            </div>
            <div className="bg-studio-surface border border-studio-border rounded-lg px-4 py-3">
              <Loader2 size={14} className="animate-spin text-studio-text-muted" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2 pt-3 border-t border-studio-border">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask anything about your studio… (Enter to send, Shift+Enter for newline)"
          rows={2}
          className="resize-none text-sm"
          disabled={loading}
        />
        <button
          onClick={send}
          disabled={!input.trim() || loading}
          className="btn-primary flex-shrink-0 flex items-center justify-center w-10 h-10 self-end"
        >
          <Send size={14} />
        </button>
      </div>
    </div>
  );
}
