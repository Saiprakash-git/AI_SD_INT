from flask import Flask, jsonify, request
from flask_cors import CORS
from bson import json_util
import json

from db.mongo_client import db

app = Flask(__name__)
CORS(app)

def parse_json(data):
    return json.loads(json_util.dumps(data))

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Social Discussion Analytics API is running"})

@app.route('/api/topics/trending', methods=['GET'])
def get_trending_topics():
    trends = list(db["trends"].find().sort("frequency", -1))
    return jsonify(parse_json(trends))

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
