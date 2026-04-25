# SOCIAL DISCUSSION IMPLEMENTATION - ECHO CHAMBERS & NARRATIVES

## 📋 TABLE OF CONTENTS
1. [Architecture Overview](#architecture-overview)
2. [Echo Chamber Detection](#echo-chamber-detection)
3. [Narrative Arc Analysis](#narrative-arc-analysis)
4. [Opinion Divergence Measurement](#opinion-divergence-measurement)
5. [Link Analysis](#link-analysis)
6. [Incident Detection](#incident-detection)
7. [Frontend Components](#frontend-components)
8. [Database Schema](#database-schema)

---

## ARCHITECTURE OVERVIEW

**Purpose**: Analyze social discussions to identify information bubbles, narrative trends, and discussion dynamics

**Data Flow**:
```
Reddit/Social Input
    ↓
[Raw Data Collection] (reddit_collector.py)
    ↓
MongoDB Storage
    ↓
[Analysis Pipeline]
├─ Echo Chamber Detection
├─ Narrative Arc Analysis
├─ Opinion Divergence
├─ Link Analysis
└─ Incident Detection
    ↓
[Frontend Visualization]
├─ Echo Chamber Dashboard
├─ Narrative Arc Chart
├─ Opinion Divergence Panel
└─ Link Analyzer
    ↓
User Insights
```

---

## ECHO CHAMBER DETECTION

### **Concept**
Echo chambers = isolated communities where members primarily interact with like-minded individuals, reducing exposure to diverse viewpoints

### **Algorithm** (`analysis/echo_chamber.py`)

```python
class EchoChamberAnalyzer:
    
    def calculate_echo_score(subreddit_data):
        """
        Measures how isolated a community is (0-1 scale)
        """
        
        # [Step 1] Extract user-to-user interaction network
        # Build graph: nodes=users, edges=comments/upvotes between users
        users = extract_unique_authors(posts_and_comments)
        interactions = []
        
        for comment in comments:
            # Connect: commenter → post_author
            interactions.append({
                "from": comment.author,
                "to": comment.post.author,
                "weight": 1 + (comment.score / 100)  # Weighted by engagement
            })
        
        # [Step 2] Calculate modularity (measure of community clustering)
        # High modularity = strong internal structure, poor external connections
        modularity = calculate_modularity(user_network)
        # Typical range: 0.3-0.7 (lower = more mixed discussions)
        
        # [Step 3] Calculate sentiment consistency
        # Do users tend to agree with each other?
        sentiments = [analyze_sentiment(comment.text) for comment in comments]
        std_dev = calculate_std_dev(sentiments)  # Low = consistent, High = diverse
        sentiment_consistency = 1 - (std_dev / 100)  # Normalize to 0-1
        
        # [Step 4] Calculate cross-community references
        # Do discussions reference outside communities?
        external_refs = count_refs_to_other_subreddits(posts)
        max_possible_refs = len(posts) * 5  # Estimate
        external_engagement = external_refs / max_possible_refs
        # High = open community, Low = insular
        
        # [Step 5] Combine factors
        echo_score = (
            0.4 * modularity +           # Network isolation
            0.3 * sentiment_consistency + # Opinion alignment
            0.3 * (1 - external_engagement)  # Lack of external refs
        )
        # Result: 0-1 scale (1 = perfect echo chamber)
        
        return {
            "echo_score": echo_score,
            "modularity": modularity,
            "sentiment_consistency": sentiment_consistency,
            "external_engagement": external_engagement,
            "classification": (
                "Extreme Echo Chamber" if echo_score > 0.75
                else "Strong Echo Chamber" if echo_score > 0.6
                else "Moderate Echo Chamber" if echo_score > 0.4
                else "Weak Echo Chamber" if echo_score > 0.25
                else "Open Community"
            )
        }
    
    def identify_user_clusters(subreddit_data):
        """
        Find groups of users within community (e.g., 3 clusters in r/politics)
        """
        
        # [Step 1] Build user interaction matrix
        # users × users matrix: strength of interaction
        interactions = []
        for comment in comments:
            interactions.append([
                comment.author,
                comment.post.author,
                comment.score
            ])
        
        # [Step 2] Apply community detection algorithm
        # Using: Louvain algorithm (fast, parallel-friendly)
        clusters = louvain_community_detection(interaction_matrix)
        # Result: {cluster_id: [user1, user2, ...], ...}
        
        # [Step 3] Characterize each cluster
        for cluster_id, users in clusters.items():
            cluster_posts = posts.filter(author in users)
            cluster_sentiment = average_sentiment(cluster_posts)
            cluster_topics = extract_topics(cluster_posts)
            
            clusters[cluster_id] = {
                "users": users,
                "size": len(users),
                "avg_sentiment": cluster_sentiment,
                "dominant_topics": cluster_topics,
                "internal_cohesion": measure_cohesion(users, interactions)
            }
        
        return clusters
        
        # Example Output:
        # {
        #   "cluster_1": {
        #     "users": ["user1", "user2", ...],
        #     "size": 45,
        #     "avg_sentiment": 0.8 (positive),
        #     "dominant_topics": ["socialism", "wealth_tax", ...],
        #     "internal_cohesion": 0.92
        #   },
        #   "cluster_2": {
        #     "users": ["user10", "user20", ...],
        #     "size": 38,
        #     "avg_sentiment": -0.7 (negative),
        #     "dominant_topics": ["freedom", "government_overreach", ...],
        #     "internal_cohesion": 0.88
        #   }
        # }
```

### **Frontend Component** (`EchoChamberDashboard.jsx`)

```jsx
Displays:
├─ [Card 1] Overall Echo Score
│  ├─ Large number: 0.72
│  ├─ Classification: "Strong Echo Chamber"
│  └─ Explanation: "This community shows high internal agreement"
│
├─ [Card 2] User Clusters
│  ├─ Visual: Network graph showing 3-5 clusters
│  ├─ Colors: Each cluster different color
│  ├─ Stats: Cluster size, sentiment, topics
│  └─ Interaction: Hover for details
│
├─ [Card 3] Sentiment Distribution
│  ├─ Histogram: Sentiment scores (-1 to +1)
│  ├─ Overlay: Bell curve showing concentration
│  └─ Stat: "95% of comments between +0.2 and +0.8"
│
├─ [Card 4] External References
│  ├─ Bar chart: % of posts referencing other communities
│  └─ Stat: "Only 12% mention other subreddits (low)"
│
└─ [Card 5] Temporal Trends
   ├─ Line chart: Echo score over time
   ├─ X-axis: Week
   └─ Y-axis: Echo score (0-1)
```

---

## NARRATIVE ARC ANALYSIS

### **Concept**
Track how stories/topics evolve in communities over time:
- Introduction → Build-up → Climax → Resolution → Decline

### **Algorithm** (`analysis/narrative_arc.py`)

```python
class NarrativeArcAnalyzer:
    
    def extract_narrative_threads(subreddit_data, time_window):
        """
        Identify distinct stories/topics and their evolution
        """
        
        # [Step 1] Identify topic clusters over time
        # Group posts by topic (using NLP)
        topics = extract_topics_lda(posts, num_topics=10)
        # Result: {topic_1: [post_ids], topic_2: [post_ids], ...}
        
        # [Step 2] Track volume over time
        for topic_id, posts in topics.items():
            daily_volume = {}
            for date in time_range:
                daily_volume[date] = len(posts.filter(date=date))
            
            # Detect narrative arc stages:
            stage = classify_stage(daily_volume)
            # Returns: "introduction" | "buildup" | "climax" | "resolution" | "decline"
        
        return narratives
        
        # Example Output:
        # {
        #   "narrative_1": {
        #     "topic": "COVID-19 Lab Leak Investigation",
        #     "timeline": [
        #       {"date": "2021-05-15", "volume": 10, "stage": "introduction"},
        #       {"date": "2021-05-16", "volume": 45, "stage": "buildup"},
        #       {"date": "2021-05-17", "volume": 280, "stage": "climax"},
        #       {"date": "2021-05-18", "volume": 190, "stage": "resolution"},
        #       {"date": "2021-05-19", "volume": 50, "stage": "decline"}
        #     ],
        #     "peak_date": "2021-05-17",
        #     "peak_volume": 280,
        #     "total_posts": 575
        #   }
        # }
    
    def analyze_messaging_shift(narrative):
        """
        Track how the narrative is framed over time
        """
        
        # [Step 1] Segment posts into time periods
        periods = divide_into_periods(narrative.timeline)
        
        # [Step 2] Extract key phrases per period
        for period in periods:
            phrases = extract_key_phrases(period.posts)
            sentiment = average_sentiment(period.posts)
            framing = detect_framing(period.posts)  # Positive/negative/neutral
            
            period.analysis = {
                "key_phrases": phrases,
                "sentiment": sentiment,
                "framing": framing
            }
        
        return periods
        
        # Example Output:
        # [
        #   {
        #     "period": "Early Stage",
        #     "key_phrases": ["lab leak", "investigation", "origins"],
        #     "sentiment": 0.1 (neutral),
        #     "framing": "investigative"
        #   },
        #   {
        #     "period": "Peak Coverage",
        #     "key_phrases": ["WHO cover-up", "conspiracy", "dangerous"],
        #     "sentiment": -0.6 (negative),
        #     "framing": "accusatory"
        #   },
        #   {
        #     "period": "Late Stage",
        #     "key_phrases": ["lab leak confirmed", "scientific consensus"],
        #     "sentiment": 0.4 (positive),
        #     "framing": "conclusive"
        #   }
        # ]
```

### **Frontend Component** (`NarrativeArcChart.jsx`)

```jsx
Displays:
├─ [Chart 1] Timeline Chart
│  ├─ X-axis: Date (1 month)
│  ├─ Y-axis: Post volume
│  ├─ Line: Volume over time with arc curve
│  ├─ Color zones: By stage (introduction/buildup/climax/etc)
│  └─ Peak marker: Highest volume with date
│
├─ [Chart 2] Messaging Shift
│  ├─ 3 boxes horizontally: Early | Peak | Late
│  ├─ Each box shows:
│  │  ├─ Key phrases (top 5)
│  │  ├─ Sentiment bar
│  │  └─ Framing label
│  └─ Arrow: Shows flow left → right
│
└─ [Details Panel]
   ├─ Narrative title
   ├─ Date range
   ├─ Peak volume
   ├─ Total posts
   └─ Summary sentence
```

---

## OPINION DIVERGENCE MEASUREMENT

### **Concept**
Measure how much disagreement exists in community discussions

### **Algorithm** (`analysis/opinion_divergence.py`)

```python
class OpinionDivergenceAnalyzer:
    
    def calculate_divergence_score(subreddit_data):
        """
        Measures disagreement level (0-1 scale)
        """
        
        # [Step 1] Extract opinions on key topics
        topics = identify_controversial_topics(posts)
        # Result: ["immigration_policy", "climate_change", "election_fraud", ...]
        
        # [Step 2] For each topic, extract sentiment distribution
        for topic in topics:
            posts_on_topic = posts.filter(mentions_topic=topic)
            sentiments = [analyze_sentiment(p.text) for p in posts_on_topic]
            
            # Calculate divergence (variance in sentiment)
            divergence_score = calculate_variance(sentiments)
            # High variance = more disagreement
            # Low variance = consensus
        
        # [Step 3] Calculate polarization index
        # Are there distinct opposing camps?
        polarization = detect_bimodal_distribution(sentiments)
        # Returns: 0-1 (1 = two distinct groups, 0 = smooth distribution)
        
        return {
            "divergence_score": divergence_score,
            "polarization_index": polarization,
            "controversial_topics": topics,
            "classification": (
                "Highly Polarized" if polarization > 0.7
                else "Moderately Divergent" if divergence_score > 0.5
                else "Relatively Consensus"
            )
        }
        
        # Example Output:
        # {
        #   "divergence_score": 0.68,
        #   "polarization_index": 0.82,
        #   "controversial_topics": [
        #     {
        #       "topic": "election_fraud",
        #       "sentiment_mean": -0.1 (mixed),
        #       "sentiment_std": 0.8 (high divergence),
        #       "post_count": 450
        #     },
        #     ...
        #   ],
        #   "classification": "Highly Polarized"
        # }
```

### **Frontend Component** (`OpinionDivergencePanel.jsx`)

```jsx
Displays:
├─ [Chart 1] Sentiment Distribution
│  ├─ Histogram with bars from -1 (negative) to +1 (positive)
│  ├─ Colors: Red (negative) → Blue (positive)
│  ├─ Show: Distribution shape (bimodal = polarized)
│  └─ Stat: Standard deviation (how spread out)
│
├─ [Chart 2] Polarization Index
│  ├─ Gauge chart: 0 to 1
│  ├─ Needle pointing at value
│  └─ Label: "Highly Polarized" or similar
│
├─ [Card] Controversial Topics
│  ├─ List of topics with:
│  │  ├─ Topic name
│  │  ├─ Sentiment distribution (mini-histogram)
│  │  ├─ Post count
│  │  └─ "Most Divisive" badge
│  └─ Clickable for details
│
└─ [Legend]
   └─ Color meanings and metrics explained
```

---

## LINK ANALYSIS

### **Concept**
Track information flow between communities and identify coordinated sharing

### **Algorithm** (`analysis/link_analyzer.py`)

```python
class LinkAnalyzer:
    
    def extract_external_links(subreddit_data):
        """
        Find all external URLs shared and their patterns
        """
        
        # [Step 1] Extract URLs from all posts and comments
        urls = extract_urls_from_text(posts + comments)
        # Result: ["https://bbc.com/article1", "https://twitter.com/user", ...]
        
        # [Step 2] Categorize by domain
        domain_counts = count_by_domain(urls)
        # Result: {"bbc.com": 45, "twitter.com": 38, "youtube.com": 22, ...}
        
        # [Step 3] Extract article titles and sentiment
        for url in urls:
            article = fetch_page_title_and_content(url)
            sentiment = analyze_sentiment(article.title)
            domain_popularity = domain_counts[extract_domain(url)]
            
            link_data = {
                "url": url,
                "domain": domain,
                "title": article.title,
                "shares": domain_popularity,
                "sentiment": sentiment
            }
        
        return links
        
        # Example Output:
        # [
        #   {
        #     "url": "https://bbc.com/lab-leak",
        #     "domain": "bbc.com",
        #     "title": "Lab Leak Investigation Reopened",
        #     "shares": 12,
        #     "sentiment": -0.2 (slightly negative)
        #   },
        #   ...
        # ]
    
    def detect_coordinated_sharing(links):
        """
        Identify if multiple users are sharing same links (potential coordination)
        """
        
        # [Step 1] For each link, find all users who shared it
        for link in links:
            users_who_shared = find_users_sharing(link)
            # Result: [user1, user2, user3, ...]
            
            # [Step 2] Check if sharing happened in short time window
            time_diffs = calculate_time_differences(users_who_shared)
            
            if all(diff < 1_hour for diff in time_diffs):
                link["coordinated"] = True
                link["coordination_score"] = calculate_score(
                    num_users=len(users_who_shared),
                    time_compression=compress_time_diffs(time_diffs)
                )
        
        return links
        
        # Example Output:
        # [
        #   {
        #     "url": "https://fox.com/election",
        #     "shares": 45,
        #     "users_involved": ["user1", "user2", "user3", ...],
        #     "coordinated": True,
        #     "coordination_score": 0.87
        #   }
        # ]
```

### **Frontend Component** (`LinkAnalyzer.jsx`)

```jsx
Displays:
├─ [Search Bar]
│  └─ Filter by: URL, domain, sentiment, coordination
│
├─ [Table] Top Shared Links
│  ├─ Columns:
│  │  ├─ Article title (clickable)
│  │  ├─ Domain
│  │  ├─ Times shared
│  │  ├─ Sentiment (color-coded)
│  │  └─ Coordinated (badge)
│  └─ Sort: By shares, by sentiment, by coordination
│
├─ [Chart] Domain Breakdown
│  ├─ Pie chart: % of links by domain
│  └─ Top 10 domains
│
└─ [Network Graph] Link Sharing Network
   ├─ Nodes: Domains
   ├─ Edges: Sharing relationships
   └─ Edge width: Number of shared links
```

---

## INCIDENT DETECTION

### **Concept**
Automatically identify emerging topics, crises, or events getting sudden attention

### **Algorithm** (`analysis/incident_detection.py`)

```python
class IncidentDetector:
    
    def detect_volume_spikes(subreddit_data):
        """
        Identify sudden increases in post volume
        """
        
        # [Step 1] Calculate baseline volume
        baseline = calculate_rolling_average(daily_volumes, window=7_days)
        # Typical daily volume
        
        # [Step 2] Compare current to baseline
        for date in recent_dates:
            current_volume = daily_volumes[date]
            baseline_for_date = baseline[date]
            
            # Calculate z-score (how many standard deviations above mean)
            z_score = (current_volume - baseline_for_date) / std_dev
            
            if z_score > 3:  # 3 standard deviations = significant spike
                spike = {
                    "date": date,
                    "volume": current_volume,
                    "spike_magnitude": z_score,
                    "top_topics": extract_topics_on_date(date),
                    "severity": classify_severity(z_score)
                }
                incidents.append(spike)
        
        return incidents
        
        # Example Output:
        # [
        #   {
        #     "date": "2024-02-20",
        #     "volume": 850,
        #     "spike_magnitude": 4.2,
        #     "top_topics": ["breaking_news", "controversy", "government"],
        #     "severity": "CRITICAL"
        #   }
        # ]
    
    def extract_incident_details(spike_date):
        """
        Get full details of what happened on spike date
        """
        
        # [Step 1] Extract all posts from spike date
        spike_posts = posts.filter(date=spike_date)
        
        # [Step 2] Cluster by topic
        topics = extract_topics_lda(spike_posts, num_topics=5)
        
        # [Step 3] For each topic, get:
        for topic in topics:
            top_posts = spike_posts.filter(topic=topic).sort_by_score()[:5]
            sentiment = average_sentiment(top_posts)
            key_phrases = extract_phrases(top_posts)
            
            topic_detail = {
                "topic": topic,
                "post_count": len(spike_posts.filter(topic=topic)),
                "sentiment": sentiment,
                "key_phrases": key_phrases,
                "top_post": {
                    "title": top_posts[0].title,
                    "score": top_posts[0].score,
                    "url": top_posts[0].url
                }
            }
        
        return incident_details
        
        # Example Output:
        # {
        #   "incident_date": "2024-02-20",
        #   "topics": [
        #     {
        #       "topic": "Political scandal",
        #       "post_count": 450,
        #       "sentiment": -0.8 (negative),
        #       "key_phrases": ["resignation", "investigation", "alleged"],
        #       "top_post": {...}
        #     }
        #   ]
        # }
```

### **Frontend Component** (Incidents page)

```jsx
Displays:
├─ [Timeline] Incident History
│  ├─ Vertical timeline with recent incidents
│  ├─ Each incident:
│  │  ├─ Date
│  │  ├─ Spike magnitude (visual)
│  │  ├─ Severity label (CRITICAL/HIGH/MEDIUM)
│  │  ├─ Top topics
│  │  └─ Click to expand
│  └─ Newest first
│
├─ [Incident Detail Panel]
│  ├─ Date, magnitude, severity
│  ├─ Topics involved (cards with stats)
│  ├─ Sentiment distribution
│  ├─ Top 5 posts
│  └─ Trend graph (3-day window)
│
└─ [Controls]
   └─ Filter: By severity, by date range
```

---

## FRONTEND COMPONENTS

### **Component Hierarchy**

```
CrawlMode (main page)
├─ EchoChamberDashboard
│  ├─ EchoScoreCard
│  ├─ UserClustersGraph
│  ├─ SentimentDistribution
│  ├─ ExternalReferencesChart
│  └─ TemporalTrendsChart
│
├─ NarrativeArcChart
│  ├─ TimelineChart (main arc visualization)
│  ├─ MessagingShiftPanel
│  └─ NarrativeDetails
│
├─ OpinionDivergencePanel
│  ├─ SentimentDistributionHistogram
│  ├─ PolarizationGauge
│  ├─ ControversialTopicsList
│  └─ Legend
│
└─ LinkAnalyzer
   ├─ SearchBar
   ├─ TopLinksTable
   ├─ DomainBreakdownChart
   └─ LinkSharingNetwork
```

### **Data Cache** (`DataCacheContext.jsx`)

Purpose: Share investigation data across all components

```jsx
const DataCacheContext = createContext();

// Provider wraps entire CrawlMode
<DataCacheProvider>
  <EchoChamberDashboard />
  <NarrativeArcChart />
  <OpinionDivergencePanel />
  <LinkAnalyzer />
</DataCacheProvider>

// All components consume:
const { sessionData, narratives, incidents } = useContext(DataCacheContext);
```

---

## DATABASE SCHEMA

### **Collections**

**investigation_sessions**
```json
{
  "_id": "ObjectId",
  "session_id": "uuid",
  "subreddit": "r/politics",
  "time_window": "7_days",
  "status": "complete",
  "echo_score": 0.68,
  "divergence_score": 0.72,
  "polarization_index": 0.82,
  "created_at": "2024-02-20T10:00:00Z",
  "updated_at": "2024-02-20T10:15:00Z"
}
```

**narrative_artifacts**
```json
{
  "_id": "ObjectId",
  "session_id": "uuid",
  "narrative_id": "narrative_1",
  "topic": "COVID Lab Leak Investigation",
  "timeline": [
    {
      "date": "2021-05-15",
      "volume": 10,
      "stage": "introduction"
    },
    ...
  ],
  "messaging_shifts": [
    {
      "period": "Early Stage",
      "key_phrases": ["lab leak", "investigation"],
      "sentiment": 0.1,
      "framing": "investigative"
    },
    ...
  ]
}
```

**evidence_items** (for social data)
```json
{
  "_id": "ObjectId",
  "session_id": "uuid",
  "type": "post",
  "source": "reddit",
  "subreddit": "r/politics",
  "author": "user123",
  "title": "New study shows...",
  "score": 450,
  "sentiment": 0.65,
  "created_at": "2024-02-20T10:00:00Z",
  "external_links": ["https://bbc.com/..."]
}
```

---

**SOCIAL DISCUSSION IMPLEMENTATION - COMPLETE ANALYSIS PIPELINE**
