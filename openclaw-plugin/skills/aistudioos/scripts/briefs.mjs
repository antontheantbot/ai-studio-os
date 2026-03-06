#!/usr/bin/env node
/**
 * aistudioos_briefs — Get the latest art market brief
 * Usage: node briefs.mjs
 */

const BASE = process.env.AISTUDIOOS_BASE_URL || "http://localhost/api/v1";

const res = await fetch(`${BASE}/briefs/latest`);
if (!res.ok) throw new Error(`API error ${res.status}`);
const brief = await res.json();

if (!brief || !brief.brief) {
  console.log("No market brief available yet. Trigger a scan via POST /api/v1/briefs/scan");
  process.exit(0);
}

console.log(`# ${brief.title}`);
console.log(`Week of: ${brief.week_of}`);

if (brief.top_mediums?.length) {
  console.log(`\nTrending mediums: ${brief.top_mediums.join(", ")}`);
}
if (brief.top_artists?.length) {
  console.log(`Market momentum: ${brief.top_artists.join(", ")}`);
}
if (brief.signals?.length) {
  const strong = brief.signals.filter(s => s.strength === "strong").length;
  const moderate = brief.signals.filter(s => s.strength === "moderate").length;
  const emerging = brief.signals.filter(s => s.strength === "emerging").length;
  console.log(`Signals: ${strong} strong, ${moderate} moderate, ${emerging} emerging`);
}

console.log(`\n---\n`);
console.log(brief.brief);

if (brief.sources?.length) {
  console.log(`\n---\nSources: ${brief.sources.slice(0, 5).join(", ")}`);
}
