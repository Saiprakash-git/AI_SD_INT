from flask import Flask, jsonify, request
from flask_cors import CORS
from bson import json_util
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apscheduler.schedulers.background import BackgroundScheduler
from db.mongo_client import db
from analysis.narrative_arc import compute_narrative_arc
from analysis.opinion_divergence import compute_opinion_divergence
import rss_collector

app = Flask(__name__)
CORS(app)

def parse_json(data):
    return json.loads(json_util.dumps(data))

# Scheduler Setup
scheduler = BackgroundScheduler()
# Needs to run in an active context or just start
scheduler.add_job(func=rss_collector.fetch_rss_live_data, trigger="interval", minutes=3)
scheduler.add_job(func=rss_collector.compute_all_echo_chambers, trigger="interval", minutes=30)
scheduler.start()

@app.route('/')
def root():
    return jsonify({"message": "API is running"})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Social Discussion Analytics API is running"})

@app.route('/api/topics/trending', methods=['GET'])
def get_trending_topics():
    trends = list(db["trends"].find().sort("frequency", -1))
    return jsonify(parse_json(trends))

@app.route('/api/trends/<topic_id>/analytics', methods=['GET'])
def get_trend_analytics(topic_id):
    from datetime import datetime
    posts = list(db["posts"].find({"topic_id": int(topic_id)}).sort("created_utc", 1))
    
    # Timeline data for LineChart mapping
    timeline_dict = {}
    total_running = 0
    for p in posts:
        total_running += 1
        ts = p.get("created_utc", 0)
        dt_str = datetime.fromtimestamp(ts).strftime('%m/%d/%Y %H:00')
        timeline_dict[dt_str] = total_running
    
    timeline = [{"time": k, "mentions": v} for k, v in timeline_dict.items()]
    
    # Origin post
    origin_post = posts[0] if posts else None
    origin = {
        "title": origin_post.get("title", "Unknown Origin") if origin_post else "Unknown Origin",
        "date": datetime.fromtimestamp(origin_post["created_utc"]).strftime('%m/%d/%Y %H:%M') if origin_post else "Unknown"
    } if origin_post else None
    
    return jsonify({"timeline": timeline, "origin": origin})

@app.route('/api/posts', methods=['GET'])
def get_posts_by_topic():
    topic_id = request.args.get('topic_id')
    query = {}
    if topic_id is not None:
        query = {"topic_id": int(topic_id)}
        
    posts = list(db["posts"].find(query).sort("score", -1).limit(20))
    return jsonify(parse_json(posts))

@app.route('/api/posts/<post_id>/summary', methods=['GET'])
def get_post_summary(post_id):
    post = db["posts"].find_one({"post_id": post_id}, {"summary": 1})
    if post and "summary" in post:
        return jsonify({"post_id": post_id, "summary": post["summary"]})
    return jsonify({"error": "Summary not found"}), 404

@app.route('/api/posts/<post_id>/sentiment', methods=['GET'])
def get_post_sentiment(post_id):
    post = db["posts"].find_one({"post_id": post_id}, {"sentiment_distribution": 1})
    if post and "sentiment_distribution" in post:
        return jsonify({"post_id": post_id, "sentiment": post["sentiment_distribution"]})
    return jsonify({"error": "Sentiment data not found"}), 404

@app.route('/api/comments/toxic', methods=['GET'])
def get_toxic_comments():
    comments = list(db["comments"].find({"is_toxic": True}).sort("toxicity_score", -1).limit(50))
    return jsonify(parse_json(comments))

@app.route('/api/posts/<post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    comments = list(db["comments"].find({"post_id": post_id}).sort("score", -1).limit(100))
    return jsonify(parse_json(comments))

@app.route('/api/status', methods=['GET'])
def get_status():
    status = list(db["rss_status"].find())
    return jsonify(parse_json(status))

@app.route('/api/posts/<post_id>/narrative-arc', methods=['GET'])
def get_narrative_arc(post_id):
    post = db["posts"].find_one({"post_id": post_id}, {"narrative_arc": 1})
    if post and "narrative_arc" in post and post["narrative_arc"]:
        return jsonify(parse_json(post["narrative_arc"]))
    # Compute on demand
    res = compute_narrative_arc(post_id)
    return jsonify(parse_json(res))

@app.route('/api/posts/<post_id>/opinion-divergence', methods=['GET'])
def get_opinion_divergence(post_id):
    post = db["posts"].find_one({"post_id": post_id}, {"opinion_divergence": 1})
    if post and "opinion_divergence" in post and post["opinion_divergence"]:
        return jsonify(parse_json(post["opinion_divergence"]))
    # Compute on demand
    res = compute_opinion_divergence(post_id)
    return jsonify(parse_json(res))

@app.route('/api/subreddits/echo-chamber', methods=['GET'])
def get_all_echo_chambers():
    scores = list(db["subreddit_metrics"].find().sort("echo_chamber_score", -1))
    return jsonify(parse_json(scores))

@app.route('/api/subreddits/<subreddit>/echo-chamber', methods=['GET'])
def get_echo_chamber(subreddit):
    doc = db["subreddit_metrics"].find_one({"subreddit": subreddit})
    return jsonify(parse_json(doc))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
