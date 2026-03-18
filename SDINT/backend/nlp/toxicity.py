from transformers import pipeline

print("Loading toxicity model. This might take a moment on first run...")
try:
    # Use a lightweight toxic comment classification model
    toxicity_classifier = pipeline("text-classification", model="martin-ha/toxic-comment-model", truncation=True)
except Exception as e:
    toxicity_classifier = None
    print(f"Error loading toxicity model: {e}")

def detect_toxicity(text, threshold=0.5):
    """
    Analyzes the provided text for toxicity.
    Returns the toxicity score and a boolean flag indicating if it's considered toxic.
    """
    if not text or toxicity_classifier is None:
        return 0.0, False
        
    try:
        # Pre-trained models usually have a hard limit on sequence length (like 512 tokens),
        # pipeline with truncation=True handles this, but we also slice just in case
        result = toxicity_classifier(text[:2000]) 
        
        label = result[0]['label']
        score = result[0]['score']
        
        # Evaluate model outputs
        # This specific model uses 'toxic' and 'non-toxic'
        is_toxic_label = (label.lower() == 'toxic')
        
        # Calculate actual toxicity score (0.0 to 1.0)
        toxicity_score = score if is_toxic_label else (1.0 - score)
        
        return float(toxicity_score), bool(toxicity_score > threshold)
    except Exception as e:
        print(f"Error during toxicity processing: {e}")
        return 0.0, False
