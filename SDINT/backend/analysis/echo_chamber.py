import sys
import os
import math
from collections import Counter
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo_client import comments_collection, posts_collection, db
from nlp.preprocess import clean_text

def compute_echo_chamber_score(subreddit):
    posts = list(posts_collection.find({"subreddit": subreddit}).sort("created_utc", -1).limit(200))
    if not posts:
        return None
        
    post_ids = [p["post_id"] for p in posts]
    comments = list(comments_collection.find({"post_id": {"$in": post_ids}}))
    
    # 1. Sentiment homogeneity
    vader_scores = [float(c.get("sentiment", {}).get("compound", 0.0)) for c in comments if "sentiment" in c]
    if len(vader_scores) > 1:
        std_dev = float(np.std(vader_scores))
        sh = max(0.0, min(1.0, 1.0 - std_dev))
    else:
        sh = 1.0
        
    # 2. Topic concentration
    topics = [p.get("topic_id", -1) for p in posts]
    valid_topics = [t for t in topics if t != -1]
    if valid_topics:
        freq = Counter(valid_topics)
        most_common = freq.most_common(1)[0][1]
        tc = most_common / len(valid_topics)
    else:
        tc = 0.0
        
    # 3. Vocabulary insularity
    texts = " ".join([c.get("text", "") for c in comments])
    clean_words = clean_text(texts).split()
    if len(clean_words) > 0:
        unique_tokens = len(set(clean_words))
        ttr = unique_tokens / len(clean_words)
        norm_ttr = max(0.0, min(1.0, (ttr - 0.1) / 0.4))
        vi = 1.0 - norm_ttr
    else:
        vi = 0.0
        
    final = (0.4 * sh) + (0.35 * tc) + (0.25 * vi)
    
    if final >= 0.75:
        lbl = "strong echo chamber"
    elif final >= 0.55:
        lbl = "moderate echo chamber"
    elif final >= 0.35:
        lbl = "mixed"
    else:
        lbl = "diverse"
        
    from datetime import datetime
    doc = {
        "subreddit": subreddit,
        "echo_chamber_score": round(final, 2),
        "classification": lbl,
        "sub_scores": {
            "sentiment_homogeneity": round(sh, 2),
            "topic_concentration": round(tc, 2),
            "vocabulary_insularity": round(vi, 2)
        },
        "posts_analyzed": len(posts),
        "computed_at": datetime.utcnow().isoformat()
    }
    db["subreddit_metrics"].update_one({"subreddit": subreddit}, {"$set": doc}, upsert=True)
    return doc
