from flask import Flask, jsonify
import feedparser
import json
import os
import threading
import time
from datetime import datetime, timezone
from urllib.parse import quote

app = Flask(__name__)

# --------------------------------------------------
# AI PERSONA
# --------------------------------------------------

PERSONA = {
    "name": "NOVA",
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
    ],
    "editorial_rule": (
        "Publish only meaningful AI or technology developments "
        "that have practical or strategic relevance."
    )
}

# --------------------------------------------------
# DATA / MEMORY
# --------------------------------------------------

DATA_DIR = "data"
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")

os.makedirs(DATA_DIR, exist_ok=True)


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {
            "published": [],
            "rejected": []
        }

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "published": [],
            "rejected": []
        }


memory = load_memory()


def save_memory():
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)


# --------------------------------------------------
# LIVE TOPIC DISCOVERY
# --------------------------------------------------

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


def discover_topics():
    topics = []

    for source in RSS_SOURCES:
        try:
            feed = feedparser.parse(source["url"])

            for entry in feed.entries[:8]:
                title = entry.get("title", "").strip()
                summary = entry.get("summary", "").strip()
                link = entry.get("link", "")

                if title:
                    topics.append({
                        "title": title,
                        "summary": summary,
                        "source": source["name"],
                        "link": link
                    })

        except Exception as e:
            print("Source error:", source["name"], e)

    return topics


# --------------------------------------------------
# EDITORIAL JUDGMENT
# --------------------------------------------------

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
    "generative"
]

BAD_KEYWORDS = [
    "celebrity",
    "sports",
    "movie",
    "entertainment",
    "recipe",
    "fashion",
    "politics"
]


def evaluate_topic(topic):
    text = (
        topic["title"] + " " +
        topic["summary"]
    ).lower()

    score = 0

    for word in GOOD_KEYWORDS:
        if word in text:
            score += 2

    for word in BAD_KEYWORDS:
        if word in text:
            score -= 4

    # Avoid publishing the same topic again
    for post in memory["published"]:
        old_title = post.get("topic", "").lower()

        if topic["title"].lower() == old_title:
            return False, 0, "Rejected because this topic was already published."

    if score >= 3:
        return True, score, "The topic has strong relevance to AI and technology."

    return False, score, "Rejected because it does not meet NOVA's editorial standard."


# --------------------------------------------------
# CONTENT CREATION
# --------------------------------------------------

def create_post(topic):
    title = topic["title"]

    post_text = (
        f"🔎 NOVA AI Technology Brief\n\n"
        f"{title}\n\n"
        f"My take: This development matters because it shows "
        f"how AI and technology are continuing to move from "
        f"experiments toward practical systems.\n\n"
        f"I am watching this area closely, especially for its "
        f"impact on developers, AI agents and real-world applications."
    )

    return post_text


# --------------------------------------------------
# PUBLISHING
# --------------------------------------------------

def publish_topic(topic, score, decision_reason):
    post = {
        "id": len(memory["published"]) + 1,
        "persona": PERSONA["name"],
        "role": PERSONA["role"],
        "topic": topic["title"],
        "content": create_post(topic),
        "published_at": datetime.now(timezone.utc).isoformat(),
        "source": topic["source"],
        "source_url": topic["link"],

        # Publishing rationale
        "rationale": {
            "why_selected": decision_reason,
            "why_relevant_now": (
                "The topic was discovered from a live information "
                "source and contains current AI or technology signals."
            ),
            "editorial_score": score
        }
    }

    memory["published"].append(post)

    # Keep memory manageable
    memory["published"] = memory["published"][-100:]

    save_memory()

    return post


# --------------------------------------------------
# AUTONOMOUS AGENT
# --------------------------------------------------

def autonomous_cycle():
    print("NOVA autonomous agent started.")

    while True:
        try:
            print("Discovering live AI topics...")

            topics = discover_topics()

            for topic in topics:
                should_publish, score, reason = evaluate_topic(topic)

                if should_publish:
                    post = publish_topic(
                        topic,
                        score,
                        reason
                    )

                    print(
                        "Published:",
                        post["topic"]
                    )

                    # Publish only one good topic per cycle
                    break

                else:
                    memory["rejected"].append({
                        "topic": topic["title"],
                        "reason": reason,
                        "checked_at": datetime.now(
                            timezone.utc
                        ).isoformat()
                    })

            save_memory()

        except Exception as e:
            print("Autonomous cycle error:", e)

        # Wait before checking again.
        # This makes publishing happen over time.
        time.sleep(30 * 60)


# --------------------------------------------------
# API ENDPOINTS
# --------------------------------------------------

@app.route("/")
def home():
    return jsonify({
        "message": "NOVA Autonomous AI Persona is running!",
        "persona": PERSONA["name"],
        "role": PERSONA["role"],
        "status": "autonomous"
    })


@app.route("/feed")
def feed():
    return jsonify({
        "persona": PERSONA,
        "posts": memory["published"],
        "total_published": len(memory["published"]),
        "total_rejected": len(memory["rejected"])
    })


@app.route("/memory")
def show_memory():
    return jsonify(memory)


@app.route("/status")
def status():
    return jsonify({
        "status": "running",
        "persona": PERSONA["name"],
        "published_posts": len(memory["published"]),
        "rejected_topics": len(memory["rejected"]),
        "autonomous": True,
        "publishing_interval": "30 minutes"
    })


# --------------------------------------------------
# START AGENT
# --------------------------------------------------

if __name__ == "__main__":

    # Start autonomous agent in background
    agent_thread = threading.Thread(
        target=autonomous_cycle,
        daemon=True
    )

    agent_thread.start()

    # Start Flask API
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )