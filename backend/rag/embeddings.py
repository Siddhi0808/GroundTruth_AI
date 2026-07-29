import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("groundtruth_ai")

# Lazy loading of sentence transformer model to save startup memory
_model = None

def get_model():
    global _model
    if _model is None:
        logger.info("Loading SentenceTransformer model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

def get_embedding(text: str) -> list:
    """Generates a dense vector embedding list for a given input text string."""
    if not text:
        return []
    model = get_model()
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()