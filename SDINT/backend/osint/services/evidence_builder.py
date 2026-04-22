"""
Evidence Builder — Factory service for creating validated evidence items.

Provides clean factory methods for each source type:
  - from_reddit_post()     → Convert a Reddit post document
  - from_reddit_comment()  → Convert a Reddit comment document
  - from_reddit_user()     → Convert Reddit user profile data
  - from_raw()             → Generic builder for any source (used by future connectors)

All methods automatically:
  1. Generate a unique evidence_id
  2. Run entity extraction on text content
  3. Set timestamps
  4. Validate the final item
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from osint.schemas.evidence_schema import (
    EvidenceItem,
    EvidenceContent,
    EvidenceTimestamps,
    EntityRecord,
    SourceType,
    EvidenceStatus,
    generate_evidence_id,
    validate_evidence_item,
)
from osint.extractors.entity_extractor import EntityExtractor

logger = logging.getLogger(__name__)

# Shared extractor instance
_extractor = EntityExtractor()


class EvidenceBuilder:
    """
    Factory for producing validated EvidenceItem objects.
    
    Usage:
        item = EvidenceBuilder.from_reddit_post(post_doc)
        item = EvidenceBuilder.from_raw(
            source_type="web_search",
            source_id="result_123",
            source_platform="duckduckgo",
            title="Search Result",
            body="...",
            url="https://...",
            metadata={"query": "john doe"}
        )
    """

    @staticmethod
    def from_reddit_post(post: Dict[str, Any], investigation_id: Optional[str] = None) -> EvidenceItem:
        """
        Convert a MongoDB Reddit post document into an EvidenceItem.
        
        Args:
            post: Post document from the 'posts' collection
            investigation_id: Optional investigation to link to
            
        Returns:
            Validated EvidenceItem
        """
        post_id = post.get("post_id", "")
        title = post.get("title", "")
        content = post.get("content", "")
        url = post.get("url", "")
        subreddit = post.get("subreddit", "")

        # Build combined text for entity extraction
        combined_text = f"{title} {content}".strip()

        # Extract entities from the combined text
        raw_entities = _extractor.extract(combined_text)
        entities = [EntityRecord.from_dict(e) for e in raw_entities]

        # Add the subreddit as a known entity
        if subreddit:
            entities.append(EntityRecord(
                type="subreddit",
                value=subreddit,
                confidence=1.0,
                source="structural",
                context=f"Posted in r/{subreddit}"
            ))

        # Build source-specific metadata
        metadata = {
            "subreddit": subreddit,
            "score": post.get("score", 0),
            "num_comments": post.get("number_of_comments", 0),
            "topic_id": post.get("topic_id"),
            "sentiment_distribution": post.get("sentiment_distribution"),
            "summary": post.get("summary"),
            "image_metadata": post.get("image_metadata"),
        }
        # Remove None values for cleaner storage
        metadata = {k: v for k, v in metadata.items() if v is not None}

        # Handle timestamp conversion
        source_created = None
        created_utc = post.get("created_utc")
        if created_utc:
            if isinstance(created_utc, (int, float)):
                source_created = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()
            elif isinstance(created_utc, str):
                source_created = created_utc

        now_iso = datetime.now(timezone.utc).isoformat()

        # Build tags
        tags = ["reddit", f"r/{subreddit}"] if subreddit else ["reddit"]
        if post.get("image_metadata"):
            tags.append("has_image")

        item = EvidenceItem(
            evidence_id=generate_evidence_id(),
            source_type=SourceType.REDDIT_POST.value,
            source_id=post_id,
            source_platform="reddit",
            content=EvidenceContent(
                title=title,
                body=content,
                url=url,
            ),
            entities=entities,
            metadata=metadata,
            timestamps=EvidenceTimestamps(
                source_created=source_created,
                collected_at=now_iso,
                processed_at=now_iso,
            ),
            confidence=0.85,  # Reddit posts are generally reliable source data
            tags=tags,
            investigation_id=investigation_id,
            status=EvidenceStatus.PROCESSED.value,
        )

        # Validate
        is_valid, errors = validate_evidence_item(item)
        if not is_valid:
            logger.warning(f"Validation issues for post {post_id}: {errors}")

        return item

    @staticmethod
    def from_reddit_comment(comment: Dict[str, Any], investigation_id: Optional[str] = None) -> EvidenceItem:
        """
        Convert a MongoDB Reddit comment document into an EvidenceItem.
        
        Args:
            comment: Comment document from the 'comments' collection
            investigation_id: Optional investigation to link to
            
        Returns:
            Validated EvidenceItem
        """
        comment_id = comment.get("comment_id", "")
        text = comment.get("text", "")
        author = comment.get("author", "")
        post_id = comment.get("post_id", "")

        # Extract entities from comment text
        raw_entities = _extractor.extract(text)
        entities = [EntityRecord.from_dict(e) for e in raw_entities]

        # Add the author as a known username entity
        if author and author not in ("[deleted]", "AutoModerator"):
            entities.append(EntityRecord(
                type="username",
                value=author,
                confidence=1.0,
                source="structural",
                context=f"Comment author: u/{author}"
            ))

        # Build metadata
        metadata = {
            "post_id": post_id,
            "author": author,
            "score": comment.get("score", 0),
            "sentiment_label": comment.get("sentiment_label"),
            "sentiment": comment.get("sentiment"),
            "toxicity_score": comment.get("toxicity_score"),
            "is_toxic": comment.get("is_toxic"),
            "cluster_id": comment.get("cluster_id"),
        }
        metadata = {k: v for k, v in metadata.items() if v is not None}

        # Timestamp
        source_created = None
        created_utc = comment.get("created_utc")
        if created_utc:
            if isinstance(created_utc, (int, float)):
                source_created = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()
            elif isinstance(created_utc, str):
                source_created = created_utc

        now_iso = datetime.now(timezone.utc).isoformat()

        # Tags
        tags = ["reddit", "comment"]
        if comment.get("is_toxic"):
            tags.append("toxic")

        item = EvidenceItem(
            evidence_id=generate_evidence_id(),
            source_type=SourceType.REDDIT_COMMENT.value,
            source_id=comment_id,
            source_platform="reddit",
            content=EvidenceContent(
                title=f"Comment by u/{author}" if author else "Reddit Comment",
                body=text,
                url="",
            ),
            entities=entities,
            metadata=metadata,
            timestamps=EvidenceTimestamps(
                source_created=source_created,
                collected_at=now_iso,
                processed_at=now_iso,
            ),
            confidence=0.80,  # Comments slightly less reliable than posts
            tags=tags,
            investigation_id=investigation_id,
            status=EvidenceStatus.PROCESSED.value,
        )

        is_valid, errors = validate_evidence_item(item)
        if not is_valid:
            logger.warning(f"Validation issues for comment {comment_id}: {errors}")

        return item

    @staticmethod
    def from_reddit_user(username: str, user_data: Dict[str, Any],
                         investigation_id: Optional[str] = None) -> EvidenceItem:
        """
        Create an EvidenceItem from Reddit user profile data.
        
        Args:
            username: Reddit username
            user_data: Dict with user profile fields (karma, created, etc.)
            investigation_id: Optional investigation to link to
            
        Returns:
            Validated EvidenceItem
        """
        entities = [
            EntityRecord(
                type="username",
                value=username,
                confidence=1.0,
                source="structural",
                context=f"Reddit user profile: u/{username}"
            )
        ]

        # Extract any additional entities from user bio/description
        bio = user_data.get("subreddit", {}).get("public_description", "")
        if bio:
            raw_entities = _extractor.extract(bio)
            entities.extend([EntityRecord.from_dict(e) for e in raw_entities])

        now_iso = datetime.now(timezone.utc).isoformat()

        # Account creation timestamp
        source_created = None
        created_utc = user_data.get("created_utc")
        if created_utc and isinstance(created_utc, (int, float)):
            source_created = datetime.fromtimestamp(created_utc, tz=timezone.utc).isoformat()

        metadata = {
            "comment_karma": user_data.get("comment_karma", 0),
            "link_karma": user_data.get("link_karma", 0),
            "is_gold": user_data.get("is_gold", False),
            "is_mod": user_data.get("is_mod", False),
            "has_verified_email": user_data.get("has_verified_email", False),
            "account_age_days": None,
        }

        if created_utc and isinstance(created_utc, (int, float)):
            age_seconds = datetime.now(timezone.utc).timestamp() - created_utc
            metadata["account_age_days"] = int(age_seconds / 86400)

        metadata = {k: v for k, v in metadata.items() if v is not None}

        item = EvidenceItem(
            evidence_id=generate_evidence_id(),
            source_type=SourceType.REDDIT_USER.value,
            source_id=f"reddit_user_{username}",
            source_platform="reddit",
            content=EvidenceContent(
                title=f"Reddit User: u/{username}",
                body=bio,
                url=f"https://www.reddit.com/user/{username}",
            ),
            entities=entities,
            metadata=metadata,
            timestamps=EvidenceTimestamps(
                source_created=source_created,
                collected_at=now_iso,
                processed_at=now_iso,
            ),
            confidence=0.90,
            tags=["reddit", "user_profile"],
            investigation_id=investigation_id,
            status=EvidenceStatus.PROCESSED.value,
        )

        is_valid, errors = validate_evidence_item(item)
        if not is_valid:
            logger.warning(f"Validation issues for user {username}: {errors}")

        return item

    @staticmethod
    def from_raw(
        source_type: str,
        source_id: str,
        source_platform: str,
        title: str = "",
        body: str = "",
        url: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        confidence: float = 0.5,
        tags: Optional[List[str]] = None,
        investigation_id: Optional[str] = None,
        source_created: Optional[str] = None,
        extract_entities: bool = True,
    ) -> EvidenceItem:
        """
        Generic evidence builder for any source type.
        Used by future connectors (DuckDuckGo, Sherlock, HIBP, etc.)
        
        Args:
            source_type: SourceType enum value
            source_id: Unique ID from the source system
            source_platform: Platform name
            title: Content title
            body: Content body text
            url: Associated URL
            metadata: Source-specific metadata dict
            confidence: Reliability score (0.0-1.0)
            tags: Classification tags
            investigation_id: Optional investigation to link to
            source_created: ISO timestamp when content was created
            extract_entities: Whether to run entity extraction
            
        Returns:
            Validated EvidenceItem
        """
        # Extract entities if requested
        combined_text = f"{title} {body}".strip()
        entities = []
        
        if extract_entities and combined_text:
            raw_entities = _extractor.extract(combined_text)
            entities = [EntityRecord.from_dict(e) for e in raw_entities]
        
        # Ensure metadata is a dict
        if metadata is None:
            metadata = {}
        else:
            metadata = dict(metadata)
        
        # Ensure tags is a list
        if tags is None:
            tags = [source_platform]
        else:
            tags = list(tags)
            if source_platform not in tags:
                tags.insert(0, source_platform)
        
        now_iso = datetime.now(timezone.utc).isoformat()
        
        item = EvidenceItem(
            evidence_id=generate_evidence_id(),
            source_type=source_type,
            source_id=source_id,
            source_platform=source_platform,
            content=EvidenceContent(
                title=title,
                body=body,
                url=url,
            ),
            entities=entities,
            metadata=metadata,
            timestamps=EvidenceTimestamps(
                source_created=source_created,
                collected_at=now_iso,
                processed_at=now_iso,
            ),
            confidence=float(max(0.0, min(1.0, confidence))),
            tags=tags,
            investigation_id=investigation_id,
            status=EvidenceStatus.PROCESSED.value,
        )
        
        is_valid, errors = validate_evidence_item(item)
        if not is_valid:
            logger.warning(f"Validation issues for {source_platform}:{source_id}: {errors}")
        
        return item
