import gensim
from gensim import corpora
from nlp.preprocess import clean_text

def perform_topic_modeling(documents, num_topics=5):
    """
    Builds an LDA topic model for a list of string documents.
    Returns the LDA model, corpus, and dictionary.
    """
    # Preprocess all documents
    clean_docs = [clean_text(doc).split() for doc in documents]
    
    # Remove empty documents
    clean_docs = [doc for doc in clean_docs if doc]
    
    # Create dictionary and corpus
    dictionary = corpora.Dictionary(clean_docs)
    
    # Filter out extreme frequencies to improve topics
    if len(dictionary) > 0:
        dictionary.filter_extremes(no_below=2, no_above=0.5)
        
    corpus = [dictionary.doc2bow(text) for text in clean_docs]
    
    if not corpus or len(dictionary) == 0:
        return None, None, None

    # Train LDA model
    lda_model = gensim.models.LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=num_topics,
        random_state=42,
        update_every=1,
        passes=10,
        alpha='auto',
        per_word_topics=True
    )
    
    return lda_model, corpus, dictionary

def get_dominant_topic(lda_model, dictionary, text):
    """
    Given a model, dictionary, and text, returns the dominant topic ID.
    """
    clean_words = clean_text(text).split()
    bow = dictionary.doc2bow(clean_words)
    
    if not bow:
        return -1
        
    topics = lda_model.get_document_topics(bow)
    if not topics:
        return -1
        
    # Sort topics by probability
    topics.sort(key=lambda x: x[1], reverse=True)
    return topics[0][0]
