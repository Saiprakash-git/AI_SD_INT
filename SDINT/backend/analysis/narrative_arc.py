import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo_client import comments_collection, posts_collection

def compute_narrative_arc(post_id):
    post = posts_collection.find_one({"post_id": post_id})
    if not post:
        return None
    
    comments = list(comments_collection.find({"post_id": post_id}).sort("created_utc", 1))
    
    if not comments:
        result = {
            "post_id": post_id,
            "arc_shape": "neutral",
            "arc_events": [],
            "timeline": [],
            "summary": {
                "total_comments": 0,
                "avg_sentiment": 0,
                "peak_positive_index": -1,
                "peak_negative_index": -1
            }
        }
        posts_collection.update_one({"post_id": post_id}, {"$set": {"narrative_arc": result}}, upsert=True)
        return result

    timeline = []
    window = []
    
    arc_events = []
    prev_rolling = 0.0
    
    peak_pos_idx = -1
    peak_neg_idx = -1
    max_pos = -1.0
    max_neg = 1.0
    
    total_score = 0.0
    
    for i, c in enumerate(comments):
        sentiment_data = c.get("sentiment", {})
        raw = float(sentiment_data.get("compound", 0.0))
        label = c.get("sentiment_label", "neutral")
        
        window.append(raw)
        if len(window) > 5:
            window.pop(0)
            
        rolling_avg = sum(window) / len(window)
        total_score += raw
        
        if raw > max_pos:
            max_pos = raw
            peak_pos_idx = i
        if raw < max_neg:
            max_neg = raw
            peak_neg_idx = i
            
        if i >= 4:
            if prev_rolling >= -0.2 and rolling_avg < -0.2:
                arc_events.append({"index": i, "type": "turned_negative", "score": round(rolling_avg, 3)})
            elif prev_rolling <= 0.2 and rolling_avg > 0.2:
                arc_events.append({"index": i, "type": "turned_positive", "score": round(rolling_avg, 3)})
            
            if abs(rolling_avg - prev_rolling) > 0.5:
                arc_events.append({"index": i, "type": "controversy_spike", "score": round(rolling_avg, 3)})
                
        prev_rolling = rolling_avg
        
        timeline.append({
            "comment_index": i,
            "raw_score": round(raw, 3),
            "rolling_avg": round(rolling_avg, 3),
            "label": label
        })
        
    avg_sentiment = total_score / len(comments)
    final_avg = timeline[-1]["rolling_avg"]
    
    start_avg = 0.0
    end_avg = 0.0
    first_20_len = max(1, int(len(timeline)*0.2))
    last_20_len = max(1, int(len(timeline)*0.2))
    start_avg = sum([t["rolling_avg"] for t in timeline[:first_20_len]]) / first_20_len
    end_avg = sum([t["rolling_avg"] for t in timeline[-last_20_len:]]) / last_20_len
        
    spike_events = sum(1 for e in arc_events if e["type"] == "controversy_spike")
    all_rolling = [t["rolling_avg"] for t in timeline[4:]] if len(timeline) >= 5 else [t["rolling_avg"] for t in timeline]
    min_rolling = min(all_rolling) if all_rolling else 0.0
    max_rolling = max(all_rolling) if all_rolling else 0.0
    
    if spike_events > 3:
        arc_shape = "volatile"
    elif final_avg > 0.2 and min_rolling >= -0.1:
        arc_shape = "steady_positive"
    elif final_avg < -0.2 and max_rolling <= 0.1:
        arc_shape = "steady_negative"
    elif start_avg > 0.1 and end_avg < -0.1:
        arc_shape = "deteriorating"
    elif start_avg < -0.1 and end_avg > 0.1:
        arc_shape = "recovering"
    else:
        arc_shape = "neutral"
        
    result = {
        "post_id": post_id,
        "arc_shape": arc_shape,
        "arc_events": arc_events,
        "timeline": timeline,
        "summary": {
            "total_comments": len(comments),
            "avg_sentiment": round(avg_sentiment, 3),
            "peak_positive_index": peak_pos_idx,
            "peak_negative_index": peak_neg_idx
        }
    }
    
    posts_collection.update_one({"post_id": post_id}, {"$set": {"narrative_arc": result}})
    return result
