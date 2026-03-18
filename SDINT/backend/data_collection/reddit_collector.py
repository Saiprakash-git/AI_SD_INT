import os
import sys

# Ensure backend root is in Python path for importing
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import praw
import time
from datetime import datetime
from dotenv import load_dotenv
from db.mongo_client import posts_collection, comments_collection
load_dotenv()

# Initialize PRAW Reddit client
reddit = praw.Reddit(
    client_id=os.getenv("REDDIT_CLIENT_ID", "YOUR_CLIENT_ID"),
    client_secret=os.getenv("REDDIT_CLIENT_SECRET", "YOUR_CLIENT_SECRET"),
    user_agent=os.getenv("REDDIT_USER_AGENT", "SocialDiscussionAnalyzer/1.0")
)

def fetch_reddit_data(subreddits=['technology', 'worldnews', 'ArtificialIntelligence', 'sports', 'movies'], limit=10):
    for sub in subreddits:
        print(f"Fetching data from subreddit: r/{sub}")
        try:
            subreddit = reddit.subreddit(sub)
            for post in subreddit.hot(limit=limit):
                # Data dictionary for the post
                post_data = {
                    "post_id": post.id,
                    "title": post.title,
                    "content": post.selftext,
                    "subreddit": sub,
                    "score": post.score,
                    "number_of_comments": post.num_comments,
                    "timestamp": datetime.fromtimestamp(post.created_utc),
                    "created_utc": post.created_utc,
                }
                
                # Upsert post to MongoDB
                posts_collection.update_one(
                    {"post_id": post.id},
                    {"$set": post_data},
                    upsert=True
                )
                
                # Fetch comments related to the post
                post.comments.replace_more(limit=0) # Flatten comment forest
                for comment in post.comments.list():
                    comment_data = {
                        "comment_id": comment.id,
                        "post_id": post.id,
                        "text": comment.body,
                        "author": str(comment.author) if comment.author else "[deleted]",
                        "score": comment.score,
                        "timestamp": datetime.fromtimestamp(comment.created_utc),
                        "created_utc": comment.created_utc,
                    }
                    
                    # Upsert comment to MongoDB
                    comments_collection.update_one(
                        {"comment_id": comment.id},
                        {"$set": comment_data},
                        upsert=True
                    )
            print(f"Completed fetching for r/{sub}")
        except Exception as e:
            print(f"Error fetching from r/{sub}: {e}")

if __name__ == "__main__":
    fetch_reddit_data()
