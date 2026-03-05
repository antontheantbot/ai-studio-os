"""
Seed the top 100 digital artists actively working today.
Run inside the api container: docker compose exec api python seed_artists.py
"""
import asyncio
import sys

ARTISTS = [
    # ── Established digital/new media pioneers ────────────────────────────────
    {"name": "Refik Anadol", "country": "USA", "city": "Los Angeles",
     "bio": "Turkish-American media artist and director known for data-driven machine intelligence artworks and immersive architectural installations.",
     "medium": ["AI art", "data sculpture", "immersive installation"], "website": "https://refikanadol.com", "instagram": "@refikanadol"},
    {"name": "teamLab", "country": "Japan", "city": "Tokyo",
     "bio": "Ultra-technologists art collective creating immersive digital art environments blending nature, technology, and human experience.",
     "medium": ["immersive installation", "digital art", "interactive art"], "website": "https://www.teamlab.art", "instagram": "@teamlab_art"},
    {"name": "Hito Steyerl", "country": "Germany", "city": "Berlin",
     "bio": "German filmmaker and media artist known for essay films and installations exploring digital images, the internet, and global capitalism.",
     "medium": ["video art", "installation", "essay film"], "website": "https://hito-steyerl.com"},
    {"name": "Ian Cheng", "country": "USA", "city": "New York",
     "bio": "American artist working with simulations, live process, and AI to explore consciousness, mutation, and worldbuilding.",
     "medium": ["simulation art", "AI art", "video"], "website": "https://iancheng.com"},
    {"name": "Memo Akten", "country": "UK", "city": "Los Angeles",
     "bio": "Turkish-British computational artist and researcher exploring the intersection of science, technology, nature, and spirituality.",
     "medium": ["generative art", "AI art", "interactive installation"], "website": "https://memo.tv", "instagram": "@memotv"},
    {"name": "Casey Reas", "country": "USA", "city": "Los Angeles",
     "bio": "American artist and educator, co-creator of Processing, known for software art exploring the boundary between digital process and visual form.",
     "medium": ["software art", "generative art", "print"], "website": "https://reas.com"},
    {"name": "Ryoji Ikeda", "country": "Japan", "city": "Paris",
     "bio": "Japanese artist working with sound and visuals to create austere, mathematical installations based on data and pure signal.",
     "medium": ["data art", "sound installation", "video installation"], "website": "https://www.ryojiikeda.com"},
    {"name": "Olafur Eliasson", "country": "Denmark", "city": "Berlin",
     "bio": "Icelandic-Danish artist whose large-scale installations engage viewers with light, water, temperature, and natural phenomena.",
     "medium": ["installation", "sculpture", "light art"], "website": "https://olafureliasson.net", "instagram": "@studioolafureliasson"},
    {"name": "Marshmallow Laser Feast", "country": "UK", "city": "London",
     "bio": "London-based art collective creating immersive experiences that reveal hidden worlds through technology, science, and art.",
     "medium": ["immersive installation", "VR", "digital art"], "website": "https://www.marshmallowlaserfeast.com", "instagram": "@marshmallowlaserfeast"},
    {"name": "Universal Everything", "country": "UK", "city": "Sheffield",
     "bio": "Future-facing art studio by Matt Pyke, creating living artworks and digital experiences across screens, spaces, and systems.",
     "medium": ["motion art", "generative art", "digital installation"], "website": "https://universaleverything.com"},

    # ── AI & machine learning artists ─────────────────────────────────────────
    {"name": "Holly Herndon", "country": "USA", "city": "San Francisco",
     "bio": "American musician and artist using AI, machine learning, and voice synthesis to explore the politics of technology and human identity.",
     "medium": ["AI music", "sound art", "performance"], "website": "https://herndondryhurst.net", "instagram": "@hollyherndon"},
    {"name": "Sofia Crespo", "country": "Argentina", "city": "Berlin",
     "bio": "Argentinian artist working with neural networks to explore biologically inspired entities and artificial life forms.",
     "medium": ["AI art", "generative art", "digital sculpture"], "website": "https://sofiacrespo.com", "instagram": "@sofia.crespo"},
    {"name": "Sougwen Chung", "country": "Canada", "city": "London",
     "bio": "Sino-Canadian artist and researcher exploring the collaboration between human mark-making and robotic drawing systems.",
     "medium": ["robotic art", "drawing", "performance"], "website": "https://sougwen.com", "instagram": "@sougwenchung"},
    {"name": "Stephanie Dinkins", "country": "USA", "city": "New York",
     "bio": "Transmedia artist creating platforms for dialogue about AI, race, and the future of inclusive machine intelligence.",
     "medium": ["AI art", "video installation", "social practice"], "website": "https://stephaniedinkins.com"},
    {"name": "Jake Elwes", "country": "UK", "city": "London",
     "bio": "British artist using machine learning to examine bias, identity, and the aesthetics of AI-generated imagery.",
     "medium": ["AI art", "video installation", "machine learning"], "website": "https://www.jakeelwes.com"},
    {"name": "Mario Klingemann", "country": "Germany", "city": "Munich",
     "bio": "German artist and neural network pioneer known for exploring creativity, culture, and perception with machine intelligence.",
     "medium": ["AI art", "generative art", "neural networks"], "website": "https://quasimondo.com", "instagram": "@quasimondo"},
    {"name": "Helena Sarin", "country": "USA", "city": "New York",
     "bio": "Visual artist and software engineer working with GANs and neural networks to create intimate, handcrafted digital art.",
     "medium": ["AI art", "GAN art", "digital collage"], "instagram": "@helena.sarin"},
    {"name": "Botto", "country": "International", "city": "Decentralized",
     "bio": "Autonomous AI artist governed by a decentralized community, generating and selling unique artworks using machine learning.",
     "medium": ["AI art", "generative art", "NFT"], "website": "https://botto.com"},
    {"name": "Obvious Art", "country": "France", "city": "Paris",
     "bio": "French art collective using GANs to create AI-generated portraits and paintings, known for the Belamy series sold at Christie's.",
     "medium": ["AI art", "GAN art", "painting"], "website": "https://obvious-art.com"},

    # ── Generative & code artists ─────────────────────────────────────────────
    {"name": "Ben Fry", "country": "USA", "city": "Boston",
     "bio": "American designer and artist, co-creator of Processing, known for visualizing complex data and computational systems.",
     "medium": ["data visualization", "software art", "generative art"], "website": "https://benfry.com"},
    {"name": "Joshua Davis", "country": "USA", "city": "New York",
     "bio": "American digital artist and designer known for generative, algorithm-driven visual systems and large-scale installations.",
     "medium": ["generative art", "digital design", "installation"], "website": "https://joshuadavis.com"},
    {"name": "Vera Molnár", "country": "France", "city": "Paris",
     "bio": "Hungarian-French pioneer of computer and algorithmic art, using mathematical structures to create abstract visual works since the 1960s.",
     "medium": ["computer art", "algorithmic art", "drawing"], "website": "https://www.veramolnar.com"},
    {"name": "Tyler Hobbs", "country": "USA", "city": "Austin",
     "bio": "American generative artist known for Fidenza and works exploring order vs chaos through algorithmic flow field compositions.",
     "medium": ["generative art", "plotter art", "NFT"], "website": "https://tylerxhobbs.com", "instagram": "@tylerxhobbs"},
    {"name": "Dmitri Cherniak", "country": "Canada", "city": "Toronto",
     "bio": "Canadian generative artist known for Ringers, exploring mathematical elegance and visual complexity through code.",
     "medium": ["generative art", "NFT", "code art"], "website": "https://www.dmitricherniak.com"},
    {"name": "Matt DesLauriers", "country": "Canada", "city": "Toronto",
     "bio": "Creative coder and generative artist working with JavaScript and WebGL to create intricate, layered digital artworks.",
     "medium": ["generative art", "creative coding", "NFT"], "website": "https://mattdesl.com", "instagram": "@mattdesl"},
    {"name": "Zach Lieberman", "country": "USA", "city": "New York",
     "bio": "American artist and coder whose daily art practice explores gesture, motion, and the poetics of computation.",
     "medium": ["creative coding", "interactive art", "generative art"], "website": "https://zachlieberman.me", "instagram": "@zach.lieberman"},
    {"name": "Lauren McCarthy", "country": "USA", "city": "Los Angeles",
     "bio": "American artist examining social relationships in the context of surveillance, automation, and networked technology.",
     "medium": ["performance", "software art", "interactive art"], "website": "https://lauren-mccarthy.com"},
    {"name": "Nervous System", "country": "USA", "city": "Somerville",
     "bio": "Design studio run by Jessica Rosenkrantz and Jesse Louis-Rosenberg, creating art and objects inspired by natural systems using simulation.",
     "medium": ["generative design", "3D printing", "jewelry"], "website": "https://n-e-r-v-o-u-s.com"},
    {"name": "Joanie Lemercier", "country": "France", "city": "Brussels",
     "bio": "French artist exploring light, projection mapping, and immersive environments, combining environmental concerns with digital practice.",
     "medium": ["projection mapping", "light art", "installation"], "website": "https://joanielemercier.com", "instagram": "@joanielemercier"},

    # ── VR / XR / immersive artists ───────────────────────────────────────────
    {"name": "Nonny de la Peña", "country": "USA", "city": "Los Angeles",
     "bio": "'Godmother of VR Journalism' creating immersive virtual reality news experiences and empathy-driven documentary works.",
     "medium": ["VR", "immersive journalism", "installation"], "website": "https://nonnydelapena.com"},
    {"name": "Chris Milk", "country": "USA", "city": "Los Angeles",
     "bio": "American filmmaker and VR pioneer, co-founder of Within, known for empathy-focused immersive virtual reality experiences.",
     "medium": ["VR", "film", "installation"], "website": "https://www.chrismilk.com"},
    {"name": "Björk", "country": "Iceland", "city": "Reykjavik",
     "bio": "Icelandic musician and artist whose Biophilia and Vulnicura albums pioneered immersive VR music experiences and app-based interactive art.",
     "medium": ["VR", "music", "interactive art"], "website": "https://bjork.com"},
    {"name": "Rachel Rossin", "country": "USA", "city": "New York",
     "bio": "American painter and VR artist whose work collages digital and physical fragments into dreamlike immersive environments.",
     "medium": ["VR", "painting", "installation"], "website": "https://www.rachelrossin.com"},

    # ── Projection mapping & light art ────────────────────────────────────────
    {"name": "AntiVJ", "country": "France", "city": "Paris",
     "bio": "Visual label and collective exploring projection, light, and spatial sound to redefine environments and perceptions of space.",
     "medium": ["projection mapping", "light art", "performance"], "website": "https://antivj.com"},
    {"name": "Studio Drift", "country": "Netherlands", "city": "Amsterdam",
     "bio": "Dutch artistic duo Lonneke Gordijn and Ralph Nauta creating kinetic sculptures and light installations responding to natural forces.",
     "medium": ["kinetic sculpture", "light installation", "drone art"], "website": "https://studiodrift.com", "instagram": "@studiodrift"},
    {"name": "James Turrell", "country": "USA", "city": "Flagstaff",
     "bio": "American light and space artist known for using light as primary medium, creating perceptual environments and the Roden Crater project.",
     "medium": ["light art", "installation", "earthworks"], "website": "https://jamesturrell.com"},
    {"name": "Limelight", "country": "Australia", "city": "Sydney",
     "bio": "Australian projection mapping collective creating large-scale architectural projections and immersive light experiences.",
     "medium": ["projection mapping", "light art", "installation"]},
    {"name": "Maxin10sity", "country": "Hungary", "city": "Budapest",
     "bio": "Hungarian visual art company creating stunning projection mapping and video mapping shows on iconic buildings worldwide.",
     "medium": ["projection mapping", "video mapping", "installation"], "website": "https://maxin10sity.com"},

    # ── Net art & digital conceptual ──────────────────────────────────────────
    {"name": "Cory Arcangel", "country": "USA", "city": "New York",
     "bio": "American artist working with appropriated pop culture, video games, and the internet to examine digital vernacular aesthetics.",
     "medium": ["net art", "video", "installation"], "website": "https://coryarcangel.com"},
    {"name": "Artie Vierkant", "country": "USA", "city": "New York",
     "bio": "American artist using digital fabrication, image files, and institutional systems to examine post-internet aesthetics.",
     "medium": ["post-internet art", "digital fabrication", "installation"], "website": "https://artievierkant.com"},
    {"name": "Jon Rafman", "country": "Canada", "city": "Montreal",
     "bio": "Canadian artist whose video, sculpture, and digital works explore internet subcultures, gaming, and post-human consciousness.",
     "medium": ["video art", "3D rendering", "net art"], "website": "https://jonrafman.com"},
    {"name": "Tabor Robak", "country": "USA", "city": "New York",
     "bio": "American artist creating lush, screen-based digital environments that blur the line between art, advertising, and spectacle.",
     "medium": ["digital video", "software art", "installation"], "website": "https://taborrobak.com"},
    {"name": "DIS Magazine", "country": "USA", "city": "New York",
     "bio": "Online magazine and art collective that defined post-internet aesthetics through digital publishing and curatorial projects.",
     "medium": ["net art", "digital publishing", "performance"]},

    # ── Video & moving image artists ──────────────────────────────────────────
    {"name": "Pipilotti Rist", "country": "Switzerland", "city": "Zurich",
     "bio": "Swiss video and installation artist known for lush, psychedelic video environments exploring feminism, the body, and desire.",
     "medium": ["video installation", "immersive installation"], "website": "https://pipilottirist.net"},
    {"name": "Nam June Paik Foundation", "country": "USA", "city": "New York",
     "bio": "Legacy foundation for the Korean-American pioneer of video art whose work with television and technology remains foundational.",
     "medium": ["video art", "installation", "performance"]},
    {"name": "Bill Viola", "country": "USA", "city": "Long Beach",
     "bio": "American video artist whose monumental video installations draw on spiritual traditions and the elemental forces of fire and water.",
     "medium": ["video installation", "video art"], "website": "https://billviola.com"},
    {"name": "Ed Atkins", "country": "UK", "city": "Berlin",
     "bio": "British artist working with HD video and CGI to create disturbing, intimate, and literary works about embodiment and digital being.",
     "medium": ["video art", "CGI", "digital video"], "website": "https://edatkins.co.uk"},

    # ── Blockchain & NFT artists ──────────────────────────────────────────────
    {"name": "Beeple", "country": "USA", "city": "Charleston",
     "bio": "Mike Winkelmann, American digital artist known for the 'Everydays' series and the $69M NFT sale that defined the crypto art market.",
     "medium": ["digital illustration", "NFT", "animation"], "website": "https://beeple-crap.com", "instagram": "@beeple"},
    {"name": "Pak", "country": "International", "city": "Unknown",
     "bio": "Anonymous digital artist and developer known for conceptual NFT works exploring value, ownership, and digital scarcity.",
     "medium": ["NFT", "generative art", "conceptual art"], "website": "https://linktr.ee/muratpak"},
    {"name": "XCOPY", "country": "UK", "city": "London",
     "bio": "British anonymous crypto artist whose glitchy, dystopian GIFs and animations capture digital anxiety and mortality.",
     "medium": ["GIF art", "digital art", "NFT"], "instagram": "@xcopyart"},
    {"name": "Hackatao", "country": "Italy", "city": "Milan",
     "bio": "Italian artistic duo Nadia Squarci and Sergio Scalet creating symbolic, layered digital works exploring identity and the unconscious.",
     "medium": ["digital drawing", "NFT", "animation"], "website": "https://hackatao.com", "instagram": "@hackatao"},
    {"name": "Fewocious", "country": "USA", "city": "Las Vegas",
     "bio": "Young American artist Victor Langlois whose autobiographical, emotionally raw digital paintings document growing up non-binary.",
     "medium": ["digital painting", "NFT"], "website": "https://fewocious.com", "instagram": "@fewocious"},
    {"name": "Larva Labs", "country": "USA", "city": "New York",
     "bio": "Canadian-American developer duo Matt Hall and John Watkinson, creators of CryptoPunks, pioneers of generative NFT collectibles.",
     "medium": ["generative art", "NFT", "software art"]},
    {"name": "Art Blocks", "country": "USA", "city": "Denver",
     "bio": "Platform and curatorial entity by Erick Caldwell for on-chain generative art, launching careers of numerous generative artists.",
     "medium": ["generative art", "NFT", "platform"]},

    # ── Sound & audiovisual artists ───────────────────────────────────────────
    {"name": "Arca", "country": "Venezuela", "city": "London",
     "bio": "Venezuelan-born experimental musician and artist Alejandra Ghersi whose sprawling, mutant music merges body horror and digital ecstasy.",
     "medium": ["sound art", "music", "visual art"], "instagram": "@arca1000000"},
    {"name": "Emptyset", "country": "UK", "city": "Bristol",
     "bio": "UK electronic duo James Ginzburg and Paul Purgas creating audiovisual installations and performances at the edge of machine sound.",
     "medium": ["sound installation", "audiovisual", "performance"], "website": "https://emptyset.info"},
    {"name": "Actual Objects", "country": "USA", "city": "Los Angeles",
     "bio": "Creative studio working at the intersection of music, moving image, and spatial experience for artists and cultural institutions.",
     "medium": ["audiovisual", "installation", "digital video"]},

    # ── Physical / computational sculpture ────────────────────────────────────
    {"name": "Random International", "country": "UK", "city": "London",
     "bio": "London-based practice creating behavioural objects and immersive environments that explore humanity's relationship with technology.",
     "medium": ["kinetic sculpture", "interactive installation", "digital art"], "website": "https://www.random-international.com", "instagram": "@random_international"},
    {"name": "Neri Oxman", "country": "USA", "city": "Boston",
     "bio": "Israeli-American designer and scientist pioneering material ecology, 3D printing biological structures at MIT Media Lab.",
     "medium": ["biodigital design", "3D printing", "architecture"], "website": "https://oxman.com"},
    {"name": "Théo Jansen", "country": "Netherlands", "city": "Delft",
     "bio": "Dutch artist creating large kinetic sculptures 'Strandbeests' that walk on wind power, blurring the boundary between life and machine.",
     "medium": ["kinetic sculpture", "robotic art"], "website": "https://www.strandbeest.com"},
    {"name": "Studio DRIFT", "country": "Netherlands", "city": "Amsterdam",
     "bio": "Dutch art studio creating drone performances and kinetic light sculptures mimicking the movements of nature.",
     "medium": ["drone art", "kinetic sculpture", "light installation"]},

    # ── Augmented reality & mixed media ───────────────────────────────────────
    {"name": "Keiichi Matsuda", "country": "UK", "city": "London",
     "bio": "British-Japanese designer and filmmaker whose HYPER-REALITY film envisions a dystopian AR-saturated future.",
     "medium": ["AR", "film", "design"], "website": "https://km.cx", "instagram": "@keiichimatsuda"},
    {"name": "Nancy Baker Cahill", "country": "USA", "city": "Los Angeles",
     "bio": "American artist creating site-specific AR public artworks that layer digital drawings over the physical environment.",
     "medium": ["AR", "drawing", "public art"], "website": "https://nancybakercahill.com", "instagram": "@nancybakercahill"},
    {"name": "Cao Fei", "country": "China", "city": "Beijing",
     "bio": "Chinese multimedia artist whose works incorporate video, installation, and virtual worlds to explore China's rapid social transformation.",
     "medium": ["video art", "VR", "installation"], "website": "https://caofei.com"},

    # ── Data & information visualization ──────────────────────────────────────
    {"name": "Fernanda Viégas", "country": "USA", "city": "Cambridge",
     "bio": "Brazilian computational designer and researcher at Google Brain creating expressive, public-facing data visualization artworks.",
     "medium": ["data visualization", "generative art", "software art"], "website": "https://fernandaviegas.com"},
    {"name": "Martin Wattenberg", "country": "USA", "city": "Cambridge",
     "bio": "American artist and researcher at Google Brain known for collaborative data visualization works and the Wind Map.",
     "medium": ["data visualization", "net art", "software art"], "website": "https://wattenberg.com"},
    {"name": "Aaron Koblin", "country": "USA", "city": "San Francisco",
     "bio": "American digital media artist and entrepreneur known for crowd-sourced and data-driven interactive art at Google Creative Lab.",
     "medium": ["data art", "interactive art", "crowd-sourcing"], "website": "https://www.aaronkoblin.com"},
    {"name": "Jer Thorp", "country": "Canada", "city": "New York",
     "bio": "Canadian data artist and New York Times R&D alum creating poetic data visualizations that foreground human stories in datasets.",
     "medium": ["data visualization", "generative art", "installation"], "website": "https://jerthorp.com"},

    # ── Post-internet & contemporary digital ──────────────────────────────────
    {"name": "Ryan Trecartin", "country": "USA", "city": "Los Angeles",
     "bio": "American artist and filmmaker creating hyperkinetic, internet-inflected video works exploring identity, language, and digital culture.",
     "medium": ["video art", "film", "installation"]},
    {"name": "K-HOLE", "country": "USA", "city": "New York",
     "bio": "New York art group and trend forecasting collective, known for coining 'normcore' and exploring consumer culture as artistic practice.",
     "medium": ["conceptual art", "publishing", "trend forecasting"]},
    {"name": "Kate Crawford", "country": "Australia", "city": "New York",
     "bio": "Australian researcher and artist examining the social and political implications of artificial intelligence through Atlas of AI and other works.",
     "medium": ["data art", "research", "installation"]},
    {"name": "Trevor Paglen", "country": "USA", "city": "New York",
     "bio": "American artist and geographer documenting surveillance infrastructure and training AI datasets to expose hidden systems of power.",
     "medium": ["photography", "installation", "data art"], "website": "https://paglen.com"},

    # ── Interactive & web-based artists ───────────────────────────────────────
    {"name": "Vera van de Seyp", "country": "Netherlands", "city": "Amsterdam",
     "bio": "Dutch digital artist creating browser-based, interactive artworks that explore digital materiality and online identity.",
     "medium": ["web art", "interactive art", "generative art"]},
    {"name": "Everest Pipkin", "country": "USA", "city": "Pittsburgh",
     "bio": "American artist and writer creating tools and poetic software exploring natural systems, labor, and the ecology of digital space.",
     "medium": ["software art", "generative art", "writing"], "website": "https://everest-pipkin.com"},
    {"name": "Menkman", "country": "Netherlands", "city": "Amsterdam",
     "bio": "Dutch audiovisual artist and glitch theorist Rosa Menkman exploring glitch aesthetics and resolution theory.",
     "medium": ["glitch art", "video art", "sound art"], "website": "https://rosa-menkman.blogspot.com"},

    # ── Photography & digital manipulation ────────────────────────────────────
    {"name": "Andreas Gursky", "country": "Germany", "city": "Düsseldorf",
     "bio": "German photographer renowned for large-format, digitally manipulated photographs of contemporary life, architecture, and global capitalism.",
     "medium": ["photography", "digital manipulation"], "website": "https://andreasgursky.com"},
    {"name": "Thomas Ruff", "country": "Germany", "city": "Düsseldorf",
     "bio": "German photographer working across photography and digital image-making to interrogate the nature and construction of images.",
     "medium": ["photography", "digital art", "print"]},

    # ── Robotic & posthuman art ───────────────────────────────────────────────
    {"name": "Stelarc", "country": "Australia", "city": "Melbourne",
     "bio": "Australian-Cypriot performance artist whose works with robotics, prosthetics, and the internet explore the obsolescence of the human body.",
     "medium": ["performance", "robotic art", "body art"], "website": "https://stelarc.org"},
    {"name": "Neil Harbisson", "country": "UK", "city": "New York",
     "bio": "Catalan-raised cyborg artist and activist who perceives color as sound through an antenna implanted in his skull.",
     "medium": ["cyborg art", "performance", "sound art"], "website": "https://neilharbisson.com"},
    {"name": "Patricia Piccinini", "country": "Australia", "city": "Melbourne",
     "bio": "Australian artist creating hyper-realistic silicone sculptures imagining hybrid human-animal futures shaped by biotechnology.",
     "medium": ["sculpture", "video", "digital art"], "website": "https://patriciapiccinini.net"},

    # ── Cross-disciplinary & institutional critical ────────────────────────────
    {"name": "Forensic Architecture", "country": "UK", "city": "London",
     "bio": "Research agency led by Eyal Weizman using architectural and digital analysis to investigate human rights violations.",
     "medium": ["data art", "film", "installation"], "website": "https://forensic-architecture.org"},
    {"name": "Metahaven", "country": "Netherlands", "city": "Amsterdam",
     "bio": "Dutch design and research studio creating films, installations, and publications that explore the aesthetics of power and digital media.",
     "medium": ["film", "installation", "design"], "website": "https://metahaven.net"},
    {"name": "Constant Dullaart", "country": "Netherlands", "city": "Amsterdam",
     "bio": "Dutch internet artist whose works examine the politics of digital platforms, fake followers, and the economy of attention.",
     "medium": ["net art", "performance", "installation"], "website": "https://constantdullaart.com"},

    # ── Emerging & contemporary wave ──────────────────────────────────────────
    {"name": "Zanele Muholi", "country": "South Africa", "city": "Johannesburg",
     "bio": "South African visual activist and photographer documenting Black LGBTQIA+ lives, increasingly using digital media and projection.",
     "medium": ["photography", "video", "digital art"], "website": "https://zanemuholi.com"},
    {"name": "LaTurbo Avedon", "country": "USA", "city": "Online",
     "bio": "Avatar-based artist LaTurbo Avedon who exists entirely in digital space, curating virtual exhibitions and inhabiting game worlds as art.",
     "medium": ["virtual art", "game art", "installation"]},
    {"name": "DIS", "country": "USA", "city": "New York",
     "bio": "American art collective co-founded by Lauren Boyle, Marco Roso, Solomon Chase and David Toro exploring post-internet culture.",
     "medium": ["net art", "video", "fashion"]},
    {"name": "Amelia Ulman", "country": "Argentina", "city": "Los Angeles",
     "bio": "Argentine-Spanish artist whose 2014 Instagram performance 'Excellences & Perfections' is considered a seminal work of social media art.",
     "medium": ["social media art", "performance", "photography"], "instagram": "@amaliaulman"},
    {"name": "Lu Yang", "country": "China", "city": "Shanghai",
     "bio": "Chinese digital artist whose maximalist, anime-influenced works explore neuroscience, gender, spirituality, and digital identity.",
     "medium": ["digital animation", "installation", "video"], "website": "https://luyang.asia"},
    {"name": "Sam Spratt", "country": "USA", "city": "New York",
     "bio": "American digital illustrator known for hyperrealistic, narrative digital paintings spanning NFTs, album art, and world-building.",
     "medium": ["digital painting", "illustration", "NFT"], "website": "https://samspratt.com", "instagram": "@samspratt"},
    {"name": "Gala Porras-Kim", "country": "Colombia", "city": "Los Angeles",
     "bio": "Colombian-Korean artist working with archives, language, and data to examine how institutions interpret historical objects.",
     "medium": ["installation", "data art", "drawing"]},
    {"name": "Simon Denny", "country": "New Zealand", "city": "Berlin",
     "bio": "New Zealand artist whose installations excavate corporate and tech culture, using graphics, objects, and documents as artistic material.",
     "medium": ["installation", "digital art", "sculpture"], "website": "https://simondenny.net"},
    {"name": "Harm van den Dorpel", "country": "Netherlands", "city": "Berlin",
     "bio": "Dutch artist and developer working with blockchain and software to explore emergent behavior, aesthetics of computation, and ownership.",
     "medium": ["software art", "blockchain art", "generative art"], "website": "https://harm.work"},
    {"name": "Addie Wagenknecht", "country": "USA", "city": "New York",
     "bio": "American artist examining the intersection of technology, feminism, and open source through sculpture, video, and code.",
     "medium": ["installation", "sculpture", "code art"], "website": "https://placesiveneverbeen.com"},
    {"name": "Kevin Abosch", "country": "Ireland", "city": "Vienna",
     "bio": "Irish photographer and conceptual artist known for minimalist portrait photography and landmark blockchain-based art projects.",
     "medium": ["photography", "blockchain art", "installation"], "website": "https://kevinabosch.com"},
    {"name": "Andreas Angelidakis", "country": "Greece", "city": "Athens",
     "bio": "Greek architect and artist whose digital ruins and virtual architectures explore nostalgia, collapse, and online space.",
     "medium": ["virtual architecture", "installation", "digital art"]},
    {"name": "Alfredo Jaar", "country": "Chile", "city": "New York",
     "bio": "Chilean artist whose media installations use photography, video, and neon text to address geopolitical crises and media representation.",
     "medium": ["installation", "photography", "video"], "website": "https://alfredojaar.net"},
]


async def seed():
    import httpx
    base = "http://localhost:8000"
    async with httpx.AsyncClient(timeout=30) as client:
        existing_r = await client.get(f"{base}/api/v1/artists/?limit=200")
        existing_names = {a["name"] for a in existing_r.json()}
        print(f"Existing artists: {len(existing_names)}")

        added = 0
        skipped = 0
        for artist in ARTISTS:
            if artist["name"] in existing_names:
                skipped += 1
                continue
            payload = {
                "name": artist["name"],
                "country": artist.get("country"),
                "city": artist.get("city"),
                "bio": artist.get("bio"),
                "medium": artist.get("medium", []),
                "website": artist.get("website"),
                "instagram": artist.get("instagram"),
                "represented_by": artist.get("represented_by", []),
            }
            r = await client.post(f"{base}/api/v1/artists/", json=payload)
            if r.status_code == 200:
                data = r.json()
                if data.get("status") == "already exists":
                    skipped += 1
                else:
                    added += 1
                    print(f"  + {artist['name']}")
            else:
                print(f"  ERROR {r.status_code} for {artist['name']}: {r.text[:100]}")
            # Small delay to avoid rate-limiting the embedding API
            await asyncio.sleep(0.3)

        print(f"\nDone. Added: {added}, Skipped: {skipped}")


if __name__ == "__main__":
    asyncio.run(seed())
