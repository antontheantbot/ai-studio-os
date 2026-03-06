#!/usr/bin/env node
/**
 * aistudioos_opportunities — Search open calls, residencies, commissions, festivals
 * Usage: node opportunities.mjs [query] [--category <type>] [--limit <n>]
 */
import { parseArgs } from "node:util";

const BASE = process.env.AISTUDIOOS_BASE_URL || "http://localhost/api/v1";

const { values, positionals } = parseArgs({
  args: process.argv.slice(2),
  options: {
    category: { type: "string", short: "c" },
    limit: { type: "string", short: "n", default: "20" },
  },
  allowPositionals: true,
  strict: false,
});

const query = positionals.join(" ").trim();
const category = values.category;
const limit = parseInt(values.limit, 10) || 20;

const params = new URLSearchParams({ upcoming_only: "true", limit: String(limit) });
if (query) params.set("q", query);

const res = await fetch(`${BASE}/opportunities/?${params}`);
if (!res.ok) throw new Error(`API error ${res.status}`);
let items = await res.json();

if (category) {
  items = items.filter(o => o.category === category);
}

if (!items.length) {
  console.log("No opportunities found.");
  process.exit(0);
}

for (const o of items) {
  const deadline = o.deadline ? ` | Deadline: ${o.deadline}` : "";
  const award = o.award ? ` | Award: ${o.award}` : "";
  const fee = o.fee ? ` | Fee: ${o.fee}` : "";
  console.log(`\n## ${o.title}`);
  console.log(`Category: ${o.category || "—"}${deadline}${award}${fee}`);
  if (o.organizer) console.log(`Organizer: ${o.organizer}`);
  if (o.location) console.log(`Location: ${o.location}${o.country ? `, ${o.country}` : ""}`);
  if (o.description) console.log(`\n${o.description.slice(0, 300)}${o.description.length > 300 ? "..." : ""}`);
  if (o.url) console.log(`URL: ${o.url}`);
}
console.log(`\n---\nTotal: ${items.length} opportunities`);
