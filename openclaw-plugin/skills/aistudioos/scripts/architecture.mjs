#!/usr/bin/env node
/**
 * aistudioos_architecture — Search architecture locations for installations/photography
 * Usage: node architecture.mjs [query] [--limit <n>]
 */
import { parseArgs } from "node:util";

const BASE = process.env.AISTUDIOOS_BASE_URL || "http://localhost/api/v1";

const { values, positionals } = parseArgs({
  args: process.argv.slice(2),
  options: { limit: { type: "string", short: "n", default: "15" } },
  allowPositionals: true,
  strict: false,
});

const query = positionals.join(" ").trim();
const limit = parseInt(values.limit, 10) || 15;

const params = new URLSearchParams({ limit: String(limit) });
if (query) params.set("q", query);

const res = await fetch(`${BASE}/architecture/?${params}`);
if (!res.ok) throw new Error(`API error ${res.status}`);
const items = await res.json();

if (!items.length) {
  console.log("No architecture locations found.");
  process.exit(0);
}

for (const loc of items) {
  const location = [loc.city, loc.country].filter(Boolean).join(", ");
  console.log(`\n## ${loc.name}${location ? ` — ${location}` : ""}`);
  if (loc.style) console.log(`Style: ${loc.style}${loc.year_built ? ` (${loc.year_built})` : ""}`);
  if (loc.architect) console.log(`Architect: ${loc.architect}`);
  if (loc.description) console.log(`\n${loc.description.slice(0, 250)}${loc.description.length > 250 ? "..." : ""}`);
  if (loc.suitability) console.log(`Suitability: ${Array.isArray(loc.suitability) ? loc.suitability.join(", ") : loc.suitability}`);
  if (loc.source_url) console.log(`URL: ${loc.source_url}`);
}
console.log(`\n---\nTotal: ${items.length} locations`);
