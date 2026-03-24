import os
import sys
import requests
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from db.mongo_client import posts_collection, comments_collection, db
from analysis.echo_chamber import compute_echo_chamber_score

def fetch_rss_live_data():
    subreddits = ['technology', 'worldnews', 'programming', 'MachineLearning', 'science', 'AskReddit']
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) SDINT/3.0"}
    
    posts_added = 0
    new_post_ids = []
    
    for sub in subreddits:
        try:
            res = requests.get(f"https://www.reddit.com/r/{sub}/new.json?limit=25", headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                for child in data.get('data', {}).get('children', []):
                    post = child['data']
                    pid = str(post['id'])
                    
                    if not posts_collection.find_one({"post_id": pid}):
                        doc = {
                            "post_id": pid,
                            "title": post.get('title', ''),
                            "content": post.get('selftext', ''),
                            "subreddit": sub,
                            "score": post.get('score', 0),
                            "number_of_comments": post.get('num_comments', 0),
                            "timestamp": datetime.fromtimestamp(post.get('created_utc', time.time())),
                            "created_utc": post.get('created_utc', time.time()),
                            "url": post.get('url', ''),
                            "fetched_at": datetime.utcnow()
                        }
                        posts_collection.insert_one(doc)
                        posts_added += 1
                        new_post_ids.append(pid)
                        
                        try:
                            time.sleep(1)
                            c_res = requests.get(f"https://www.reddit.com/r/{sub}/comments/{pid}.json?limit=10", headers=headers, timeout=10)
                            if c_res.status_code == 200:
                                c_data = c_res.json()
                                if len(c_data) > 1:
                                    for c in c_data[1].get('data', {}).get('children', []):
                                        if c['kind'] == 't1':
                                            c_info = c['data']
                                            c_id = str(c_info['id'])
                                            if not comments_collection.find_one({"comment_id": c_id}):
                                                comments_collection.insert_one({
                                                    "comment_id": c_id,
                                                    "post_id": pid,
                                                    "text": c_info.get('body', ''),
                                                    "author": c_info.get('author', ''),
                                                    "score": c_info.get('score', 0),
                                                    "timestamp": datetime.fromtimestamp(c_info.get('created_utc', time.time())),
                                                    "created_utc": c_info.get('created_utc', time.time())
                                                })
                        except Exception as ce:
                            pass
        except Exception as e:
            pass
            
        total_posts = posts_collection.count_documents({"subreddit": sub})
        db["rss_status"].update_one(
            {"subreddit": sub},
            {"$set": {
                "subreddit": sub,
                "last_poll_time": datetime.utcnow().isoformat(),
                "posts_added_this_cycle": posts_added,
                "total_posts_in_db": total_posts
            }}, upsert=True
        )
        time.sleep(1)
        
    print(f"[{datetime.utcnow()}] RSS Collector finished. New posts added: {posts_added}")
    
    if posts_added > 0:
        import subprocess
        # Trigger offline processing only on missing sentiment or topics
        # process_data.py natively processes unprocessed.
        subprocess.Popen([sys.executable, "process_data.py"], cwd=os.path.dirname(os.path.abspath(__file__)))

def compute_all_echo_chambers():
    subreddits = ['technology', 'worldnews', 'programming', 'MachineLearning', 'science', 'AskReddit']
    for sub in subreddits:
        compute_echo_chamber_score(sub)

if __name__ == "__main__":
    fetch_rss_live_data()
