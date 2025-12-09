"""
CSV Resume Database with FAISS vector search.
"""
import os
import pickle
import faiss
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from app.utils import load_model, generate_embeddings


class CSVResumeDatabase:
    """FAISS-based vector database for CSV resume search."""
    
    def __init__(self, csv_path: str = "Resume.csv", index_path: str = "resume_index.faiss", metadata_path: str = "resume_metadata.pkl"):
        """
        Initialize the CSV resume database.
        
        Args:
            csv_path: Path to the CSV file containing resumes
            index_path: Path to save/load FAISS index
            metadata_path: Path to save/load resume metadata
        """
        self.csv_path = csv_path
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index = None
        self.metadata = []
        self.model = None
        
    def build_index(self):
        """Build or load the FAISS index from CSV data."""
        # Load the model
        self.model = load_model()
        
        # Check if index already exists
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            print("Loading existing FAISS index...")
            self._load_index()
            return
        
        print("Building FAISS index from CSV...")
        
        # Read CSV
        if not os.path.exists(self.csv_path):
            print(f"Warning: CSV file '{self.csv_path}' not found. Creating empty index.")
            self.index = None
            self.metadata = []
            return
        
        df = pd.read_csv(self.csv_path)
        
        # Extract resume texts and metadata
        resume_texts = []
        metadata_list = []
        
        # Use Resume_str column if available, otherwise try Resume_html
        text_column = None
        if "Resume_str" in df.columns:
            text_column = "Resume_str"
        elif "Resume_html" in df.columns:
            text_column = "Resume_html"
        else:
            print("Warning: No resume text column found in CSV")
            self.index = None
            self.metadata = []
            return
        
        for idx, row in df.iterrows():
            resume_text = str(row.get(text_column, ""))
            if not resume_text or resume_text.strip() == "":
                continue
            
            resume_texts.append(resume_text)
            
            # Store metadata
            metadata_list.append({
                "id": str(row.get("ID", idx)),
                "filename": f"resume_{row.get('ID', idx)}.csv",
                "category": str(row.get("Category", "Unknown")),
                "text": resume_text[:500] + "..." if len(resume_text) > 500 else resume_text,  # Preview
                "full_text": resume_text
            })
        
        if not resume_texts:
            print("Warning: No valid resume texts found in CSV")
            self.index = None
            self.metadata = []
            return
        
        print(f"Generating embeddings for {len(resume_texts)} resumes...")
        
        # Generate embeddings in batches
        batch_size = 32
        all_embeddings = []
        
        for i in range(0, len(resume_texts), batch_size):
            batch = resume_texts[i:i + batch_size]
            embeddings = generate_embeddings(batch)
            all_embeddings.append(embeddings)
            print(f"Processed {min(i + batch_size, len(resume_texts))}/{len(resume_texts)} resumes...")
        
        # Concatenate all embeddings
        embeddings_array = np.vstack(all_embeddings).astype('float32')
        
        # Normalize embeddings for cosine similarity (Inner Product)
        faiss.normalize_L2(embeddings_array)
        
        # Create FAISS index (Inner Product for cosine similarity)
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        self.index.add(embeddings_array)
        
        self.metadata = metadata_list
        
        # Save index and metadata
        self._save_index()
        
        print(f"✅ FAISS index built successfully with {len(metadata_list)} resumes!")
    
    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            print(f"Index saved to {self.index_path}")
    
    def _load_index(self):
        """Load FAISS index and metadata from disk."""
        try:
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            print(f"✅ Loaded index with {len(self.metadata)} resumes from disk")
        except Exception as e:
            print(f"Error loading index: {e}")
            self.index = None
            self.metadata = []
    
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Dict]:
        """
        Search the database for similar resumes.
        
        Args:
            query_vector: Query embedding vector (normalized)
            top_k: Number of top results to return
            
        Returns:
            List of dictionaries with candidate metadata and scores
        """
        if self.index is None or len(self.metadata) == 0:
            return []
        
        # Ensure query vector is normalized and correct shape
        query_vector = query_vector.astype('float32')
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)
        
        faiss.normalize_L2(query_vector)
        
        # Search
        scores, indices = self.index.search(query_vector, min(top_k, len(self.metadata)))
        
        # Format results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                # Convert inner product to similarity score (0-1 range)
                # Inner product of normalized vectors = cosine similarity
                similarity = float(score)
                result["score"] = max(0.0, min(1.0, similarity))  # Clamp to [0, 1]
                results.append(result)
        
        return results

