import re
import unicodedata
from typing import List, Set
import nltk
from nltk.corpus import stopwords

# Initialize NLTK resources
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# Get English stopwords, fallback to basic set if NLTK fails
try:
    STOPWORDS: Set[str] = set(stopwords.words("english"))
except Exception:
    STOPWORDS: Set[str] = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "has", "he", "in", "is", "it", "its", "of", "on", "that", "the",
        "to", "was", "were", "will", "with"
    }

def clean_text(text: str) -> str:
    """Basic text cleaning: lowercase, remove accents, punctuation."""
    if not text:
        return ""
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def preprocess_for_embedding(text: str) -> str:
    """Process text for embedding models: remove URLs, stopwords, short words."""
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"[^a-z ]", "", text)
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    return " ".join(tokens)

def tokenize(text: str) -> List[str]:
    """Split text into tokens."""
    return text.split()

def preprocess_review(text: str, name: str = None) -> str:
    """Full preprocessing pipeline for reviews including venue name."""
    if name:
        text = f"{name} {text or ''}"
    cleaned = clean_text(text)
    preprocessed = preprocess_for_embedding(cleaned)
    return preprocessed
