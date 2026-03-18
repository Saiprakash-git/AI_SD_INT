from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

def cluster_comments(comments, num_clusters=3):
    """
    Groups comments into defined number of clusters using TF-IDF and K-Means.
    comments: list of string texts
    Returns a list of cluster IDs corresponding to the comments
    """
    # Exclude empty comments
    valid_comments = [c for c in comments if c and len(c.strip()) > 0]
    
    if len(valid_comments) < num_clusters:
        # Not enough comments to cluster meaningfully into num_clusters
        return [0] * len(comments)
        
    try:
        vectorizer = TfidfVectorizer(stop_words='english', min_df=2)
        X = vectorizer.fit_transform(valid_comments)
        
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X).tolist()
        
        # Map clusters back to the original comments array including empty ones
        final_clusters = []
        cluster_idx = 0
        for comment in comments:
            if comment and len(comment.strip()) > 0:
                final_clusters.append(int(clusters[cluster_idx]))
                cluster_idx += 1
            else:
                final_clusters.append(-1) # -1 for empty/invalid comments
                
        return final_clusters
    except Exception as e:
        print(f"Error clustering comments: {e}")
        # Fallback to single cluster
        return [0] * len(comments)
