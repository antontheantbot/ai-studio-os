---
name: aistudioos
description: Query the AI Studio OS database — search open calls, grants, residencies, contests, artists, journalists, collectors, curators, market briefs, color & size trends, architecture locations, get daily career actions, and ask the knowledge base. Use these tools when the user asks about art opportunities, press contacts, collectors, market trends, location scouting, or today's daily action.
metadata:
  {
    "openclaw": {
      "emoji": "🎨"
    }
  }
---

# AI Studio OS

Tools to query the AI Studio OS — a live database of art opportunities, grants, contests, artists, journalists, collectors, curators, architecture locations, daily career actions, and art market intelligence.

## When to use

| Tool | Use when |
|------|----------|
| `aistudioos_opportunities` | Finding open calls, residencies, commissions, festivals |
| `aistudioos_grants` | Finding funding and grant opportunities for artists |
| `aistudioos_contests` | Finding art contests and competitions with prizes |
| `aistudioos_artists` | Searching or listing digital artists |
| `aistudioos_journalists` | Finding journalists/critics covering art, culture, photography, architecture — includes email and social media |
| `aistudioos_collectors` | Finding art collectors — who buys digital/contemporary art |
| `aistudioos_curators` | Finding curators working with digital and contemporary art |
| `aistudioos_market_brief` | Getting the latest weekly art market brief (Christie's, Sotheby's, Art Basel, Pace, Artsy) |
| `aistudioos_color_trends` | Getting trending colors and artwork sizes in contemporary art |
| `aistudioos_architecture` | Scouting locations for installations or photography |
| `aistudioos_daily` | Getting today's daily career action for Ryan & Alice — one concrete task toward their goals |
| `aistudioos_chat` | Asking the AI Studio knowledge base a strategic question |

## Scripts

```bash
# Search open calls / residencies / commissions / festivals
node {baseDir}/scripts/opportunities.mjs
node {baseDir}/scripts/opportunities.mjs "digital art residency"

# Search grants
node {baseDir}/scripts/grants.mjs

# Search artists
node {baseDir}/scripts/artists.mjs "generative AI"

# Get latest market brief
node {baseDir}/scripts/briefs.mjs

# Search architecture locations
node {baseDir}/scripts/architecture.mjs "brutalist concrete"

# Ask the knowledge base
node {baseDir}/scripts/chat.mjs "Which collectors in Europe buy digital installations?"
node {baseDir}/scripts/chat.mjs "Who are the best journalists to pitch for a new media show?"
```
