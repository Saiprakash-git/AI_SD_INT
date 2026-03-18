from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()

def analyze_sentiment(text):
    """
    Analyzes the sentiment of the provided text.
    Returns the sentiment scores and a categorical label (positive, negative, neutral).
    """
    if not text:
        return {"compound": 0, "pos": 0, "neu": 0, "neg": 0}, "neutral"
        
    scores = analyzer.polarity_scores(text)
    
    # Classify based on compound score
    if scores['compound'] >= 0.05:
        label = "positive"
    elif scores['compound'] <= -0.05:
        label = "negative"
    else:
        label = "neutral"
        
    return scores, label
