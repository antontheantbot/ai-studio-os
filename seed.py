"""
Seed script — populates AI Studio OS with realistic test data.
Runs against the live API at http://localhost:8000
"""
import httpx
import json

BASE = "http://localhost:8000/api/v1"
client = httpx.Client(timeout=30)

def post(path, data):
    r = client.post(f"{BASE}{path}", json=data)
    if r.status_code not in (200, 201):
        print(f"  ERROR {r.status_code} {path}: {r.text[:200]}")
        return None
    return r.json()

def ok(label, result):
    if result:
        name = result.get("name") or result.get("title") or result.get("id", "")
        print(f"  ✓ {label}: {name}")

print("\n── Institutions ─────────────────────────────────────────────")
institutions = [
    {"name": "Ars Electronica", "city": "Linz", "country": "Austria", "type": "festival",
     "website": "https://ars.electronica.art", "focus_areas": ["digital art", "AI", "interactive", "sound"],
     "annual_budget": "€8M", "digital_art_program": True,
     "notes": "World's leading digital art festival. Key contact: festival director. Apply via open calls each spring."},
    {"name": "ZKM Center for Art and Media", "city": "Karlsruhe", "country": "Germany", "type": "museum",
     "website": "https://zkm.de", "focus_areas": ["media art", "digital", "immersive", "AI"],
     "annual_budget": "€12M", "digital_art_program": True,
     "notes": "Major museum for media art. Strong collection of video and interactive work."},
    {"name": "Rhizome", "city": "New York", "country": "USA", "type": "foundation",
     "website": "https://rhizome.org", "focus_areas": ["net art", "digital preservation", "new media"],
     "annual_budget": "€2M", "digital_art_program": True,
     "notes": "Affiliated with New Museum. Key platform for net art and digital culture."},
    {"name": "Serpentine Galleries", "city": "London", "country": "UK", "type": "gallery",
     "website": "https://serpentinegalleries.org", "focus_areas": ["contemporary", "digital", "architecture", "performance"],
     "annual_budget": "€15M", "digital_art_program": True,
     "notes": "Strong digital program. R&D platform commissions speculative projects."},
    {"name": "bitforms gallery", "city": "New York", "country": "USA", "type": "gallery",
     "website": "https://bitforms.art", "focus_areas": ["digital art", "software art", "generative", "video"],
     "annual_budget": "€1M", "digital_art_program": True,
     "notes": "Specialist gallery for digital and software-based art. Represents many key artists."},
    {"name": "Venice Biennale", "city": "Venice", "country": "Italy", "type": "biennial",
     "website": "https://labiennale.org", "focus_areas": ["contemporary art", "architecture", "international"],
     "annual_budget": "€30M", "digital_art_program": False,
     "notes": "Most prestigious international contemporary art exhibition. National pavilions + main show."},
]
inst_ids = {}
for inst in institutions:
    r = post("/institutions/", inst)
    ok("Institution", r)
    if r:
        inst_ids[inst["name"]] = r["id"]

print("\n── Artists ──────────────────────────────────────────────────")
artists = [
    {"name": "Refik Anadol", "country": "USA", "city": "Los Angeles",
     "bio": "Turkish-American media artist and director working at the intersection of AI, data, and architecture. Known for large-scale data sculptures and immersive installations.",
     "medium": ["AI", "data sculpture", "immersive installation", "generative video"],
     "website": "https://refikanadol.com", "instagram": "@refikanadol",
     "represented_by": ["Serpentine Galleries", "bitforms gallery"]},
    {"name": "teamLab", "country": "Japan", "city": "Tokyo",
     "bio": "Interdisciplinary art collective combining art, science, technology, and the natural world. Creates large-scale immersive digital installations.",
     "medium": ["immersive installation", "digital art", "interactive", "projection"],
     "website": "https://teamlab.art", "instagram": "@teamlab_news",
     "represented_by": ["Pace Gallery"]},
    {"name": "Hito Steyerl", "country": "Germany", "city": "Berlin",
     "bio": "German filmmaker, visual artist, and writer whose work explores media, technology, and global capitalism. Known for essayistic video works.",
     "medium": ["video", "installation", "essay film", "AI"],
     "website": "https://hitosteyerl.info", "instagram": "@hitosteyerl",
     "represented_by": ["Andrew Kreps Gallery", "espaivisor"]},
    {"name": "Ian Cheng", "country": "USA", "city": "New York",
     "bio": "American artist working with live simulations, video games, and AI to explore the nature of change and the conditions that allow it or prevent it.",
     "medium": ["simulation", "AI", "video", "live simulation"],
     "website": "https://iancheng.com", "instagram": "@ian_cheng",
     "represented_by": ["Gladstone Gallery", "Pilar Corrias"]},
    {"name": "Memo Akten", "country": "UK", "city": "London",
     "bio": "Turkish-British artist, researcher and musician exploring the nature of experience, perception, consciousness and our relationship with technology.",
     "medium": ["AI", "generative", "performance", "interactive installation"],
     "website": "https://memo.tv", "instagram": "@memotv",
     "represented_by": ["bitforms gallery"]},
]
artist_ids = {}
for artist in artists:
    r = post("/artists/", artist)
    ok("Artist", r)
    if r:
        artist_ids[artist["name"]] = r["id"]

print("\n── Artworks ─────────────────────────────────────────────────")
artworks = [
    {"title": "Machine Hallucinations — Nature Dreams", "artist_id": artist_ids.get("Refik Anadol"),
     "year": 2023, "medium": "AI data sculpture, custom software", "dimensions": "Variable",
     "description": "A large-scale AI data sculpture generated from 300 million images of nature. The work transforms collective machine memory into a living, breathing archive.",
     "collection": "Serpentine Galleries", "exhibition_history": ["Serpentine 2023", "Ars Electronica 2023"]},
    {"title": "Unsupervised", "artist_id": artist_ids.get("Refik Anadol"),
     "year": 2022, "medium": "Single-channel video, custom AI software", "dimensions": "Variable",
     "description": "Site-specific installation at MoMA that processes the museum's entire collection through an AI system to create a living, breathing interpretation.",
     "collection": "Museum of Modern Art, New York", "exhibition_history": ["MoMA 2022–2023"]},
    {"title": "How Do We Know What We Know?", "artist_id": artist_ids.get("teamLab"),
     "year": 2024, "medium": "Interactive digital installation", "dimensions": "Variable",
     "description": "An immersive environment where visitors' movements alter cascading waterfalls and blooming flowers in real-time.",
     "exhibition_history": ["teamLab Planets Tokyo 2024", "teamLab Borderless Shanghai 2024"]},
    {"title": "Factory of the Sun", "artist_id": artist_ids.get("Hito Steyerl"),
     "year": 2015, "medium": "HD video installation, custom environment", "dimensions": "Variable",
     "description": "A narrative about a dancer's motion-captured movements that are turned into energy in a data mine, exploring labor, technology and light.",
     "collection": "Various institutions", "exhibition_history": ["German Pavilion Venice Biennale 2015", "LACMA 2016", "Serpentine 2019"]},
    {"title": "BOB (Bag of Beliefs)", "artist_id": artist_ids.get("Ian Cheng"),
     "year": 2018, "medium": "Live simulation, custom software, app", "dimensions": "Infinite duration",
     "description": "An artificial life simulation of an entity with evolving emotional states, desires and beliefs — living indefinitely on a server.",
     "collection": "Various private collections", "exhibition_history": ["MoMA 2018", "Gladstone Gallery 2019"]},
    {"title": "Superradiance", "artist_id": artist_ids.get("Memo Akten"),
     "year": 2022, "medium": "AI, real-time generative video", "dimensions": "Variable",
     "description": "An exploration of collective consciousness through AI-generated imagery responding to the movements and breath of participants.",
     "exhibition_history": ["Ars Electronica 2022", "bitforms 2023"]},
]
for artwork in artworks:
    ok("Artwork", post("/artworks/", artwork))

print("\n── Exhibitions ──────────────────────────────────────────────")
exhibitions = [
    {"title": "AI: More than Human", "institution_id": inst_ids.get("Serpentine Galleries"),
     "type": "group", "start_date": "2023-06-01", "end_date": "2023-09-03",
     "artists": ["Refik Anadol", "teamLab", "Ian Cheng", "Holly Herndon"],
     "description": "A major survey of art and technology exploring artificial intelligence through the lens of creativity, philosophy, and human experience.",
     "url": "https://serpentinegalleries.org"},
    {"title": "Ars Electronica Festival 2024 — Hope", "institution_id": inst_ids.get("Ars Electronica"),
     "type": "festival", "start_date": "2024-09-04", "end_date": "2024-09-08",
     "artists": ["Memo Akten", "Refik Anadol", "teamLab", "Various"],
     "description": "Annual festival exploring the intersections of art, technology, and society with the theme 'Hope — Who Will Turn the Tide?'",
     "url": "https://ars.electronica.art/hope"},
    {"title": "Digital Condition", "institution_id": inst_ids.get("ZKM Center for Art and Media"),
     "type": "survey", "start_date": "2023-03-11", "end_date": "2023-07-30",
     "artists": ["Hito Steyerl", "Ian Cheng", "Hasan Elahi", "Zach Lieberman"],
     "description": "A comprehensive survey of digital art practices examining the conditions of contemporary digital existence.",
     "url": "https://zkm.de"},
    {"title": "Unfinished Machines", "institution_id": inst_ids.get("bitforms gallery"),
     "type": "group", "start_date": "2024-02-10", "end_date": "2024-03-30",
     "artists": ["Memo Akten", "Sofia Crespo", "Gene Kogan"],
     "description": "An exhibition of AI-driven works exploring the unfinished, generative, and emergent qualities of machine learning systems.",
     "url": "https://bitforms.art"},
]
for ex in exhibitions:
    ok("Exhibition", post("/exhibitions/", ex))

print("\n── Collectors ───────────────────────────────────────────────")
collectors = [
    {"name": "Julia Stoschek", "bio": "German collector and founder of the Julia Stoschek Collection in Düsseldorf and Berlin, one of the world's foremost collections of time-based media art.",
     "location": "Düsseldorf", "country": "Germany",
     "interests": ["video art", "time-based media", "performance", "digital"],
     "known_works": ["Factory of the Sun — Hito Steyerl", "The Clock — Christian Marclay"],
     "institutions": ["Julia Stoschek Collection", "Schirn Kunsthalle"],
     "contact_url": "https://jsc.art", "social_links": {"instagram": "juliastoschek"},
     "notes": "Extremely active collector. Focuses on video and time-based media. Runs own kunsthalle."},
    {"name": "Pamela and Richard Kramlich", "bio": "San Francisco-based collectors who pioneered collecting new media art, co-founding the New Art Trust and supporting institutions internationally.",
     "location": "San Francisco", "country": "USA",
     "interests": ["new media", "video", "interactive", "digital"],
     "institutions": ["New Art Trust", "SFMOMA", "Tate"],
     "notes": "Foundational collectors of new media. Close relationship with ZKM and Ars Electronica."},
    {"name": "Helyn Goldenberg", "bio": "Chicago-based collector with significant holdings in digital and generative art, known for supporting emerging artists working with technology.",
     "location": "Chicago", "country": "USA",
     "interests": ["generative art", "AI art", "software art", "digital"],
     "institutions": ["Art Institute of Chicago", "MCA Chicago"],
     "notes": "Strong interest in generative and algorithmic work. Open to studio visits."},
]
for c in collectors:
    ok("Collector", post("/collectors/", c))

print("\n── Curators ─────────────────────────────────────────────────")
curators = [
    {"name": "Hans Ulrich Obrist", "bio": "Swiss curator and artistic director of the Serpentine Galleries. One of the most influential figures in contemporary art.",
     "institution": "Serpentine Galleries", "role": "Artistic Director",
     "location": "London", "country": "UK",
     "focus_areas": ["contemporary art", "digital", "architecture", "interdisciplinary"],
     "notable_shows": ["AI: More than Human", "Do It", "Marathon series"],
     "contact_url": "https://serpentinegalleries.org",
     "social_links": {"instagram": "hansulrichobrist"},
     "notes": "Very active on Instagram. Prefers email introductions via gallery. Interested in AI and speculative work."},
    {"name": "Christiane Paul", "bio": "Curator of digital art at the Whitney Museum and adjunct professor at the School of Visual Arts, New York.",
     "institution": "Whitney Museum of American Art", "role": "Adjunct Curator of Digital Art",
     "location": "New York", "country": "USA",
     "focus_areas": ["digital art", "net art", "interactive", "new media"],
     "notable_shows": ["Profiling", "Data Dynamics", "CodeDoc"],
     "notes": "Key figure in institutional digital art collecting. Author of 'Digital Art' (Thames & Hudson)."},
    {"name": "Gerfried Stocker", "bio": "Artistic director of Ars Electronica since 1995, overseeing the festival, museum, and R&D lab.",
     "institution": "Ars Electronica", "role": "Artistic Director",
     "location": "Linz", "country": "Austria",
     "focus_areas": ["AI", "digital art", "society", "science"],
     "notable_shows": ["Ars Electronica Festival (annual)", "Prix Ars Electronica"],
     "notes": "Approachable at the festival. Best to submit through official Prix and open call channels."},
]
for c in curators:
    ok("Curator", post("/curators/", c))

print("\n── Opportunities ────────────────────────────────────────────")
opportunities = [
    {"title": "Prix Ars Electronica 2026 — AI & Life Art", "category": "open_call",
     "organizer": "Ars Electronica", "location": "Linz", "country": "Austria",
     "description": "International competition for cyberarts. Category AI & Life Art invites works exploring artificial intelligence, machine learning, and synthetic biology.",
     "deadline": "2026-05-01", "fee": "Free", "award": "Golden Nica + €10,000",
     "url": "https://ars.electronica.art/prix", "tags": ["AI", "competition", "digital", "prize"]},
    {"title": "Sundance New Frontier Fellowship 2026", "category": "residency",
     "organizer": "Sundance Institute", "location": "Park City", "country": "USA",
     "description": "Residency for artists working at the intersection of film, storytelling, and emerging technology including VR, AR, AI, and interactive media.",
     "deadline": "2026-06-15", "fee": "Free", "award": "Residency + $10,000 stipend",
     "url": "https://sundance.org/programs/new-frontier", "tags": ["residency", "VR", "interactive", "AI"]},
    {"title": "ZKM Open Call — Becoming Digital", "category": "open_call",
     "organizer": "ZKM Center for Art and Media", "location": "Karlsruhe", "country": "Germany",
     "description": "Open call for works exploring digital transformation and its impact on identity, society, and culture. Works may be shown in ZKM's collection galleries.",
     "deadline": "2026-07-30", "fee": "Free", "award": "Exhibition + production support",
     "url": "https://zkm.de/open-call", "tags": ["digital art", "exhibition", "media art"]},
    {"title": "Rhizome Commissions 2026", "category": "commission",
     "organizer": "Rhizome", "location": "New York", "country": "USA",
     "description": "Annual commissions supporting the creation of new net-based artworks, software art, and digital projects that push boundaries of online creative practice.",
     "deadline": "2026-08-01", "fee": "Free", "award": "$5,000–$15,000",
     "url": "https://rhizome.org/commissions", "tags": ["net art", "software", "commission", "online"]},
    {"title": "Onassis AiR Digital Residency", "category": "residency",
     "organizer": "Onassis Foundation", "location": "Athens", "country": "Greece",
     "description": "Residency for artists working with digital tools, AI, and technology. Includes studio space, production budget, and mentorship from leading practitioners.",
     "deadline": "2026-09-15", "fee": "Free", "award": "€8,000 + accommodation",
     "url": "https://onassis.org/air", "tags": ["residency", "AI", "digital", "Greece"]},
]
for opp in opportunities:
    ok("Opportunity", post("/opportunities/", opp))

print("\n── Press Items ──────────────────────────────────────────────")
press = [
    {"title": "Refik Anadol's AI Art Is Taking Over the World's Museums", "source": "Wired",
     "author": "Emily Dreyfuss", "category": "review",
     "published_at": "2024-01-15T10:00:00Z",
     "summary": "How the Turkish-American artist became the face of machine learning aesthetics, transforming institutions from MoMA to the Serpentine with his data sculptures.",
     "url": "https://wired.com/story/refik-anadol", "tags": ["AI art", "data sculpture", "MoMA"],
     "mentioned_artists": ["Refik Anadol"]},
    {"title": "Is AI Art Really Art? Critics and Curators Weigh In", "source": "Artforum",
     "author": "Lane Relyea", "category": "review",
     "published_at": "2024-02-01T09:00:00Z",
     "summary": "A critical survey of AI-generated work shown in major institutions, asking whether the field represents a genuine artistic movement or a technological novelty.",
     "url": "https://artforum.com/ai-art-debate", "tags": ["AI art", "criticism", "institutions"],
     "mentioned_artists": ["Hito Steyerl", "Ian Cheng", "Memo Akten"]},
    {"title": "Ars Electronica 2024 Review: Hope in the Age of Algorithms", "source": "Frieze",
     "author": "Jörg Heiser", "category": "exhibition",
     "published_at": "2024-09-10T12:00:00Z",
     "summary": "The annual festival grapples with optimism and anxiety around AI, with standout works by Memo Akten, Holly Herndon, and dozens of international artists.",
     "url": "https://frieze.com/ars-electronica-2024", "tags": ["Ars Electronica", "AI", "festival"],
     "mentioned_artists": ["Memo Akten", "Holly Herndon", "Refik Anadol"]},
    {"title": "Hito Steyerl: The Wretched of the Screen — ZKM Survey", "source": "ARTnews",
     "author": "Sarah Cascone", "category": "exhibition",
     "published_at": "2023-11-20T14:00:00Z",
     "summary": "A major retrospective of Steyerl's video and installation practice at ZKM surveys thirty years of work engaging with media, technology, and political economy.",
     "url": "https://artnews.com/hito-steyerl-zkm", "tags": ["retrospective", "video art", "ZKM"],
     "mentioned_artists": ["Hito Steyerl"]},
    {"title": "The Generative Turn: Software Art Enters the Museum", "source": "Rhizome",
     "author": "Michael Connor", "category": "news",
     "published_at": "2024-03-05T11:00:00Z",
     "summary": "As generative AI reshapes art markets and institutions, Rhizome traces the longer history of software-based practice that laid the groundwork for today's moment.",
     "url": "https://rhizome.org/generative-turn", "tags": ["generative art", "software art", "history"],
     "mentioned_artists": ["Casey Reas", "Vera Molnár", "Memo Akten"]},
]
for p in press:
    ok("Press", post("/press/", p))

print("\n── Knowledge Items ──────────────────────────────────────────")
knowledge = [
    {"title": "Artist Statement Template — Digital Installation",
     "content": """My practice investigates the relationship between computational systems and natural phenomena, exploring how machine learning can reveal hidden patterns within vast datasets.

Working at the intersection of AI, data visualization, and immersive installation, I create environments that transform invisible information flows into sensory experiences. Each work begins with a specific dataset — whether ecological measurements, architectural archives, or collective human behavior — and develops an AI system trained to find meaning within that data.

The resulting installations occupy physical space while existing simultaneously in computational space, creating a dialogue between the digital and material world. Viewers become participants in a living system, their presence altering the generated imagery in real time.

My work has been exhibited internationally, from Ars Electronica to the Serpentine, and is held in both public and private collections.""",
     "source_type": "note", "tags": ["artist statement", "template", "AI", "installation"],
     "summary": "Template artist statement for digital installation and AI-based practices."},
    {"title": "Proposal Writing Guide — Residency Applications",
     "content": """Key elements for a successful residency proposal:

1. PROJECT DESCRIPTION (300–500 words)
Be specific about what you will make. Avoid vague language like 'explore' or 'investigate' — say exactly what the work will look like, sound like, and do.

2. RESEARCH CONTEXT
Position your work within art history AND technology. Name the specific artists, theorists, and technical developments your work responds to.

3. PRODUCTION PLAN
Include realistic timeline, equipment needs, collaborators, and post-residency plans for the work.

4. RELEVANCE TO PROGRAM
Show you've researched the residency. Reference their past artists, facilities, and stated mission. Explain why this specific residency at this specific time is necessary for your practice.

5. BUDGET
Break down costs clearly. Underpromise and overdeliver — request what you genuinely need.

COMMON MISTAKES:
- Too much biography, not enough project
- Generic language that could apply to any artist
- Forgetting to address the specific brief or theme
- Poor quality documentation images""",
     "source_type": "note", "tags": ["proposals", "residency", "writing guide", "tips"],
     "summary": "Practical guide for writing successful residency and open call proposals."},
    {"title": "Key Art Fairs for Digital and New Media",
     "content": """TIER 1 (Essential):
- Art Basel (Basel, Miami Beach, Hong Kong) — digital work increasingly represented
- Frieze London / New York — strong gallery presence for media art
- The Armory Show, New York

SPECIALIST FAIRS:
- UNTITLED Art Fair — strongest showing of digital/video work
- Nada Art Fair — emerging and experimental practices
- Moving Image (NY, London) — dedicated to video and moving image
- FILE Electronic Language International Festival, São Paulo

DIGITAL-NATIVE:
- NFT.NYC — for blockchain-based work
- Bright Moments — crypto art focused

NOTES:
Art Basel has been increasing digital work representation. The main hall remains dominated by painting but galleries like bitforms and Pace regularly show digital work.
Moving Image is the most relevant fair for video and installation — strong collector attendance from film and media backgrounds.""",
     "source_type": "reference", "tags": ["art fairs", "market", "strategy", "sales"],
     "summary": "Overview of major and specialist art fairs relevant to digital and new media practices."},
    {"title": "Understanding pgvector for Semantic Search",
     "content": """pgvector is a PostgreSQL extension for vector similarity search. It enables storing and querying high-dimensional vectors (embeddings) directly in PostgreSQL.

KEY CONCEPTS:
- Embeddings: numerical representations of text/images as vectors
- Cosine similarity: measures angle between vectors (1 = identical, 0 = unrelated)
- IVFFlat index: approximate nearest neighbor for large datasets

USAGE IN AI STUDIO OS:
Every record is embedded using OpenAI text-embedding-3-small (1536 dimensions).
Search uses cosine distance operator <=> to find most similar records.

EXAMPLE QUERY:
SELECT title, 1 - (embedding <=> '[0.1, 0.2, ...]'::vector) AS similarity
FROM knowledge_items
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;

TUNING:
- lists = 100 works well up to ~1M rows
- Rebuild index when data grows significantly
- Use HNSW index for better recall at the cost of build time""",
     "source_type": "reference", "tags": ["pgvector", "embeddings", "technical", "search"],
     "summary": "Technical reference for pgvector usage in AI Studio OS, including indexing and search patterns."},
]
for k in knowledge:
    ok("Knowledge", post("/knowledge/notes", k))

print("\n── Done ─────────────────────────────────────────────────────")
print("Database seeded. Refresh http://localhost to see the data.\n")
client.close()
