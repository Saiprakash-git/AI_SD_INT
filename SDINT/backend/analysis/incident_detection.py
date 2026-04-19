import os
import sys
from datetime import datetime, timedelta
from duckduckgo_search import DDGS

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo_client import topics_collection, posts_collection

def detect_incidents():
    # Fetch active topics
    topics = list(topics_collection.find().limit(10))
    incidents = []
    
    for t in topics:
        topic_id = t.get('topic_id')
        if topic_id is None:
            continue
            
        # Handle both field names: 'top_words' (list) or 'label' (space-separated string)
        if 'top_words' in t and isinstance(t['top_words'], list):
            words = t['top_words']
        elif 'label' in t and isinstance(t['label'], str):
            words = t['label'].split()
        else:
            continue
            
        if not words:
            continue
        
        # Find posts related to this topic
        assigned_posts = list(posts_collection.find({"topic_id": topic_id}).sort("timestamp", 1))
        
        if len(assigned_posts) < 3: 
            continue
            
        # Incident Title Auto-Generation
        title = " / ".join(words[:3]).title() + " Discussion"
        
        # Severity based on total score / comments
        activity = sum([p.get('score', 0) + p.get('number_of_comments', 0) for p in assigned_posts])
        severity = min(abs(activity) // 100, 100) # 0-100 gauge
        
        # Generate Timeline
        timeline = []
        for i, p in enumerate(assigned_posts[:5]):
            phase = "Trigger" if i == 0 else "Reactions" if i == 1 else "Evolution" if i == 2 else "Current State"
            
            # Handle different timestamp formats
            ts = p.get('timestamp')
            if isinstance(ts, datetime):
                date_str = ts.strftime('%b %d, %H:%M')
            elif isinstance(ts, (int, float)):
                date_str = datetime.fromtimestamp(ts).strftime('%b %d, %H:%M')
            else:
                date_str = "Unknown"
                
            post_title = p.get('title', 'Untitled')
            summary = (post_title[:80] + "...") if len(post_title) > 80 else post_title
            
            timeline.append({
                "phase": phase,
                "date": date_str,
                "summary": summary
            })
            
        # External News Articles for context
        news = []
        try:
            query_str = " ".join(words[:2])
            with DDGS() as ddgs:
                results = list(ddgs.news(query_str, max_results=3))
                for r in results:
                    news.append({
                        "source": r.get('source'),
                        "title": r.get('title'),
                        "url": r.get('url'),
                        "date": r.get('date')
                    })
        except Exception as e:
            pass
            
        incidents.append({
            "incident_id": f"incident_{topic_id}",
            "title": title,
            "severity": severity,
            "timeline": timeline,
            "posts": [p.get('post_id') for p in assigned_posts[:10]],
            "news": news
        })
        
    # Sort by severity descending
    incidents.sort(key=lambda x: x['severity'], reverse=True)
    return incidents
