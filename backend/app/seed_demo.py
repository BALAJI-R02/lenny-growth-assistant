"""Seed script: inserts sample transcript chunks directly into Postgres for demo/testing.
Run when GitHub is unreachable: python -m app.seed_demo
"""
from __future__ import annotations
import asyncio
import asyncpg
import uuid

DB_URL = "postgresql://lenny:lennypass@localhost:5432/lennygrowth"

SAMPLE_CHUNKS = [
    {
        "episode": "How Brian Balfour Thinks About Retention",
        "guest": "Brian Balfour",
        "source_path": "episodes/brian-balfour-retention.md",
        "chunks": [
            "Retention is the single most important metric in consumer products. Brian Balfour explains that if you do not retain users you are essentially building a leaky bucket — you acquire users only to lose them. The goal should always be to find your retention curve and flatten it. A flattened retention curve means you have found product-market fit.",
            "Brian Balfour describes the habit loop as the core mechanism of retention. Users who form habits around a product tend to have dramatically higher retention. The trigger (internal or external), the action, the reward, and the investment cycle must all be designed into the product experience intentionally.",
            "Engagement loops drive long-term retention. Brian Balfour says the most successful consumer products have multiple overlapping engagement loops — social, content, utility — that keep users coming back through different motivations. Products that rely on a single loop are more fragile.",
        ],
    },
    {
        "episode": "Casey Winters on Growth and Activation",
        "guest": "Casey Winters",
        "source_path": "episodes/casey-winters-activation.md",
        "chunks": [
            "Casey Winters defines activation as the moment a new user first experiences the core value of your product. At Pinterest, activation was a user seeing their first personalized home feed. Everything in onboarding should drive toward that moment as fast as possible. Activation rate is the percentage of new users who reach that moment.",
            "Growth at Pinterest was built around making the aha moment — seeing beautiful content relevant to you — happen within the first 30 seconds. Casey Winters says reducing time-to-value is the highest leverage lever in activation. Every step that delays value delivery should be ruthlessly cut.",
            "Casey Winters explains that activation varies dramatically by channel. Users who come from SEO have very different intent than users from paid social. Great growth teams segment activation metrics by acquisition channel so they can optimize each onboarding flow independently.",
        ],
    },
    {
        "episode": "Lenny on Product-Led Growth Fundamentals",
        "guest": "Lenny Rachitsky",
        "source_path": "episodes/lenny-plg-fundamentals.md",
        "chunks": [
            "Product-led growth (PLG) means the product itself is the primary driver of acquisition, retention, and expansion. Lenny Rachitsky explains that in a PLG model the product does the selling — users discover value themselves and invite others organically. This creates compounding growth loops that are far more capital efficient than sales-led growth.",
            "The three pillars of PLG are: a product that delivers value quickly (time-to-value), viral or sharing mechanics built into the core workflow, and a freemium or free trial model that lowers the barrier to entry. Lenny Rachitsky says companies that nail all three tend to have exceptional net revenue retention above 120%.",
            "Lenny Rachitsky distinguishes between growth loops and funnels. A funnel is linear — you put users in the top and they fall through. A loop is circular — users doing actions creates more users. PLG companies like Figma and Notion built sharing loops where every file shared brought in a new potential user.",
        ],
    },
    {
        "episode": "Elena Verna on B2B Product-Led Growth",
        "guest": "Elena Verna",
        "source_path": "episodes/elena-verna-b2b-plg.md",
        "chunks": [
            "Elena Verna argues that B2B PLG is fundamentally different from B2C PLG. In B2B the buyer and the user are different people. The product must first win over the end user through genuine value, and then surface that usage data to make the case to the economic buyer. This is called product-led sales.",
            "In B2B PLG the freemium layer serves as the top of funnel. Elena Verna says the key decision is what to put behind the paywall. The best B2B PLG companies put collaboration and administrative features behind the paywall — things teams need but individuals do not. This creates organic expansion within accounts.",
            "Elena Verna explains that the biggest mistake in B2B PLG is launching freemium before achieving product-market fit. Freemium with a weak product just amplifies churn. You must first find the retention baseline among paying customers before opening the freemium funnel.",
        ],
    },
    {
        "episode": "Andrew Chen on Network Effects",
        "guest": "Andrew Chen",
        "source_path": "episodes/andrew-chen-network-effects.md",
        "chunks": [
            "Network effects occur when a product becomes more valuable as more people use it. Andrew Chen explains there are multiple types: direct network effects (each user adds value to all others), indirect network effects (more supply attracts more demand), data network effects (more usage creates better ML models), and social network effects (status and identity).",
            "The cold start problem is the biggest challenge for network-effect businesses. Andrew Chen says every marketplace and platform must solve the chicken-and-egg problem — you need supply to attract demand and demand to attract supply. The best solutions involve finding a small atomic network where value exists even with few participants.",
            "Andrew Chen describes the three phases of a network-effect business: cold start (finding atomic networks), tipping point (crossing the threshold where the product becomes self-sustaining), and escape velocity (the flywheel spins fast enough that competitors cannot catch up). Most companies fail in the cold start phase.",
        ],
    },
]


async def seed():
    conn = await asyncpg.connect(DB_URL)
    total = 0
    for ep_data in SAMPLE_CHUNKS:
        for idx, text in enumerate(ep_data["chunks"]):
            await conn.execute(
                """
                INSERT INTO chunks (id, episode, guest, source_path, chunk_index, text)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (source_path, chunk_index) DO UPDATE
                  SET text = EXCLUDED.text
                """,
                str(uuid.uuid4()),
                ep_data["episode"],
                ep_data["guest"],
                ep_data["source_path"],
                idx,
                text,
            )
            total += 1
    await conn.close()
    print(f"[OK] Seeded {total} demo chunks across {len(SAMPLE_CHUNKS)} episodes")


if __name__ == "__main__":
    asyncio.run(seed())
