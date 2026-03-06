#!/usr/bin/env node
/**
 * aistudioos_chat — Ask the AI Studio OS knowledge base a strategic question
 * Usage: node chat.mjs "Which collectors in Europe buy digital art?"
 */

const BASE = process.env.AISTUDIOOS_BASE_URL || "http://localhost/api/v1";

const message = process.argv.slice(2).join(" ").trim();
if (!message) {
  console.error("Usage: node chat.mjs \"your question here\"");
  process.exit(1);
}

const res = await fetch(`${BASE}/chat/`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message, history: [] }),
});

if (!res.ok) throw new Error(`API error ${res.status}: ${await res.text()}`);
const data = await res.json();

console.log(data.response);

if (data.sources?.length) {
  console.log(`\n---\nSources: ${data.sources.join(", ")}`);
}
