import os
import sys
import kagglehub
import pandas as pd
from datetime import datetime
import numpy as np

# Ensure backend root is in Python path for importing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.mongo_client import posts_collection, comments_collection, db

def import_kaggle_data():
    print("Clearing existing database collections...")
    posts_collection.delete_many({})
    comments_collection.delete_many({})
    db["topics"].drop()
    db["trends"].drop()

    print("Downloading/Locating Kaggle Reddit dataset...")
    path = kagglehub.dataset_download("pavellexyr/the-reddit-dataset-dataset")
    
    posts_path = os.path.join(path, "the-reddit-dataset-dataset-posts.csv")
    comments_path = os.path.join(path, "the-reddit-dataset-dataset-comments.csv")

    print("Loading CSVs into memory...")
    posts_df = pd.read_csv(posts_path)
    comments_df = pd.read_csv(comments_path)

    print("Processing data...")
    # Clean up nan
    posts_df = posts_df.replace({np.nan: None})
    comments_df = comments_df.replace({np.nan: None})

    # Filter out removed/deleted posts
    valid_posts = posts_df[
        (~posts_df['title'].astype(str).str.contains(r'\[removed\]|\[deleted\]', case=False, na=False)) &
        (~posts_df['selftext'].astype(str).str.contains(r'\[removed\]|\[deleted\]', case=False, na=False))
    ]

    # Extract post_id from comment permalink. 
    # Example format: https://old.reddit.com/r/datasets/comments/t45uk7/request_looking_for_a/...
    def extract_post_id(url):
        try:
            parts = str(url).split('/')
            return parts[6] if len(parts) > 6 else None
        except:
            return None

    comments_df['post_id'] = comments_df['permalink'].apply(extract_post_id)
    
    # We want posts that have a good number of comments
    comment_counts = comments_df.groupby('post_id').size().reset_index(name='count')
    
    # Merge posts with their comment counts
    posts_with_counts = valid_posts.merge(comment_counts, left_on='id', right_on='post_id', how='inner')
    
    # Sort by comment count to get rich discussions, take top 50
    top_posts = posts_with_counts.sort_values(by='count', ascending=False).head(50)
    
    if len(top_posts) == 0:
        print("Warning: Could not find any posts with matching comments in this subset.")
        # Fallback: Just take 50 random valid posts and their comments if any
        top_posts = valid_posts.dropna(subset=['title']).head(50)

    print(f"Selecting {len(top_posts)} posts to import...")

    post_docs = []
    comment_docs = []

    for _, row in top_posts.iterrows():
        p_id = str(row['id'])
        created_utc = float(row['created_utc']) if pd.notnull(row['created_utc']) else 0
        
        post_docs.append({
            "post_id": p_id,
            "title": str(row['title']) if pd.notnull(row['title']) else "",
            "content": str(row['selftext']) if pd.notnull(row['selftext']) else "",
            "subreddit": str(row.get('subreddit.name', 'unknown')),
            "score": int(row.get('score', 0)),
            "number_of_comments": int(row.get('count', 0)),
            "timestamp": datetime.fromtimestamp(created_utc) if created_utc else datetime.utcnow(),
            "created_utc": created_utc
        })
        
        # Get matching comments
        matched_comments = comments_df[comments_df['post_id'] == p_id]
        for _, c_row in matched_comments.iterrows():
            c_created = float(c_row['created_utc']) if pd.notnull(c_row['created_utc']) else 0
            comment_docs.append({
                "comment_id": str(c_row['id']),
                "post_id": p_id,
                "text": str(c_row['body']) if pd.notnull(c_row['body']) else "",
                "author": "anonymous_user", # Kaggle dataset doesn't seem to have author
                "score": int(c_row.get('score', 0)),
                "timestamp": datetime.fromtimestamp(c_created) if c_created else datetime.utcnow(),
                "created_utc": c_created
            })

    # Insert into MongoDB
    if post_docs:
        posts_collection.insert_many(post_docs)
    if comment_docs:
        comments_collection.insert_many(comment_docs)
        
    print(f"Successfully imported {len(post_docs)} posts and {len(comment_docs)} comments into MongoDB!")
    print("Run `python process_data.py` to analyze the newly imported dataset.")

if __name__ == "__main__":
    import_kaggle_data()
