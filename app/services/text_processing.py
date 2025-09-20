import re
import unicodedata
from typing import List

def clean_text(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize(text: str) -> List[str]:
    return text.split()

def preprocess_review(text: str) -> List[str]:
    cleaned = clean_text(text)
    tokens = tokenize(cleaned)
    return tokens