import os
import sys
from datetime import datetime, timedelta
from duckduckgo_search import DDGS

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo_client import posts_collection

def construct_narrative(query):
    # Search posts regex
    cursor = posts_collection.find({
        "$or": [
            {"title": {"$regex": query, "$options": "i"}},
            {"content": {"$regex": query, "$options": "i"}}
        ]
    }).sort("timestamp", 1)  # Chronological
    
    posts = list(cursor)
    
    timeline = []
    
    # 1. Timeline Construction
    if posts:
        # Group by day or roughly create nodes
        for p in posts:
            # We want each to be a timeline node
            ts = p.get('timestamp') or datetime.utcnow()
            dt_str = ts.strftime('%Y-%m-%d %H:%M')
            timeline.append({
                "date": dt_str,
                "summary": f"{p.get('subreddit')}: {p.get('title')[:100]}...",
                "post_id": p.get('post_id'),
                "sentiment_state": "mixed", # Defaulting dynamically for now
                "activity_score": 1 + (p.get('score', 0) / 1000)
            })
            
    # 2. External News Overlay
    external_news = []
    try:
        with DDGS() as ddgs:
            # Fetch latest news
            results = ddgs.news(query, max_results=5)
            # DDG news result structure: title, body, date, url, source
            for r in results:
                external_news.append({
                    "date": r.get('date', ''),
                    "headline": r.get('title', ''),
                    "source": r.get('source', ''),
                    "url": r.get('url', '')
                })
    except Exception as e:
        print("DuckDuckGo News Error:", e)
        
    # Find active duration
    days_ago = 0
    if timeline:
        first_dt = datetime.strptime(timeline[0]['date'], '%Y-%m-%d %H:%M')
        days_ago = (datetime.utcnow() - first_dt).days
        
    return {
        "query": query,
        "first_appeared_days_ago": days_ago,
        "total_posts": len(posts),
        "peaked_on": timeline[len(timeline)//2]['date'] if timeline else "Unknown",
        "current_sentiment": "mixed",
        "timeline": timeline,
        "external_news": external_news
    }
