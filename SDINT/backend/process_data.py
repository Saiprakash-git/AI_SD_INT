import sys
import os
from datetime import datetime
from collections import Counter

# Ensure backend root is in Python path for importing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.mongo_client import posts_collection, comments_collection, db
from nlp.topic_modeling import perform_topic_modeling, get_dominant_topic
from nlp.sentiment import analyze_sentiment
from nlp.toxicity import detect_toxicity
from nlp.clustering import cluster_comments
from nlp.summarization import summarize_text

def process_nlp_pipeline():
    print("Starting NLP processing pipeline...")
    
    # Process Comments: Sentiment & Toxicity
    unprocessed_comments = list(comments_collection.find({"sentiment_label": {"$exists": False}}).limit(1000))
    print(f"Found {len(unprocessed_comments)} un-processed comments.")
    
    for comment in unprocessed_comments:
        text = comment.get("text", "")
        # Sentiment
        scores, label = analyze_sentiment(text)
        
        # Toxicity
        tox_score, is_toxic = detect_toxicity(text)
        
        # Update comment
        comments_collection.update_one(
            {"_id": comment["_id"]},
            {"$set": {
                "sentiment": scores,
                "sentiment_label": label,
                "toxicity_score": tox_score,
                "is_toxic": is_toxic
            }}
        )
        print(f"Processed comment ID {comment.get('comment_id')}")

    # Process Posts: Clustering, Summarization & Topic Modeling
    # Let's get all recent posts
    posts = list(posts_collection.find())
    
    # Topic Modeling on Posts
    documents = [p.get("title", "") + " " + p.get("content", "") for p in posts]
    
    if len(documents) > 2:
        print("Running topic modeling...")
        lda_model, corpus, dictionary = perform_topic_modeling(documents, num_topics=5)
        
        if lda_model:
            # Get keywords for topics to use as labels
            topics_data = []
            for i in range(5):
                words = [word for word, prob in lda_model.show_topic(i, topn=5)]
                topics_data.append({
                    "topic_id": i,
                    "label": " ".join(words)
                })
            
            # Save topics in the DB
            db["topics"].drop()
            db["topics"].insert_many(topics_data)
            
            for idx, post in enumerate(posts):
                doc_text = documents[idx]
                dominant_topic = get_dominant_topic(lda_model, dictionary, doc_text)
                
                posts_collection.update_one(
                    {"_id": post["_id"]},
                    {"$set": {"topic_id": int(dominant_topic)}}
                )
    
    for post in posts:
        post_id = post["post_id"]
        post_comments = list(comments_collection.find({"post_id": post_id}))
        comment_texts = [c.get("text", "") for c in post_comments]
        
        if len(comment_texts) > 2:
            # Summarization
            print(f"Summarizing post ID {post_id}")
            summary = summarize_text(" ".join(comment_texts), num_sentences=3)
            
            # Sentiment aggregation
            sentiments = [c.get("sentiment_label", "neutral") for c in post_comments]
            sentiment_counts = dict(Counter(sentiments))
            
            posts_collection.update_one(
                {"_id": post["_id"]},
                {"$set": {
                    "summary": summary,
                    "sentiment_distribution": sentiment_counts
                }}
            )
            
            # Clustering
            print(f"Clustering comments for post ID {post_id}")
            cluster_ids = cluster_comments(comment_texts)
            for c_idx, comment in enumerate(post_comments):
                comments_collection.update_one(
                    {"_id": comment["_id"]},
                    {"$set": {"cluster_id": cluster_ids[c_idx]}}
                )
                
    # Detect trends
    print("Detecting trends...")
    topic_times = []
    for post in posts:
        if "topic_id" in post:
            topic_times.append((post["topic_id"], post.get("timestamp") or post.get("created_utc")))

    if topic_times:
        freqs = Counter([t[0] for t in topic_times])
        trending_topics = freqs.most_common(3)
        trends_info = []
        for t_id, cnt in trending_topics:
            topic_label = next((t["label"] for t in db["topics"].find({"topic_id": t_id})), f"Topic {t_id}")
            
            # Origin detection
            origin_post = posts_collection.find_one({"topic_id": t_id}, sort=[("created_utc", 1)])
            
            trends_info.append({
                "topic_id": t_id,
                "label": topic_label,
                "frequency": cnt,
                "origin_post_id": origin_post["post_id"] if origin_post else None,
                "origin_timestamp": origin_post["created_utc"] if origin_post else None
            })
            
        db["trends"].drop()
        db["trends"].insert_many(trends_info)

    print("Pipeline execution finished.")

if __name__ == "__main__":
    process_nlp_pipeline()
