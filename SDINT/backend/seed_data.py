import os
import sys
import random
from datetime import datetime, timedelta

# Ensure backend root is in Python path for importing
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.mongo_client import posts_collection, comments_collection, db

# Dummy data generator
def seed_dummy_data():
    print("Clearing existing data...")
    posts_collection.delete_many({})
    comments_collection.delete_many({})
    db["topics"].drop()
    db["trends"].drop()

    print("Generating simulated Reddit data...")
    
    # 1. Define typical subreddits and some topics
    subreddits = ['technology', 'worldnews', 'ArtificialIntelligence', 'sports', 'movies']
    
    # Let's create some fake posts representing trending concepts
    templates = [
        {
            "sub": "ArtificialIntelligence",
            "title": "OpenAI just announced GPT-5 and it's insane",
            "content": "The new model is completely multimodal, running across video, text, and robotics flawlessly. Does anyone know if they are updating the API anytime soon?",
            "comments": [
                {"text": "This is totally going to change everything. So excited!", "author": "tech_fan", "toxic": False, "sentiment": "pos"},
                {"text": "I think it's just hype. They always say it's insane and then it's just a small upgrade.", "author": "skeptic99", "toxic": False, "sentiment": "neg"},
                {"text": "You are a complete idiot if you believe this PR garbage. Shut up.", "author": "angry_troll", "toxic": True, "sentiment": "neg"},
                {"text": "Does anyone have the link to the actual paper?", "author": "researcher_x", "toxic": False, "sentiment": "neu"},
                {"text": "Wow, the implications for automation are staggering.", "author": "future_thinker", "toxic": False, "sentiment": "pos"},
            ]
        },
        {
            "sub": "technology",
            "title": "Apple's new Vision Pro 2 might be cheaper",
            "content": "Rumors are saying Apple will drop the price by $1000 for the next generation of their VR headset.",
            "comments": [
                {"text": "Still too expensive. Who would buy that?", "author": "user_123", "toxic": False, "sentiment": "neg"},
                {"text": "If it drops under $2k, I'm definitely getting one.", "author": "apple_fanboy", "toxic": False, "sentiment": "pos"},
                {"text": "VR is a dead gimmick anyway.", "author": "hater_1", "toxic": False, "sentiment": "neg"},
            ]
        },
        {
            "sub": "sports",
            "title": "Incredible comeback in the Champions League final!",
            "content": "I can't believe they managed to score 3 goals in the last 10 minutes. Greatest match of the decade.",
            "comments": [
                {"text": "Unbelievable game! I was screaming at my TV!", "author": "soccer_fan", "toxic": False, "sentiment": "pos"},
                {"text": "The referee was totally biased. They cheated their way to victory you morons.", "author": "sore_loser", "toxic": True, "sentiment": "neg"},
                {"text": "What a historical moment.", "author": "neutral_observer", "toxic": False, "sentiment": "pos"},
                {"text": "I didn't watch it, what was the final score?", "author": "curious_one", "toxic": False, "sentiment": "neu"},
            ]
        },
        {
            "sub": "movies",
            "title": "The new Dune movie is a masterpiece",
            "content": "Denis Villeneuve has outdone himself. The cinematography, the score, the acting. Perfect 10/10.",
            "comments": [
                {"text": "Absolutely breathtaking visuals. I need to see it in IMAX again.", "author": "cinephile", "toxic": False, "sentiment": "pos"},
                {"text": "It was too long and boring. I fell asleep in the theater.", "author": "action_fan", "toxic": False, "sentiment": "neg"},
                {"text": "Hans Zimmer's score was incredible as always.", "author": "music_lover", "toxic": False, "sentiment": "pos"},
                {"text": "Dune is the best sci-fi franchise right now.", "author": "scifi_nerd", "toxic": False, "sentiment": "pos"},
                {"text": "Anyone who likes this trash movie has terrible taste.", "author": "movie_snob", "toxic": True, "sentiment": "neg"}
            ]
        },
        {
            "sub": "technology",
            "title": "Congress proposes new bill to ban TikTok",
            "content": "The new proposed legislation would force ByteDance to sell the app or face a complete ban in the US.",
            "comments": [
                {"text": "Finally! That app is absolute brain rot anyway.", "author": "user_x", "toxic": False, "sentiment": "pos"},
                {"text": "This is ridiculous overreach by the government.", "author": "freedom_fighter", "toxic": False, "sentiment": "neg"},
                {"text": "What does this mean for creators who rely on it for income?", "author": "concerned_citizen", "toxic": False, "sentiment": "neu"},
                {"text": "You are all stupid sheep following whatever the media tells you.", "author": "conspiracy_nut", "toxic": True, "sentiment": "neg"},
                {"text": "They've been saying this for years, nothing will happen.", "author": "pessimist", "toxic": False, "sentiment": "neu"}
            ]
        }
    ]

    base_time = datetime.utcnow()
    
    # Generate data and insert
    for i, t in enumerate(templates):
        # Create Post
        post_id = f"post_{i}_{int(time.time())}"
        post_time = base_time - timedelta(hours=random.randint(1, 48))
        
        post_data = {
            "post_id": post_id,
            "title": t["title"],
            "content": t["content"],
            "subreddit": t["sub"],
            "score": random.randint(100, 5000),
            "number_of_comments": len(t["comments"]),
            "timestamp": post_time,
            "created_utc": post_time.timestamp()
        }
        
        posts_collection.insert_one(post_data)
        
        # Create Comments
        for j, c in enumerate(t["comments"]):
            comment_id = f"comment_{i}_{j}_{int(time.time())}"
            comment_time = post_time + timedelta(minutes=random.randint(5, 300))
            
            comment_data = {
                "comment_id": comment_id,
                "post_id": post_id,
                "text": c["text"],
                "author": c["author"],
                "score": random.randint(-50, 500),
                "timestamp": comment_time,
                "created_utc": comment_time.timestamp()
            }
            
            comments_collection.insert_one(comment_data)

    print("Dummy data successfully inserted into MongoDB!")
    print("Now run `python process_data.py` to analyze this data.")

if __name__ == "__main__":
    import time
    seed_dummy_data()
