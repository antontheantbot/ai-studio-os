#!/usr/bin/env node
/**
 * aistudioos_artists — Search digital artists in the studio database
 * Usage: node artists.mjs [query] [--limit <n>]
 */
import { parseArgs } from "node:util";

const BASE = process.env.AISTUDIOOS_BASE_URL || "http://localhost/api/v1";

const { values, positionals } = parseArgs({
  args: process.argv.slice(2),
  options: { limit: { type: "string", short: "n", default: "20" } },
  allowPositionals: true,
  strict: false,
});

const query = positionals.join(" ").trim();
const limit = parseInt(values.limit, 10) || 20;

const params = new URLSearchParams({ limit: String(limit) });
if (query) params.set("q", query);

const res = await fetch(`${BASE}/artists/?${params}`);
if (!res.ok) throw new Error(`API error ${res.status}`);
const items = await res.json();

if (!items.length) {
  console.log("No artists found.");
  process.exit(0);
}

for (const a of items) {
  const location = [a.city, a.country].filter(Boolean).join(", ");
  console.log(`\n## ${a.name}${location ? ` — ${location}` : ""}`);
  if (a.medium?.length) console.log(`Medium: ${a.medium.join(", ")}`);
  if (a.bio) console.log(`\n${a.bio.slice(0, 250)}${a.bio.length > 250 ? "..." : ""}`);
  if (a.website) console.log(`Web: ${a.website}`);
  if (a.instagram) console.log(`Instagram: ${a.instagram}`);
}
console.log(`\n---\nTotal: ${items.length} artists`);
