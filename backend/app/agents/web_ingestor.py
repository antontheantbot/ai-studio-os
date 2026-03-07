"""
Web Ingestor — Tavily-powered scanner for all database categories.
Searches the open web for architecture locations, collectors, curators,
press coverage, and knowledge items relevant to digital installation art.
"""
import json
import logging
from datetime import datetime

from sqlalchemy import text
from tavily import AsyncTavilyClient

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.embeddings import embed
from app.services.llm import generate

logger = logging.getLogger(__name__)

# ─── Search query banks ─────────────────────────────────────────────────────

ARCHITECTURE_QUERIES = [
    "brutalist architecture buildings photography locations Europe",
    "modernist concrete architecture installation art suitable",
    "abandoned industrial architecture site-specific art installation",
    "deconstructivist architecture landmark public space",
    "monumental public architecture digital projection mapping",
    "soviet brutalist architecture Eastern Europe",
    "contemporary museum architecture space for digital art",
    "iconic building facade LED projection mapping installation",
]

COLLECTOR_QUERIES = [
    "digital art collector new media art collection 2026",
    "who collects AI generative art collectors list",
    "NFT art collector traditional digital art collection",
    "new media art collector interview acquisition 2026",
    "technology art collector Silicon Valley Europe",
    "immersive installation art private collector",
]

CURATOR_QUERIES = [
    "curator digital art new media exhibition 2026",
    "museum curator artificial intelligence art show",
    "new media art curator interview profile",
    "digital installation curator biennale exhibition",
    "curator generative art immersive experience",
]

PRESS_QUERIES = [
    "digital art news 2026 new media exhibition review",
    "AI art controversy museum acquisition 2026",
    "immersive installation art review opening 2026",
    "generative art press coverage critical review 2026",
    "new media art biennale coverage 2026",
    "technology art world news 2026",
    "digital artist interview profile 2026",
]

JOURNALIST_QUERIES = [
    "art critic journalist writer Artforum Frieze contact email",
    "contemporary art journalist writer profile publication 2026",
    "architecture critic journalist writer publication contact",
    "culture journalist writer art photography publication email",
    "art writer freelance journalist New York Times Guardian Artsy",
    "photography critic journalist publication portfolio contact",
    "art market journalist writer contact publication",
    "contemporary art blogger writer social media publication",
]

KNOWLEDGE_QUERIES = [
    "how to write artist residency proposal digital art",
    "art world guide digital installation artist career",
    "how to approach galleries new media art collectors",
    "digital art market report 2026 prices trends",
    "immersive art production budget planning guide",
    "artist statement examples digital new media art",
    "art fair strategy digital media artist guide",
]

# ─── Extraction prompts ──────────────────────────────────────────────────────

ARCHITECTURE_PROMPT = """From these search results, extract notable architecture locations suitable for digital art installations or photography.
Return a JSON array with fields:
- name (string, building/location name)
- description (string, 2-3 sentences)
- architect (string or null)
- city (string)
- country (string)
- style (string, e.g. "brutalist", "modernist", "deconstructivist")
- year_built (string or null)
- suitability (string, why it suits installations/photography)
- source_url (string, URL of source)
- photography_score (integer 1-10)
- historical_significance (string, 1-2 sentences or null)

Only include real, named buildings or locations. Return [] if none found.

Search results:
{results}"""

COLLECTOR_PROMPT = """From these search results, extract profiles of art collectors who collect digital, new media, or technology-based art.
Return a JSON array with fields:
- name (string, full name)
- bio (string, 2-3 sentences about their collecting focus)
- location (string, city)
- country (string)
- interests (array of strings, e.g. ["digital art", "AI art", "new media"])
- known_works (array of strings, artworks or artists they collect)
- institutions (array of strings, museum boards or foundations they support)
- notes (string, additional context or null)

Only include real, named collectors with verifiable digital art interests. Return [] if none found.

Search results:
{results}"""

CURATOR_PROMPT = """From these search results, extract profiles of curators who work with digital, new media, or technology-based art.
Return a JSON array with fields:
- name (string, full name)
- bio (string, 2-3 sentences)
- institution (string, primary institution or "Independent")
- role (string, e.g. "Senior Curator", "Chief Curator")
- location (string, city)
- country (string)
- focus_areas (array of strings, e.g. ["digital art", "AI", "immersive installations"])
- notable_shows (array of strings, exhibitions they have curated)
- notes (string or null)

Only include real, named curators. Return [] if none found.

Search results:
{results}"""

PRESS_PROMPT = """From these search results, extract press articles and reviews about digital art, new media, or technology-based art.
Return a JSON array with fields:
- title (string, article title)
- summary (string, 2-3 sentence summary)
- source (string, publication name e.g. "Artforum", "Frieze")
- author (string or null)
- url (string, direct article URL)
- published_at (string, ISO date YYYY-MM-DD or null)
- category (string: "review", "news", "interview", or "feature")
- tags (array of strings)
- mentioned_artists (array of strings, artist names mentioned)

Only include real articles from identifiable publications. Return [] if none found.

Search results:
{results}"""

JOURNALIST_PROMPT = """From these search results, extract profiles of journalists, critics, and writers who cover contemporary art, culture, photography, or architecture.
Return a JSON array with fields:
- name (string, full name)
- bio (string, 2-3 sentences about their focus and work)
- publications (array of strings, publications or outlets they write for e.g. ["Artforum", "The Guardian", "Frieze"])
- beats (array of strings, topics they cover e.g. ["contemporary art", "architecture", "photography", "culture"])
- email (string, publicly listed email address or null — only include if clearly public)
- social_links (object with any of: twitter, instagram, linkedin, website — use public profile URLs)
- location (string, city or null)
- country (string or null)
- notes (string, any useful context e.g. "covers emerging artists" or null)

Only include real, named journalists with verifiable work. Prioritise those who cover art, culture, architecture or photography. Return [] if none found.

Search results:
{results}"""

KNOWLEDGE_PROMPT = """From these search results, extract useful knowledge, guides, or resources relevant to a digital installation artist's career.
Return a JSON array with fields:
- title (string, descriptive title for this knowledge item)
- content (string, detailed useful content — extract as much relevant text as possible, 200-500 words)
- summary (string, 1-2 sentence summary)
- source_type (string: "article", "guide", "report", "interview", or "resource")
- source_url (string, URL)
- author (string or null)
- tags (array of strings)

Only include genuinely useful, substantive content. Return [] if none found.

Search results:
{results}"""


class WebIngestor:
    def __init__(self):
        self.client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)

    async def _search(self, query: str, max_results: int = 7) -> str:
        """Run a Tavily search and format results for Claude."""
        response = await self.client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=False,
        )
        results = response.get("results", [])
        return "\n\n".join(
            f"Title: {r.get('title', '')}\nURL: {r.get('url', '')}\nContent: {r.get('content', '')[:700]}"
            for r in results
        )

    async def _extract(self, prompt: str, results_text: str) -> list[dict]:
        """Run Claude extraction on search results."""
        raw = await generate(prompt.format(results=results_text))
        start, end = raw.find("["), raw.rfind("]")
        if start == -1 or end == -1 or end <= start:
            return []
        try:
            return json.loads(raw[start:end + 1])
        except json.JSONDecodeError:
            return []

    # ─── Architecture ────────────────────────────────────────────────────────

    async def scan_architecture(self) -> int:
        total = 0
        seen = set()
        for query in ARCHITECTURE_QUERIES:
            try:
                results_text = await self._search(query)
                items = await self._extract(ARCHITECTURE_PROMPT, results_text)
                count = await self._save_architecture(items, seen)
                total += count
                logger.info(f"[WebIngestor/Architecture] '{query}': {count} saved")
            except Exception as e:
                logger.error(f"[WebIngestor/Architecture] Failed '{query}': {e}")
        return total

    async def _save_architecture(self, items: list[dict], seen: set) -> int:
        saved = 0
        async with AsyncSessionLocal() as db:
            for item in items:
                url = item.get("source_url", "")
                name = item.get("name", "")
                if not name or url in seen:
                    continue
                exists = await db.execute(
                    text("SELECT id FROM architecture_locations WHERE name = :name AND city = :city"),
                    {"name": name, "city": item.get("city", "")}
                )
                if exists.first():
                    continue
                embed_text = f"{name} {item.get('city', '')} {item.get('style', '')} {item.get('description', '')}"
                embedding = await embed(embed_text)
                embedding_str = f"[{','.join(str(x) for x in embedding)}]"
                await db.execute(text("""
                    INSERT INTO architecture_locations
                        (name, description, architect, city, country, style, year_built,
                         suitability, source_url, photography_score, historical_significance, embedding)
                    VALUES
                        (:name, :description, :architect, :city, :country, :style, :year_built,
                         :suitability, :source_url, :photography_score, :historical_significance,
                         CAST(:embedding AS vector))
                    ON CONFLICT DO NOTHING
                """), {
                    "name": name,
                    "description": item.get("description"),
                    "architect": item.get("architect"),
                    "city": item.get("city"),
                    "country": item.get("country"),
                    "style": item.get("style"),
                    "year_built": item.get("year_built"),
                    "suitability": item.get("suitability"),
                    "source_url": url or None,
                    "photography_score": item.get("photography_score"),
                    "historical_significance": item.get("historical_significance"),
                    "embedding": embedding_str,
                })
                saved += 1
                if url:
                    seen.add(url)
            await db.commit()
        return saved

    # ─── Collectors ──────────────────────────────────────────────────────────

    async def scan_collectors(self) -> int:
        total = 0
        seen_names = set()
        for query in COLLECTOR_QUERIES:
            try:
                results_text = await self._search(query)
                items = await self._extract(COLLECTOR_PROMPT, results_text)
                count = await self._save_collectors(items, seen_names)
                total += count
                logger.info(f"[WebIngestor/Collectors] '{query}': {count} saved")
            except Exception as e:
                logger.error(f"[WebIngestor/Collectors] Failed '{query}': {e}")
        return total

    async def _save_collectors(self, items: list[dict], seen: set) -> int:

        saved = 0
        async with AsyncSessionLocal() as db:
            for item in items:
                name = item.get("name", "")
                if not name or name in seen:
                    continue
                exists = await db.execute(
                    text("SELECT id FROM collectors WHERE name = :name"), {"name": name}
                )
                if exists.first():
                    seen.add(name)
                    continue
                embed_text = f"{name} {item.get('bio', '')} {' '.join(item.get('interests', []))}"
                embedding = await embed(embed_text)
                embedding_str = f"[{','.join(str(x) for x in embedding)}]"
                await db.execute(text("""
                    INSERT INTO collectors
                        (name, bio, location, country, interests, known_works,
                         institutions, notes, social_links, embedding)
                    VALUES
                        (:name, :bio, :location, :country, :interests, :known_works,
                         :institutions, :notes, CAST(:social_links AS jsonb), CAST(:embedding AS vector))
                    ON CONFLICT DO NOTHING
                """), {
                    "name": name,
                    "bio": item.get("bio"),
                    "location": item.get("location"),
                    "country": item.get("country"),
                    "interests": item.get("interests", []),
                    "known_works": item.get("known_works", []),
                    "institutions": item.get("institutions", []),
                    "notes": item.get("notes"),
                    "social_links": json.dumps({}),
                    "embedding": embedding_str,
                })
                saved += 1
                seen.add(name)
            await db.commit()
        return saved

    # ─── Curators ────────────────────────────────────────────────────────────

    async def scan_curators(self) -> int:
        total = 0
        seen_names = set()
        for query in CURATOR_QUERIES:
            try:
                results_text = await self._search(query)
                items = await self._extract(CURATOR_PROMPT, results_text)
                count = await self._save_curators(items, seen_names)
                total += count
                logger.info(f"[WebIngestor/Curators] '{query}': {count} saved")
            except Exception as e:
                logger.error(f"[WebIngestor/Curators] Failed '{query}': {e}")
        return total

    async def _save_curators(self, items: list[dict], seen: set) -> int:

        saved = 0
        async with AsyncSessionLocal() as db:
            for item in items:
                name = item.get("name", "")
                if not name or name in seen:
                    continue
                exists = await db.execute(
                    text("SELECT id FROM curators WHERE name = :name"), {"name": name}
                )
                if exists.first():
                    seen.add(name)
                    continue
                embed_text = f"{name} {item.get('institution', '')} {item.get('bio', '')} {' '.join(item.get('focus_areas', []))}"
                embedding = await embed(embed_text)
                embedding_str = f"[{','.join(str(x) for x in embedding)}]"
                await db.execute(text("""
                    INSERT INTO curators
                        (name, bio, institution, role, location, country,
                         focus_areas, notable_shows, notes, social_links, embedding)
                    VALUES
                        (:name, :bio, :institution, :role, :location, :country,
                         :focus_areas, :notable_shows, :notes, CAST(:social_links AS jsonb),
                         CAST(:embedding AS vector))
                    ON CONFLICT DO NOTHING
                """), {
                    "name": name,
                    "bio": item.get("bio"),
                    "institution": item.get("institution"),
                    "role": item.get("role"),
                    "location": item.get("location"),
                    "country": item.get("country"),
                    "focus_areas": item.get("focus_areas", []),
                    "notable_shows": item.get("notable_shows", []),
                    "notes": item.get("notes"),
                    "social_links": json.dumps({}),
                    "embedding": embedding_str,
                })
                saved += 1
                seen.add(name)
            await db.commit()
        return saved

    # ─── Press ───────────────────────────────────────────────────────────────

    async def scan_press(self) -> int:
        total = 0
        seen_urls = set()
        for query in PRESS_QUERIES:
            try:
                results_text = await self._search(query)
                items = await self._extract(PRESS_PROMPT, results_text)
                count = await self._save_press(items, seen_urls)
                total += count
                logger.info(f"[WebIngestor/Press] '{query}': {count} saved")
            except Exception as e:
                logger.error(f"[WebIngestor/Press] Failed '{query}': {e}")
        return total

    async def _save_press(self, items: list[dict], seen: set) -> int:
        saved = 0
        async with AsyncSessionLocal() as db:
            for item in items:
                url = item.get("url", "")
                if not item.get("title") or not url or url in seen:
                    continue
                exists = await db.execute(
                    text("SELECT id FROM press_items WHERE url = :url"), {"url": url}
                )
                if exists.first():
                    seen.add(url)
                    continue
                published_at = None
                if item.get("published_at"):
                    try:
                        published_at = datetime.fromisoformat(item["published_at"][:10])
                    except (ValueError, TypeError):
                        pass
                embed_text = f"{item['title']} {item.get('summary', '')}"
                embedding = await embed(embed_text)
                embedding_str = f"[{','.join(str(x) for x in embedding)}]"
                await db.execute(text("""
                    INSERT INTO press_items
                        (title, summary, source, author, url, published_at,
                         category, tags, mentioned_artists, embedding)
                    VALUES
                        (:title, :summary, :source, :author, :url, :published_at,
                         :category, :tags, :mentioned_artists, CAST(:embedding AS vector))
                    ON CONFLICT (url) DO NOTHING
                """), {
                    "title": item["title"],
                    "summary": item.get("summary"),
                    "source": item.get("source"),
                    "author": item.get("author"),
                    "url": url,
                    "published_at": published_at,
                    "category": item.get("category", "news"),
                    "tags": item.get("tags", []),
                    "mentioned_artists": item.get("mentioned_artists", []),
                    "embedding": embedding_str,
                })
                saved += 1
                seen.add(url)
            await db.commit()
        return saved

    # ─── Knowledge ───────────────────────────────────────────────────────────

    async def scan_knowledge(self) -> int:
        total = 0
        seen_urls = set()
        for query in KNOWLEDGE_QUERIES:
            try:
                results_text = await self._search(query)
                items = await self._extract(KNOWLEDGE_PROMPT, results_text)
                count = await self._save_knowledge(items, seen_urls)
                total += count
                logger.info(f"[WebIngestor/Knowledge] '{query}': {count} saved")
            except Exception as e:
                logger.error(f"[WebIngestor/Knowledge] Failed '{query}': {e}")
        return total

    async def _save_knowledge(self, items: list[dict], seen: set) -> int:
        saved = 0
        async with AsyncSessionLocal() as db:
            for item in items:
                url = item.get("source_url", "")
                if not item.get("title") or url in seen:
                    continue
                exists = await db.execute(
                    text("SELECT id FROM knowledge_items WHERE title = :title"),
                    {"title": item["title"]}
                )
                if exists.first():
                    if url:
                        seen.add(url)
                    continue
                embed_text = f"{item['title']} {item.get('content', '')[:500]}"
                embedding = await embed(embed_text)
                embedding_str = f"[{','.join(str(x) for x in embedding)}]"
                await db.execute(text("""
                    INSERT INTO knowledge_items
                        (title, content, summary, source_type, source_url, author, tags, embedding)
                    VALUES
                        (:title, :content, :summary, :source_type, :source_url, :author,
                         :tags, CAST(:embedding AS vector))
                    ON CONFLICT DO NOTHING
                """), {
                    "title": item["title"],
                    "content": item.get("content"),
                    "summary": item.get("summary"),
                    "source_type": item.get("source_type", "article"),
                    "source_url": url or None,
                    "author": item.get("author"),
                    "tags": item.get("tags", []),
                    "embedding": embedding_str,
                })
                saved += 1
                if url:
                    seen.add(url)
            await db.commit()
        return saved

    # ─── Journalists ─────────────────────────────────────────────────────────

    async def scan_journalists(self) -> int:

        total = 0
        seen_names: set = set()
        for query in JOURNALIST_QUERIES:
            try:
                results_text = await self._search(query)
                items = await self._extract(JOURNALIST_PROMPT, results_text)
                count = await self._save_journalists(items, seen_names)
                total += count
                logger.info(f"[WebIngestor/Journalists] '{query}': {count} saved")
            except Exception as e:
                logger.error(f"[WebIngestor/Journalists] Failed '{query}': {e}")
        return total

    async def _save_journalists(self, items: list[dict], seen: set) -> int:

        saved = 0
        async with AsyncSessionLocal() as db:
            for item in items:
                name = item.get("name", "").strip()
                if not name or name in seen:
                    continue
                exists = await db.execute(
                    text("SELECT id FROM journalists WHERE name = :name"), {"name": name}
                )
                if exists.first():
                    seen.add(name)
                    continue
                embed_text = f"{name} {' '.join(item.get('publications', []))} {item.get('bio', '')} {' '.join(item.get('beats', []))}"
                embedding = await embed(embed_text)
                embedding_str = f"[{','.join(str(x) for x in embedding)}]"
                await db.execute(text("""
                    INSERT INTO journalists
                        (id, name, bio, publications, beats, email, social_links, location, country, notes)
                    VALUES
                        (gen_random_uuid(), :name, :bio, CAST(:publications AS jsonb), CAST(:beats AS jsonb),
                         :email, CAST(:social_links AS jsonb), :location, :country, :notes)
                    ON CONFLICT (name) DO NOTHING
                """), {
                    "name": name,
                    "bio": item.get("bio"),
                    "publications": json.dumps(item.get("publications") or []),
                    "beats": json.dumps(item.get("beats") or []),
                    "email": item.get("email"),
                    "social_links": json.dumps(item.get("social_links") or {}),
                    "location": item.get("location"),
                    "country": item.get("country"),
                    "notes": item.get("notes"),
                })
                saved += 1
                seen.add(name)
            await db.commit()
        return saved

    # ─── Journalist enrichment ───────────────────────────────────────────────

    async def enrich_journalists(self, batch_size: int = 20) -> int:
        """
        For journalists missing email/contact info, search the web and update them.
        Processes up to batch_size journalists per run, oldest-first.
        Never removes existing data — only fills in null fields.
        """
        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                SELECT id, name, publications, beats
                FROM journalists
                WHERE email IS NULL
                ORDER BY created_at ASC
                LIMIT :limit
            """), {"limit": batch_size})
            rows = [dict(r._mapping) for r in result]

        updated = 0
        for row in rows:
            try:
                name = row["name"]
                pubs = (row.get("publications") or [])
                pub_hint = pubs[0] if pubs else "art"
                query = f'"{name}" journalist email contact {pub_hint}'
                results_text = await self._search(query, max_results=5)

                prompt = f"""From these search results, extract contact information for the journalist "{name}".
Return a JSON object with these fields (null if not found):
- email (string, publicly listed email address — only if clearly public)
- social_links (object with any of: twitter, instagram, linkedin, website — full URLs)

Return only a single JSON object, not an array. Return {{}} if nothing found.

Search results:
{results_text}"""

                raw = await generate(prompt)
                start = raw.find("{")
                end = raw.rfind("}")
                if start == -1 or end == -1 or end <= start:
                    continue
                try:
                    contact = json.loads(raw[start:end + 1])
                except json.JSONDecodeError:
                    continue

                email = (contact.get("email") or "").strip() or None
                social = contact.get("social_links") or {}

                if not email and not social:
                    continue

                async with AsyncSessionLocal() as db:
                    await db.execute(text("""
                        UPDATE journalists
                        SET
                            email = COALESCE(email, :email),
                            social_links = CASE
                                WHEN social_links = '{}'::jsonb OR social_links IS NULL
                                THEN CAST(:social_links AS jsonb)
                                ELSE social_links
                            END
                        WHERE id = :id
                    """), {
                        "id": str(row["id"]),
                        "email": email,
                        "social_links": json.dumps(social),
                    })
                    await db.commit()

                updated += 1
                logger.info(f"[WebIngestor/Enrich] Updated contact info for {name}: email={email}")
            except Exception as e:
                logger.error(f"[WebIngestor/Enrich] Failed enriching {row.get('name')}: {e}")

        logger.info(f"[WebIngestor/Enrich] Enriched {updated}/{len(rows)} journalists")
        return updated

    # ─── Run all ─────────────────────────────────────────────────────────────

    async def run_all(self) -> dict:
        import asyncio
        results = await asyncio.gather(
            self.scan_architecture(),
            self.scan_collectors(),
            self.scan_curators(),
            self.scan_press(),
            self.scan_knowledge(),
            self.scan_journalists(),
            return_exceptions=True,
        )
        categories = ["architecture", "collectors", "curators", "press", "knowledge", "journalists"]
        summary = {}
        for cat, res in zip(categories, results):
            if isinstance(res, Exception):
                logger.error(f"[WebIngestor] {cat} failed: {res}")
                summary[cat] = 0
            else:
                summary[cat] = res
        logger.info(f"[WebIngestor] Scan complete: {summary}")
        return summary


_ingestor = WebIngestor()


async def run_all() -> dict:
    return await _ingestor.run_all()


async def scan_architecture() -> int:
    return await _ingestor.scan_architecture()


async def scan_collectors() -> int:
    return await _ingestor.scan_collectors()


async def scan_curators() -> int:
    return await _ingestor.scan_curators()


async def scan_press() -> int:
    return await _ingestor.scan_press()


async def scan_knowledge() -> int:
    return await _ingestor.scan_knowledge()


async def scan_journalists() -> int:
    return await _ingestor.scan_journalists()


async def enrich_journalists() -> int:
    return await _ingestor.enrich_journalists()
