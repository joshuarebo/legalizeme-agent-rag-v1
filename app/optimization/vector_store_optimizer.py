"""
Vector Store Optimizer - For optimizing vector store performance
"""
import os
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import faiss
import pickle
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger(__name__)

class VectorStoreOptimizer:
    """
    Optimizer for vector store performance.
    
    This class provides methods to optimize FAISS vector indexes for faster retrieval
    and better search results.
    """
    
    def __init__(self, vector_db_path: str = None):
        """Initialize the vector store optimizer."""
        self.vector_db_path = vector_db_path or os.getenv("VECTOR_DB_PATH", "./data/vector_db")
        self.index_path = f"{self.vector_db_path}/faiss_index.faiss"
        self.optimized_index_path = f"{self.vector_db_path}/faiss_index_optimized.faiss"
        self.stats_path = f"{self.vector_db_path}/optimization_stats.pkl"
        
        # Optimization parameters
        self.nlist = int(os.getenv("FAISS_NLIST", "100"))  # Number of clusters for IVF
        self.nprobe = int(os.getenv("FAISS_NPROBE", "10"))  # Number of clusters to probe
        self.use_hnsw = os.getenv("FAISS_USE_HNSW", "True").lower() in ("true", "1", "t")
        self.m_hnsw = int(os.getenv("FAISS_M_HNSW", "32"))  # HNSW parameter
        self.ef_construction = int(os.getenv("FAISS_EF_CONSTRUCTION", "200"))  # HNSW parameter
        self.quantize = os.getenv("FAISS_QUANTIZE", "True").lower() in ("true", "1", "t")
        
        # Stats tracking
        self.stats = self._load_stats() or {
            "last_optimization": None,
            "optimization_count": 0,
            "original_size_mb": 0,
            "optimized_size_mb": 0,
            "improvement_pct": 0,
            "query_speedup": 0
        }
    
    def _load_stats(self) -> Optional[Dict[str, Any]]:
        """Load optimization statistics."""
        try:
            if os.path.exists(self.stats_path):
                with open(self.stats_path, "rb") as f:
                    return pickle.load(f)
        except Exception as e:
            logger.error(f"Error loading optimization stats: {str(e)}")
        return None
    
    def _save_stats(self):
        """Save optimization statistics."""
        try:
            with open(self.stats_path, "wb") as f:
                pickle.dump(self.stats, f)
        except Exception as e:
            logger.error(f"Error saving optimization stats: {str(e)}")
    
    def needs_optimization(self) -> bool:
        """
        Check if the vector store needs optimization.
        
        Returns:
            True if optimization is needed, False otherwise
        """
        # Check if original index exists
        if not os.path.exists(self.index_path):
            logger.warning("No FAISS index found at path: " + self.index_path)
            return False
        
        # If no optimized index exists, optimization is needed
        if not os.path.exists(self.optimized_index_path):
            return True
        
        # Check when the last optimization was performed
        last_opt = self.stats["last_optimization"]
        if not last_opt:
            return True
        
        # Check if the original index was modified after the last optimization
        orig_mtime = os.path.getmtime(self.index_path)
        orig_mtime_dt = datetime.fromtimestamp(orig_mtime)
        last_opt_dt = datetime.fromisoformat(last_opt)
        
        # If original index is newer than last optimization, we need to optimize
        return orig_mtime_dt > last_opt_dt
    
    def optimize(self) -> bool:
        """
        Optimize the FAISS vector index.
        
        Returns:
            True if optimization was successful, False otherwise
        """
        if not os.path.exists(self.index_path):
            logger.warning(f"No FAISS index found at path: {self.index_path}")
            return False
        
        try:
            logger.info(f"Starting FAISS index optimization")
            
            # Load the original index
            original_index = faiss.read_index(self.index_path)
            
            # Get original dimensions
            dimension = original_index.d
            
            # Create optimized index
            if self.use_hnsw:
                # HNSW index is optimized for speed
                optimized_index = self._create_hnsw_index(original_index, dimension)
            else:
                # IVF index with quantization
                optimized_index = self._create_ivf_index(original_index, dimension)
            
            # Save the optimized index
            faiss.write_index(optimized_index, self.optimized_index_path)
            
            # Benchmark and save stats
            orig_size = os.path.getsize(self.index_path) / (1024 * 1024)  # MB
            opt_size = os.path.getsize(self.optimized_index_path) / (1024 * 1024)  # MB
            
            speedup = self._benchmark_comparison(original_index, optimized_index)
            
            # Update stats
            self.stats["last_optimization"] = datetime.now().isoformat()
            self.stats["optimization_count"] += 1
            self.stats["original_size_mb"] = round(orig_size, 2)
            self.stats["optimized_size_mb"] = round(opt_size, 2)
            self.stats["improvement_pct"] = round(100 - (opt_size / orig_size * 100), 2) if orig_size > 0 else 0
            self.stats["query_speedup"] = round(speedup, 2)
            
            self._save_stats()
            
            logger.info(f"FAISS index optimization completed successfully")
            logger.info(f"Size reduction: {self.stats['improvement_pct']}%, Query speedup: {speedup}x")
            
            return True
            
        except Exception as e:
            logger.error(f"Error optimizing FAISS index: {str(e)}")
            return False
    
    def _create_hnsw_index(self, original_index, dimension: int) -> faiss.Index:
        """
        Create an HNSW index for better speed.
        
        Args:
            original_index: Original FAISS index
            dimension: Vector dimension
            
        Returns:
            Optimized HNSW index
        """
        # Create HNSW index
        hnsw_index = faiss.IndexHNSWFlat(dimension, self.m_hnsw)
        hnsw_index.hnsw.efConstruction = self.ef_construction
        hnsw_index.hnsw.efSearch = self.ef_construction
        
        # Copy vectors from original index to new index
        if isinstance(original_index, faiss.IndexFlat):
            # Direct copy for flat index
            vectors = faiss.extract_index_vectors(original_index)[1]
            hnsw_index.add(vectors)
        else:
            # For other index types, we need to extract vectors
            ntotal = original_index.ntotal
            batch_size = 10000  # Process in batches to avoid memory issues
            
            for i in range(0, ntotal, batch_size):
                end_idx = min(i + batch_size, ntotal)
                ids = np.arange(i, end_idx, dtype=np.int64)
                vectors = np.zeros((end_idx - i, dimension), dtype=np.float32)
                
                for j, idx in enumerate(range(i, end_idx)):
                    # Reconstruct vector from index
                    vec = np.zeros((1, dimension), dtype=np.float32)
                    original_index.reconstruct(idx, vec[0])
                    vectors[j] = vec[0]
                
                hnsw_index.add(vectors)
        
        return hnsw_index
    
    def _create_ivf_index(self, original_index, dimension: int) -> faiss.Index:
        """
        Create an IVF index with optional quantization.
        
        Args:
            original_index: Original FAISS index
            dimension: Vector dimension
            
        Returns:
            Optimized IVF index
        """
        # Extract vectors from original index
        vectors = None
        
        if isinstance(original_index, faiss.IndexFlat):
            # Direct extraction for flat index
            vectors = faiss.extract_index_vectors(original_index)[1]
        else:
            # For other index types, reconstruct vectors
            ntotal = original_index.ntotal
            vectors = np.zeros((ntotal, dimension), dtype=np.float32)
            
            for i in range(ntotal):
                original_index.reconstruct(i, vectors[i])
        
        # Determine optimal number of clusters
        nlist = min(self.nlist, max(int(vectors.shape[0] / 39), 1))
        
        # Create quantizer
        quantizer = faiss.IndexFlatL2(dimension)
        
        # Create IVF index
        if self.quantize and vectors.shape[0] > 1000:
            # IVF with scalar quantization for larger datasets
            ivf_index = faiss.IndexIVFScalarQuantizer(
                quantizer, dimension, nlist,
                faiss.ScalarQuantizer.QT_8bit
            )
        else:
            # Standard IVF for smaller datasets
            ivf_index = faiss.IndexIVFFlat(quantizer, dimension, nlist)
        
        # Train the index
        ivf_index.nprobe = self.nprobe
        ivf_index.train(vectors)
        ivf_index.add(vectors)
        
        return ivf_index
    
    def _benchmark_comparison(self, original_index, optimized_index, num_queries: int = 10) -> float:
        """
        Benchmark original vs optimized index.
        
        Args:
            original_index: Original FAISS index
            optimized_index: Optimized FAISS index
            num_queries: Number of benchmark queries
            
        Returns:
            Speedup factor (optimized / original)
        """
        try:
            # Generate random query vectors
            dimension = original_index.d
            query_vectors = np.random.random((num_queries, dimension)).astype(np.float32)
            
            # Benchmark original index
            start_time = time.time()
            for i in range(num_queries):
                original_index.search(query_vectors[i:i+1], k=10)
            original_time = time.time() - start_time
            
            # Benchmark optimized index
            start_time = time.time()
            for i in range(num_queries):
                optimized_index.search(query_vectors[i:i+1], k=10)
            optimized_time = time.time() - start_time
            
            # Calculate speedup
            if optimized_time > 0:
                return original_time / optimized_time
            return 1.0
            
        except Exception as e:
            logger.error(f"Error benchmarking indexes: {str(e)}")
            return 1.0
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """
        Get optimization statistics.
        
        Returns:
            Dictionary with optimization statistics
        """
        return self.stats
    
    def update_query_params(self, nprobe: int = None) -> bool:
        """
        Update runtime query parameters for the optimized index.
        
        Args:
            nprobe: Number of clusters to probe during search (IVF only)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.optimized_index_path):
                return False
            
            index = faiss.read_index(self.optimized_index_path)
            
            # Update IVF nprobe if applicable
            if isinstance(index, faiss.IndexIVFFlat) or isinstance(index, faiss.IndexIVFScalarQuantizer):
                if nprobe is not None:
                    index.nprobe = nprobe
            
            # Save the updated index
            faiss.write_index(index, self.optimized_index_path)
            return True
            
        except Exception as e:
            logger.error(f"Error updating query parameters: {str(e)}")
            return False
