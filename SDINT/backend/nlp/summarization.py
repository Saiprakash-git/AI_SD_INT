import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.tokenize import sent_tokenize

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('punkt_tab')

def summarize_text(text, num_sentences=3):
    """
    Generates an extractive summary of the text using the TextRank algorithm.
    """
    if not text:
        return ""
        
    sentences = sent_tokenize(text)
    if len(sentences) <= num_sentences:
        return text
        
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        # Build token matrix
        X = vectorizer.fit_transform(sentences)
        
        # Calculate cosine similarity between sentences
        similarity_matrix = cosine_similarity(X, X)
        
        # Build graph and run pagerank
        nx_graph = nx.from_numpy_array(similarity_matrix)
        scores = nx.pagerank(nx_graph)
        
        # Sort sentences by pagerank score
        ranked_sentences = sorted(((scores[i], s) for i, s in enumerate(sentences)), reverse=True)
        
        # Select top sentences
        top_sentences = [ranked_sentences[i] for i in range(num_sentences)]
        
        # Maintain original sentence order
        selected_indices = []
        for _, s in top_sentences:
            selected_indices.append(sentences.index(s))
        
        selected_indices.sort()
        summary = " ".join([sentences[i] for i in selected_indices])
        return summary
    except Exception as e:
        print(f"Error in summarizing text: {e}")
        # Fallback: Just return the first N sentences
        return " ".join(sentences[:num_sentences])
