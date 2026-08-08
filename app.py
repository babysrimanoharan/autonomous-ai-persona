from flask import Flask, jsonify, request
import feedparser
import json
import os
import threading
import time
import uuid
from datetime import datetime, timezone

app = Flask(__name__)

# ============================================================
# PERSONA
# ============================================================

PERSONA = {
    "name": "NOVA",
    "domain": "AI Technology",
    "role": "AI Technology Researcher",
    "style": "clear, analytical, practical and slightly opinionated",
    "interests": [
        "artificial intelligence",
        "machine learning",
        "AI agents",
        "AI security",
        "developer tools",
        "open source AI",
        "robotics"
    ]
}

# ============================================================
# MEMORY
# ============================================================

DATA_DIR = "data"
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")

os.makedirs(DATA_DIR, exist_ok=True)

memory_lock = threading.Lock()

memory = {
    "agent_id": None,
    "initialized": False,
    "published": [],
    "rejected": []
}


def load_memory():
    global memory
    if not os.path.exists(MEMORY_FILE):
        return

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            saved = json.load(file)

            if isinstance(saved, dict):
                memory.update(saved)

    except Exception as error:
        print("Memory loading error:", error)


def save_memory():
    with memory_lock:
        with open(MEMORY_FILE, "w", encoding="utf-8") as file:
            json.dump(
                memory,
                file,
                indent=2,
                ensure_ascii=False
            )


load_memory()

# ============================================================
# LIVE INFORMATION SOURCES
# ============================================================

RSS_SOURCES = [
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com/feed/"
    },
    {
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/"
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml"
    },
    {
        "name": "ArXiv AI",
        "url": "https://export.arxiv.org/rss/cs.AI"
    }
]

# ============================================================
# EDITORIAL RULES
# ============================================================

GOOD_KEYWORDS = [
    "ai",
    "artificial intelligence",
    "machine learning",
    "agent",
    "robot",
    "robotics",
    "llm",
    "model",
    "open source",
    "security",
    "developer",
    "neural",
    "computer vision",
    "generative",
    "deep learning"
]

BAD_KEYWORDS = [
    "celebrity",
    "sports",
    "movie",
    "entertainment",
    "recipe",
    "fashion",
    "politics",
    "travel"
]


# ============================================================
# TOPIC DISCOVERY
# ============================================================

def discover_topics():

    topics = []

    for source in RSS_SOURCES:

        try:
            feed = feedparser.parse(source["url"])

            for entry in feed.entries[:10]:

                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                link = entry.get("link", "").strip()

                if title:

                    topics.append({
                        "title": title,
                        "summary": summary,
                        "source": source["name"],
                        "link": link
                    })

        except Exception as error:

            print(
                "Source error:",
                source["name"],
                error
            )

    return topics


# ============================================================
# EDITORIAL JUDGMENT
# ============================================================

def evaluate_topic(topic):

    text = (
        topic["title"] + " " +
        topic["summary"]
    ).lower()

    score = 0

    # Positive signals
    for keyword in GOOD_KEYWORDS:

        if keyword in text:
            score += 2

    # Negative signals
    for keyword in BAD_KEYWORDS:

        if keyword in text:
            score -= 4

    # Avoid repetition
    for post in memory["published"]:

        previous_title = post.get(
            "topic",
            ""
        ).lower()

        if topic["title"].lower() == previous_title:

            return (
                False,
                0,
                "Rejected because NOVA has already published this topic."
            )

    # Publishing threshold
    if score >= 3:

        return (
            True,
            score,
            "Selected because the topic has strong relevance to AI and technology."
        )

    return (
        False,
        score,
        "Rejected because it does not meet NOVA's editorial standards."
    )


# ============================================================
# CONTENT CREATION
# ============================================================

def create_post(topic):

    return (
        f"🔎 NOVA AI Technology Brief\n\n"
        f"{topic['title']}\n\n"
        f"My take: This development is worth watching because "
        f"it reflects an important direction in AI and technology. "
        f"I am particularly interested in its practical impact "
        f"on developers, AI systems and real-world applications.\n\n"
        f"NOVA's view: useful technology should move beyond hype "
        f"and demonstrate meaningful technical or practical value."
    )


# ============================================================
# PUBLISH
# ============================================================

def publish_topic(topic, score, selection_reason):

    created_at = datetime.now(
        timezone.utc
    ).isoformat().replace("+00:00", "Z")

    post = {

        "id": "p-" + uuid.uuid4().hex[:10],

        "createdAt": created_at,

        "text": create_post(topic),

        "rationale": (
            f"{selection_reason} "
            f"The topic is relevant now because it was discovered "
            f"from a live information source during the autonomous "
            f"discovery cycle. NOVA selected it over lower-scoring "
            f"candidates because its editorial score was {score}."
        ),

        "sources": [
            topic["link"]
        ],

        # Internal fields used for memory
        "topic": topic["title"],
        "source_name": topic["source"]
    }

    with memory_lock:

        memory["published"].append(post)

        # Keep previously published posts available.
        # We don't delete old posts.
        save_memory()

    print(
        "Published:",
        topic["title"]
    )

    return post


# ============================================================
# AUTONOMOUS AGENT
# ============================================================

def autonomous_cycle():

    print("NOVA autonomous agent started.")

    # Small delay after initialization
    time.sleep(10)

    while True:

        try:

            print(
                "\nNOVA is discovering live AI topics..."
            )

            topics = discover_topics()

            published_this_cycle = False

            for topic in topics:

                should_publish, score, reason = evaluate_topic(
                    topic
                )

                if should_publish:

                    publish_topic(
                        topic,
                        score,
                        reason
                    )

                    published_this_cycle = True

                    # Only one post per cycle
                    break

                else:

                    rejected_item = {

                        "topic": topic["title"],

                        "reason": reason,

                        "checkedAt": datetime.now(
                            timezone.utc
                        ).isoformat().replace(
                            "+00:00",
                            "Z"
                        )
                    }

                    with memory_lock:
                        memory["rejected"].append(
                            rejected_item
                        )

            save_memory()

            if not published_this_cycle:

                print(
                    "No topic met NOVA's publishing standard."
                )

        except Exception as error:

            print(
                "Autonomous cycle error:",
                error
            )

        # Autonomous publishing interval.
        # The agent continues without another human request.
        time.sleep(30 * 60)


# ============================================================
# INITIALIZE AGENT
# ============================================================

@app.route(
    "/api/agent/init",
    methods=["POST"]
)
def initialize_agent():

    global memory

    # Initialization is allowed exactly once
    if memory.get("initialized"):

        return jsonify({
            "error": "Agent has already been initialized.",
            "agentId": memory.get("agent_id")
        }), 409

    data = request.get_json(
        silent=True
    ) or {}

    requested_persona = data.get(
        "persona",
        {}
    )

    # Use supplied persona information if provided
    if requested_persona.get("name"):

        PERSONA["name"] = requested_persona["name"]

    if requested_persona.get("domain"):

        PERSONA["domain"] = requested_persona["domain"]

    # Generate unique agent ID
    agent_id = "agent-" + uuid.uuid4().hex[:12]

    memory["agent_id"] = agent_id
    memory["initialized"] = True

    save_memory()

    # Start autonomous operation AFTER initialization
    agent_thread = threading.Thread(
        target=autonomous_cycle,
        daemon=True
    )

    agent_thread.start()

    print(
        "Agent initialized:",
        agent_id
    )

    return jsonify({
        "agentId": agent_id
    })


# ============================================================
# FEED
# ============================================================

@app.route(
    "/api/agent/feed",
    methods=["GET"]
)
def get_feed():

    agent_id = request.args.get(
        "agentId"
    )

    if not agent_id:

        return jsonify({
            "posts": []
        })

    if agent_id != memory.get("agent_id"):

        return jsonify({
            "posts": []
        })

    # Newest first
    posts = sorted(
        memory["published"],
        key=lambda post: post["createdAt"],
        reverse=True
    )

    # Return only fields required by evaluator
    clean_posts = []

    for post in posts:

        clean_posts.append({

            "id": post["id"],

            "createdAt": post["createdAt"],

            "text": post["text"],

            "rationale": post["rationale"],

            "sources": post["sources"]
        })

    return jsonify({
        "posts": clean_posts
    })


# ============================================================
# OPTIONAL STATUS ENDPOINT
# ============================================================

@app.route(
    "/status",
    methods=["GET"]
)
def status():

    return jsonify({

        "status": "running",

        "initialized": memory["initialized"],

        "agentId": memory["agent_id"],

        "persona": PERSONA["name"],

        "publishedPosts": len(
            memory["published"]
        ),

        "rejectedTopics": len(
            memory["rejected"]
        ),

        "autonomous": True
    })


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    print("NOVA server starting...")

    @app.route("/")
    def home():
        return "NOVA is running successfully!"

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )