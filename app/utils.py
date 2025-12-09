"""
THE BRAIN. This file uses Sentence-BERT to understand the meaning of resumes.
"""
import io
from typing import List, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
from sklearn.metrics.pairwise import cosine_similarity

from app.text_preprocessor import TextPreprocessor


# Global model instance (loaded at startup)
model: SentenceTransformer = None


def load_model():
    """Load the Sentence-Transformer model at startup."""
    global model
    if model is None:
        print("Loading Sentence-Transformer model: all-MiniLM-L6-v2...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully!")
    return model


def extract_text_from_pdf(pdf_file: bytes, filename: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_file: PDF file bytes
        filename: Original filename for error reporting
        
    Returns:
        Extracted text as string
    """
    try:
        pdf_reader = PdfReader(io.BytesIO(pdf_file))
        text_parts = []
        
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        
        extracted_text = "\n".join(text_parts)
        
        if not extracted_text.strip():
            return f"[Warning: No text could be extracted from {filename}]"
        
        return extracted_text
    except Exception as e:
        return f"[Error extracting text from {filename}: {str(e)}]"


def generate_embeddings(texts: List[str]) -> np.ndarray:
    """
    Generate embeddings for a list of texts using the loaded model.
    
    Args:
        texts: List of text strings
        
    Returns:
        Numpy array of embeddings
    """
    global model
    if model is None:
        model = load_model()
    
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return embeddings


def calculate_similarity_scores(
    job_description: str,
    resume_texts: List[str],
    resume_filenames: List[str]
) -> List[Tuple[str, str, float]]:
    """
    Calculate cosine similarity scores between job description and resumes.
    
    Args:
        job_description: Job description text
        resume_texts: List of resume text contents
        resume_filenames: List of corresponding filenames
        
    Returns:
        List of tuples: (filename, resume_text, similarity_score)
        Sorted by similarity score (descending)
    """
    if not resume_texts:
        return []
    
    # Generate embeddings
    all_texts = [job_description] + resume_texts
    embeddings = generate_embeddings(all_texts)
    
    # Separate job description and resume embeddings
    jd_embedding = embeddings[0:1]  # Shape: (1, embedding_dim)
    resume_embeddings = embeddings[1:]  # Shape: (n_resumes, embedding_dim)
    
    # Calculate cosine similarity
    similarity_scores = cosine_similarity(jd_embedding, resume_embeddings)[0]
    
    # Create list of (filename, text, score) tuples
    results = [
        (filename, text, float(score))
        for filename, text, score in zip(resume_filenames, resume_texts, similarity_scores)
    ]
    
    # Sort by similarity score (descending)
    results.sort(key=lambda x: x[2], reverse=True)
    
    return results


def format_score(score: float) -> float:
    """
    Format similarity score as percentage (0-100).
    
    Args:
        score: Cosine similarity score (typically -1 to 1, but usually 0 to 1)
        
    Returns:
        Percentage score (0-100)
    """
    # Clamp to [0, 1] range and convert to percentage
    clamped_score = max(0.0, min(1.0, score))
    return round(clamped_score * 100, 2)