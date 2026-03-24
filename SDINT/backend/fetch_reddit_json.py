import requests
import time
from datetime import datetime
import os
import sys

# Ensure backend root is in Python path for importing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.mongo_client import posts_collection, comments_collection

def fetch_json_data():
    subreddits = ['technology', 'ArtificialIntelligence', 'dataisbeautiful', 'movies']
    # Disguise requests as a normal web browser to prevent 429 Too Many Requests status
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
    
    print("Fetching direct JSON from Reddit without API credentials...")
    new_posts = 0
    new_comments = 0
    
    for sub in subreddits:
        print(f"Fetching /r/{sub}...")
        try:
            res = requests.get(f"https://www.reddit.com/r/{sub}/hot.json?limit=10", headers=headers)
            if res.status_code != 200:
                print(f"Failed to fetch {sub}: HTTP {res.status_code}")
                time.sleep(3)
                continue
            
            data = res.json()
            for child in data.get('data', {}).get('children', []):
                post = child.get('data', {})
                post_id = post.get('id')
                
                if not post_id or post.get('stickied', False): 
                    continue
                
                # Insert post
                posts_collection.update_one(
                    {"post_id": post_id},
                    {"$set": {
                        "post_id": post_id,
                        "title": post.get('title', ''),
                        "content": post.get('selftext', ''),
                        "subreddit": sub,
                        "score": post.get('score', 0),
                        "number_of_comments": post.get('num_comments', 0),
                        "timestamp": datetime.fromtimestamp(post.get('created_utc', time.time())),
                        "created_utc": post.get('created_utc', time.time())
                    }},
                    upsert=True
                )
                new_posts += 1
                
                # Wait before fetching comments to respect rate limits
                time.sleep(1.5)
                c_res = requests.get(f"https://www.reddit.com/r/{sub}/comments/{post_id}.json?limit=20", headers=headers)
                if c_res.status_code == 200:
                    c_data = c_res.json()
                    if len(c_data) > 1:
                        comments = c_data[1].get('data', {}).get('children', [])
                        for c in comments:
                            if c.get('kind') == 't1': # comment type
                                c_info = c.get('data', {})
                                comments_collection.update_one(
                                    {"comment_id": c_info.get('id')},
                                    {"$set": {
                                        "comment_id": c_info.get('id'),
                                        "post_id": post_id,
                                        "text": c_info.get('body', ''),
                                        "author": c_info.get('author', '[deleted]'),
                                        "score": c_info.get('score', 0),
                                        "timestamp": datetime.fromtimestamp(c_info.get('created_utc', time.time())),
                                        "created_utc": c_info.get('created_utc', time.time())
                                    }},
                                    upsert=True
                                )
                                new_comments += 1
        except Exception as e:
            print(f"Error fetching JSON for {sub}: {e}")
            
        time.sleep(3) # Wait before next subreddit
        
    print(f"Finished direct JSON scraping! Saved {new_posts} posts and {new_comments} comments to MongoDB.")

if __name__ == "__main__":
    fetch_json_data()
