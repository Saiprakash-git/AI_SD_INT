"""
Reddit Converter — Batch converts existing Reddit data into evidence items.

Reads from the existing MongoDB collections (posts, comments) and converts
each document into a normalized EvidenceItem using the EvidenceBuilder.

Features:
  - Batch conversion with progress tracking
  - Skip-if-exists logic (idempotent — safe to re-run)
  - User profile extraction from comment authors
  - Statistics reporting

This is the bridge between the existing social analytics system and the
new OSINT intelligence pipeline.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

import sys
import os

backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
project_root = os.path.dirname(backend_root)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.db.mongo_client import posts_collection, comments_collection, db

from osint.services.evidence_builder import EvidenceBuilder
from osint.db.evidence_store import EvidenceStore

logger = logging.getLogger(__name__)


class RedditConverter:
    """
    Converts existing Reddit data from MongoDB into evidence items.
    
    Usage:
        converter = RedditConverter()
        stats = converter.convert_all()
        print(stats)
        # {'posts_converted': 150, 'comments_converted': 1200, 'users_extracted': 85, ...}
    """

    def __init__(self, investigation_id: Optional[str] = None):
        """
        Args:
            investigation_id: Optional investigation ID to tag all converted items with
        """
        self.investigation_id = investigation_id
        self.store = EvidenceStore()
        self._stats = {
            "posts_converted": 0,
            "posts_skipped": 0,
            "comments_converted": 0,
            "comments_skipped": 0,
            "users_extracted": 0,
            "users_skipped": 0,
            "errors": 0,
            "total_entities_extracted": 0,
        }

    def convert_all(self, limit: Optional[int] = None) -> Dict[str, int]:
        """
        Convert all existing Reddit data into evidence items.
        
        Args:
            limit: Max number of posts/comments to convert (None = all)
            
        Returns:
            Statistics dict with conversion counts
        """
        logger.info("Starting Reddit → Evidence conversion pipeline...")

        self._convert_posts(limit)
        self._convert_comments(limit)
        self._extract_unique_users(limit)

        logger.info(f"Conversion complete. Stats: {self._stats}")
        return self._stats

    def convert_posts(self, limit: Optional[int] = None) -> Dict[str, int]:
        """Convert only posts. Returns stats."""
        self._convert_posts(limit)
        return self._stats

    def convert_comments(self, limit: Optional[int] = None) -> Dict[str, int]:
        """Convert only comments. Returns stats."""
        self._convert_comments(limit)
        return self._stats

    def _convert_posts(self, limit: Optional[int] = None):
        """Batch convert Reddit posts to evidence items."""
        query = {}
        cursor = posts_collection.find(query)
        if limit:
            cursor = cursor.limit(limit)

        posts = list(cursor)
        total = len(posts)
        logger.info(f"Converting {total} Reddit posts to evidence items...")

        for i, post in enumerate(posts):
            try:
                post_id = post.get("post_id", "")

                # Skip if already converted (idempotent)
                if self.store.exists_by_source("reddit_post", post_id):
                    self._stats["posts_skipped"] += 1
                    continue

                item = EvidenceBuilder.from_reddit_post(post, self.investigation_id)
                self.store.insert(item)

                self._stats["posts_converted"] += 1
                self._stats["total_entities_extracted"] += len(item.entities)

                if (i + 1) % 50 == 0:
                    logger.info(f"  Posts: {i + 1}/{total} processed")

            except Exception as e:
                self._stats["errors"] += 1
                logger.error(f"Error converting post {post.get('post_id', '?')}: {e}")

    def _convert_comments(self, limit: Optional[int] = None):
        """Batch convert Reddit comments to evidence items."""
        query = {}
        cursor = comments_collection.find(query)
        if limit:
            cursor = cursor.limit(limit)

        comments = list(cursor)
        total = len(comments)
        logger.info(f"Converting {total} Reddit comments to evidence items...")

        for i, comment in enumerate(comments):
            try:
                comment_id = comment.get("comment_id", "")

                # Skip if already converted
                if self.store.exists_by_source("reddit_comment", comment_id):
                    self._stats["comments_skipped"] += 1
                    continue

                item = EvidenceBuilder.from_reddit_comment(comment, self.investigation_id)
                self.store.insert(item)

                self._stats["comments_converted"] += 1
                self._stats["total_entities_extracted"] += len(item.entities)

                if (i + 1) % 100 == 0:
                    logger.info(f"  Comments: {i + 1}/{total} processed")

            except Exception as e:
                self._stats["errors"] += 1
                logger.error(f"Error converting comment {comment.get('comment_id', '?')}: {e}")

    def _extract_unique_users(self, limit: Optional[int] = None):
        """
        Extract unique Reddit usernames from comments and create user evidence items.
        This creates a basic user profile record for entity resolution in later modules.
        """
        logger.info("Extracting unique Reddit users from comments...")

        # Get distinct authors
        pipeline = [
            {"$match": {"author": {"$nin": [None, "", "[deleted]", "AutoModerator"]}}},
            {"$group": {"_id": "$author", "comment_count": {"$sum": 1}, "total_score": {"$sum": "$score"}}},
            {"$sort": {"comment_count": -1}},
        ]
        if limit:
            pipeline.append({"$limit": limit})

        authors = list(comments_collection.aggregate(pipeline))
        logger.info(f"Found {len(authors)} unique Reddit users to process.")

        for author_doc in authors:
            username = author_doc["_id"]
            try:
                source_id = f"reddit_user_{username}"

                # Skip if already exists
                if self.store.exists_by_source("reddit_user", source_id):
                    self._stats["users_skipped"] += 1
                    continue

                # Build a minimal user profile from available data
                user_data = {
                    "comment_count_in_db": author_doc["comment_count"],
                    "total_comment_score": author_doc["total_score"],
                    "subreddit": {"public_description": ""},
                }

                item = EvidenceBuilder.from_reddit_user(username, user_data, self.investigation_id)

                # Add derived metadata
                item.metadata["comment_count_in_db"] = author_doc["comment_count"]
                item.metadata["total_comment_score"] = author_doc["total_score"]

                self.store.insert(item)
                self._stats["users_extracted"] += 1
                self._stats["total_entities_extracted"] += len(item.entities)

            except Exception as e:
                self._stats["errors"] += 1
                logger.error(f"Error creating user evidence for {username}: {e}")

    def get_stats(self) -> Dict[str, int]:
        """Return current conversion statistics."""
        return self._stats.copy()
