from datetime import UTC, datetime, timedelta

from models import (
    Category,
    Episode,
    EpisodeStatus,
    Host,
    HostRole,
    Podcast,
    PodcastStatus,
)


def seed() -> None:
    # ── Categories ─────────────────────────────────────────────────────────────

    tech = Category(
        name="Technology",
        color="#4e79a7",
        description="Software, hardware, AI, and the digital world.",
    ).save()
    comedy = Category(
        name="Comedy",
        color="#59a14f",
        description="Laughs, satire, and light-hearted storytelling.",
    ).save()
    true_crime = Category(
        name="True Crime",
        color="#e15759",
        description="Real investigations, mysteries, and criminal cases.",
    ).save()
    business = Category(
        name="Business",
        color="#f28e2b",
        description="Entrepreneurship, startups, finance, and strategy.",
    ).save()
    science = Category(
        name="Science",
        color="#76b7b2",
        description="Physics, biology, space, and the natural world.",
    ).save()
    self_help = Category(
        name="Self-Help",
        color="#edc948",
        description="Productivity, mindset, and personal development.",
    ).save()

    # ── Hosts ──────────────────────────────────────────────────────────────────

    alex = Host(
        full_name="Alex Rivera",
        email="alex@stacktrace.fm",
        bio=(
            "Senior software engineer turned podcaster. Obsessed with distributed "
            "systems, Python, and open-source communities."
        ),
        role=HostRole.HOST,
        joined_at=datetime.now(UTC) - timedelta(days=400),
    ).save()

    sam = Host(
        full_name="Sam Chen",
        email="sam@stacktrace.fm",
        bio="DevOps engineer and cloud architect. Makes Kubernetes sound almost fun.",
        role=HostRole.CO_HOST,
        joined_at=datetime.now(UTC) - timedelta(days=380),
    ).save()

    maya = Host(
        full_name="Maya Patel",
        email="maya@crimescene.fm",
        bio=(
            "Investigative journalist with 12 years covering criminal justice. "
            "Hosts Crime Scene Weekly."
        ),
        role=HostRole.HOST,
        joined_at=datetime.now(UTC) - timedelta(days=300),
    ).save()

    jordan = Host(
        full_name="Jordan Lee",
        email="jordan@startupfuel.co",
        bio="Three-time founder, angel investor, and startup advisor.",
        role=HostRole.HOST,
        joined_at=datetime.now(UTC) - timedelta(days=200),
    ).save()

    # ── Podcasts ───────────────────────────────────────────────────────────────

    stack_trace = Podcast(
        title="The Stack Trace",
        slug="the-stack-trace",
        description=(
            "Weekly deep-dives into software engineering: architecture decisions, "
            "debugging war stories, and the tools that make or break a codebase."
        ),
        language="en",
        featured=True,
        tags=["software", "engineering", "open-source", "python"],
        categories=[tech],
        status=PodcastStatus.ACTIVE,
        created_at=datetime.now(UTC) - timedelta(days=365),
    ).save()

    crime_scene = Podcast(
        title="Crime Scene Weekly",
        slug="crime-scene-weekly",
        description=(
            "Real cases, real investigations. Maya Patel walks through the evidence "
            "one crime at a time, from cold cases to courtroom drama."
        ),
        language="en",
        featured=True,
        tags=["investigation", "cold-cases", "justice"],
        categories=[true_crime],
        status=PodcastStatus.ACTIVE,
        created_at=datetime.now(UTC) - timedelta(days=280),
    ).save()

    startup_fuel = Podcast(
        title="Startup Fuel",
        slug="startup-fuel",
        description=(
            "Candid conversations with founders who've been in the trenches. "
            "Fundraising, hiring, pivots, and the moments that define companies."
        ),
        language="en",
        featured=False,
        tags=["startups", "venture-capital", "entrepreneurship"],
        categories=[business],
        status=PodcastStatus.ACTIVE,
        created_at=datetime.now(UTC) - timedelta(days=180),
    ).save()

    cosmos = Podcast(
        title="Cosmos Explored",
        slug="cosmos-explored",
        description=(
            "Astrophysics, quantum mechanics, and the biggest questions in science, "
            "explained without the jargon."
        ),
        language="en",
        featured=False,
        tags=["astronomy", "physics", "space", "science"],
        categories=[science],
        status=PodcastStatus.DRAFT,
        created_at=datetime.now(UTC) - timedelta(days=30),
    ).save()

    Podcast(
        title="Laugh Track",
        slug="laugh-track",
        description="Stand-up sets, comedy interviews, and the business of being funny.",
        language="en",
        featured=False,
        tags=["stand-up", "improv", "humor"],
        categories=[comedy, self_help],
        status=PodcastStatus.ARCHIVED,
        created_at=datetime.now(UTC) - timedelta(days=500),
    ).save()

    # ── Episodes ───────────────────────────────────────────────────────────────

    # The Stack Trace episodes
    Episode(
        podcast=stack_trace,
        host=alex,
        title="Python 3.13 Deep Dive",
        episode_number=1,
        season=1,
        duration_minutes=58,
        published_at=datetime.now(UTC) - timedelta(days=340),
        status=EpisodeStatus.PUBLISHED,
        notes="Covers JIT compiler, free-threading, and the new REPL improvements.",
    ).save()

    Episode(
        podcast=stack_trace,
        host=sam,
        title="Building Async APIs That Don't Lie",
        episode_number=2,
        season=1,
        duration_minutes=72,
        published_at=datetime.now(UTC) - timedelta(days=320),
        status=EpisodeStatus.PUBLISHED,
    ).save()

    Episode(
        podcast=stack_trace,
        host=alex,
        title="Observability in 2025: Beyond Logs",
        episode_number=3,
        season=1,
        duration_minutes=65,
        published_at=datetime.now(UTC) - timedelta(days=300),
        status=EpisodeStatus.PUBLISHED,
        notes="OpenTelemetry, distributed tracing, and why your logs are lying to you.",
    ).save()

    Episode(
        podcast=stack_trace,
        host=alex,
        title="The Future of AI-Assisted Coding",
        episode_number=4,
        season=1,
        duration_minutes=80,
        published_at=None,
        status=EpisodeStatus.DRAFT,
        notes="Rough outline: co-pilots, agents, and where human judgment still wins.",
    ).save()

    # Crime Scene Weekly episodes
    Episode(
        podcast=crime_scene,
        host=maya,
        title="The Missing Manuscript",
        episode_number=1,
        season=1,
        duration_minutes=45,
        published_at=datetime.now(UTC) - timedelta(days=250),
        status=EpisodeStatus.PUBLISHED,
        notes="A stolen rare book, three suspects, and a trail of forged provenance.",
    ).save()

    Episode(
        podcast=crime_scene,
        host=maya,
        title="Digital Footprints",
        episode_number=2,
        season=1,
        duration_minutes=52,
        published_at=datetime.now(UTC) - timedelta(days=220),
        status=EpisodeStatus.ARCHIVED,
    ).save()

    Episode(
        podcast=crime_scene,
        host=maya,
        title="The Vanishing Archivist",
        episode_number=3,
        season=1,
        duration_minutes=61,
        published_at=datetime.now(UTC) - timedelta(days=15),
        status=EpisodeStatus.PUBLISHED,
    ).save()

    # Startup Fuel episodes
    Episode(
        podcast=startup_fuel,
        host=jordan,
        title="From Zero to Series A: The Unfiltered Truth",
        episode_number=1,
        season=1,
        duration_minutes=90,
        published_at=datetime.now(UTC) - timedelta(days=160),
        status=EpisodeStatus.PUBLISHED,
        notes="Guests: founders from three different verticals share their fundraising playbook.",
    ).save()

    Episode(
        podcast=startup_fuel,
        host=jordan,
        title="Hiring Your First 10 Engineers",
        episode_number=2,
        season=1,
        duration_minutes=68,
        published_at=datetime.now(UTC) - timedelta(days=130),
        status=EpisodeStatus.PUBLISHED,
    ).save()

    Episode(
        podcast=startup_fuel,
        host=jordan,
        title="When to Pivot (and When to Double Down)",
        episode_number=3,
        season=1,
        duration_minutes=55,
        published_at=None,
        status=EpisodeStatus.DRAFT,
    ).save()

    # Cosmos Explored episodes
    Episode(
        podcast=cosmos,
        host=alex,
        title="Dark Matter Demystified",
        episode_number=1,
        season=1,
        duration_minutes=42,
        published_at=None,
        status=EpisodeStatus.DRAFT,
        notes="Target release: next month. Still waiting on interview with Dr. Okonkwo.",
    ).save()
