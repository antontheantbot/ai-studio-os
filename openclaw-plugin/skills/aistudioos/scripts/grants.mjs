#!/usr/bin/env node
/**
 * aistudioos_grants — Search art grants and funding opportunities
 * Usage: node grants.mjs [query] [--limit <n>]
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

const params = new URLSearchParams({ upcoming_only: "true", limit: String(limit) });
if (query) params.set("q", query);

const res = await fetch(`${BASE}/opportunities/?${params}`);
if (!res.ok) throw new Error(`API error ${res.status}`);
const all = await res.json();
const items = all.filter(o => o.category === "grant");

if (!items.length) {
  console.log("No grants found. Try scanning: POST /api/v1/opportunities/scan");
  process.exit(0);
}

for (const o of items) {
  const deadline = o.deadline ? ` | Deadline: ${o.deadline}` : "";
  const award = o.award ? ` | Award: ${o.award}` : "";
  console.log(`\n## ${o.title}`);
  console.log(`Grant${deadline}${award}`);
  if (o.organizer) console.log(`Organizer: ${o.organizer}`);
  if (o.description) console.log(`\n${o.description.slice(0, 300)}${o.description.length > 300 ? "..." : ""}`);
  if (o.url) console.log(`URL: ${o.url}`);
}
console.log(`\n---\nTotal: ${items.length} grants`);
