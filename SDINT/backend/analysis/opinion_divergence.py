import sys
import os
import math
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo_client import comments_collection, posts_collection

def compute_opinion_divergence(post_id):
    comments = list(comments_collection.find({"post_id": post_id, "cluster_id": {"$exists": True}}))
    if not comments:
        return None
        
    clusters_map = {}
    for c in comments:
        cid = c.get("cluster_id", 0)
        if cid not in clusters_map:
            clusters_map[cid] = []
        clusters_map[cid].append(c)
        
    clusters_data = []
    
    for cid, c_list in clusters_map.items():
        if len(c_list) == 0: continue
            
        vader_sum = sum(float(c.get("sentiment", {}).get("compound", 0.0)) for c in c_list)
        avg_sent = vader_sum / len(c_list)
        
        toxic_count = sum(1 for c in c_list if c.get("is_toxic", False))
        tox_ratio = toxic_count / len(c_list)
        
        texts = [c.get("text", "") for c in c_list if c.get("text", "").strip() != ""]
        top_keywords = []
        if len(texts) > 0:
            try:
                vec = TfidfVectorizer(stop_words='english', max_features=8)
                X = vec.fit_transform(texts)
                
                # Sum tfidf over all docs
                sum_tfidf = X.sum(axis=0)
                words = vec.get_feature_names_out()
                
                word_scores = [(word, sum_tfidf[0, idx]) for idx, word in enumerate(words)]
                sorted_words = sorted(word_scores, key=lambda x: x[1], reverse=True)
                top_keywords = [w[0] for w in sorted_words][:8]
            except Exception as e:
                pass
                
        if len(top_keywords) >= 3:
            viewpoint = " ".join(top_keywords[:3])
        elif len(top_keywords) > 0:
            viewpoint = " ".join(top_keywords)
        else:
            viewpoint = "General Discussion"
            
        if avg_sent > 0.05: lbl = "positive"
        elif avg_sent < -0.05: lbl = "negative"
        else: lbl = "neutral"
            
        clusters_data.append({
            "cluster_id": cid,
            "comment_count": len(c_list),
            "avg_sentiment": round(avg_sent, 3),
            "sentiment_label": lbl,
            "top_keywords": top_keywords,
            "viewpoint_label": viewpoint,
            "toxicity_ratio": round(tox_ratio, 3)
        })
        
    pairwise = []
    most_app_pair = []
    highest_score = -1.0
    overall_sum = 0.0
    
    n_clusters = len(clusters_data)
    for i in range(n_clusters):
        for j in range(i+1, n_clusters):
            ca = clusters_data[i]
            cb = clusters_data[j]
            
            sa = set(ca["top_keywords"])
            sb = set(cb["top_keywords"])
            shared = sa.intersection(sb)
            keyword_overlap_ratio = len(shared) / 8.0
            
            div_score = abs(ca["avg_sentiment"] - cb["avg_sentiment"]) + (1.0 - keyword_overlap_ratio)
            overall_sum += div_score
            
            pairwise.append({
                "cluster_a": ca["cluster_id"],
                "cluster_b": cb["cluster_id"],
                "score": round(div_score, 3)
            })
            
            if div_score > highest_score:
                highest_score = div_score
                most_app_pair = [ca["cluster_id"], cb["cluster_id"]]
                
    overall = overall_sum / len(pairwise) if pairwise else 0.0
    
    res = {
        "post_id": post_id,
        "cluster_count": n_clusters,
        "clusters": clusters_data,
        "pairwise_divergence": pairwise,
        "most_opposed_pair": most_app_pair,
        "overall_divergence": round(overall, 3)
    }
    
    posts_collection.update_one({"post_id": post_id}, {"$set": {"opinion_divergence": res}})
    return res
