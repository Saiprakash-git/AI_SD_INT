import os
import sys
import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from duckduckgo_search import DDGS
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.mongo_client import posts_collection
from nlp.sentiment import analyze_sentiment
from nlp.toxicity import detect_toxicity

def run_link_analysis(url):
    ret = {
        "url": url,
        "content_summary": None,
        "sentiment": None,
        "is_toxic": False,
        "internal_matches": [],
        "external_web": [],
        "confidence_score": 0
    }
    
    # 1. Fetch & Parse URL Content
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')
        title = soup.title.string if soup.title else "Unknown Title"
        # Gather paragraphs
        paragraphs = soup.find_all('p')
        text_content = " ".join([p.get_text() for p in paragraphs[:15]]) # First 15 paragraphs
        
        if not text_content.strip():
            text_content = title
            
        ret['content_summary'] = {"title": title, "preview": text_content[:300] + "..."}
        
        # Sentiment & Toxicity
        scores, label = analyze_sentiment(text_content)
        tox_score, is_toxic = detect_toxicity(text_content)
        ret['sentiment'] = scores
        ret['is_toxic'] = is_toxic
        
        # 2. Match Internally using TF-IDF Semantic similarity
        import pymongo
        recent_posts = list(posts_collection.find().sort("timestamp", -1).limit(500))
        if recent_posts:
            docs = [text_content] + [p.get('title', '') + " " + p.get('content', '') for p in recent_posts]
            vectorizer = TfidfVectorizer(stop_words='english', max_features=1000)
            tfidf_matrix = vectorizer.fit_transform(docs)
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            
            # Find closest matches
            top_indices = cosine_sim.argsort()[-5:][::-1]
            for idx in top_indices:
                score = cosine_sim[idx]
                if score > 0.1: # Threshold
                    p = recent_posts[idx]
                    ret['internal_matches'].append({
                        "post_id": p['post_id'],
                        "title": p.get('title'),
                        "subreddit": p.get('subreddit'),
                        "similarity": round(score * 100, 1)
                    })
                    
            if ret['internal_matches']:
                ret['confidence_score'] = ret['internal_matches'][0]['similarity']
                
        # 3. External Web Related Content
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(title, max_results=5))
                ret['external_web'] = results
        except Exception as e:
            pass
            
    except Exception as e:
        print("Link Analyzer Error:", e)
        ret['error'] = str(e)
        
    return ret
