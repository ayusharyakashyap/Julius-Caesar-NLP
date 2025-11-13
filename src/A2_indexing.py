"""
Phase 2: Indexing & Vector Store

This module handles:
1. Loading processed chunks from JSONL
2. Embedding chunks using sentence-transformers
3. Storing embeddings in ChromaDB with metadata
"""

import jsonlines
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
import json


class JuliusCaesarIndexer:
    """Index Julius Caesar chunks into ChromaDB"""
    
    def __init__(
        self,
        chunks_path: str,
        db_path: str,
        embedding_model_name: str = "BAAI/bge-base-en-v1.5",
        collection_name: str = "julius_caesar"
    ):
        self.chunks_path = Path(chunks_path)
        self.db_path = Path(db_path)
        self.embedding_model_name = embedding_model_name
        self.collection_name = collection_name
        
        # Initialize embedding model
        print(f"Loading embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)
        print(f"Embedding dimension: {self.embedding_model.get_sentence_embedding_dimension()}")
        
        # Initialize ChromaDB client
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.db_path))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "Julius Caesar play chunks with metadata"}
        )
        
        self.chunks: List[Dict[str, Any]] = []
    
    def load_chunks(self) -> List[Dict[str, Any]]:
        """Load chunks from JSON file"""
        print(f"Loading chunks from {self.chunks_path}...")
        
        if not self.chunks_path.exists():
            raise FileNotFoundError(f"Chunks file not found: {self.chunks_path}")
        
        with open(self.chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        self.chunks = chunks
        print(f"Loaded {len(self.chunks)} chunks")
        return self.chunks
    
    def embed_chunks(self, batch_size: int = 32) -> List[List[float]]:
        """Embed all chunks using the embedding model"""
        print(f"Embedding {len(self.chunks)} chunks...")
        
        # Extract text from chunks
        texts = [chunk['text'] for chunk in self.chunks]
        
        # Generate embeddings in batches with progress bar
        embeddings = []
        for i in tqdm(range(0, len(texts), batch_size), desc="Embedding batches"):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = self.embedding_model.encode(
                batch_texts,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            embeddings.extend(batch_embeddings.tolist())
        
        print(f"Generated {len(embeddings)} embeddings")
        return embeddings
    
    def index_chunks(self, embeddings: List[List[float]]) -> None:
        """Index chunks into ChromaDB"""
        print(f"Indexing into ChromaDB collection '{self.collection_name}'...")
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        embeddings_list = []
        
        for i, (chunk, embedding) in enumerate(zip(self.chunks, embeddings)):
            # Use chunk_id if available, otherwise generate
            chunk_id = chunk.get('chunk_id', f"chunk_{i}")
            ids.append(chunk_id)
            
            # Document text
            documents.append(chunk['text'])
            
            # Metadata (ChromaDB requires all values to be strings, ints, or floats)
            metadata = {
                'act': chunk['act'],
                'scene': chunk['scene'],
                'speaker': chunk.get('speaker', ''),
                'type': chunk.get('type', ''),
                'line_range': chunk.get('line_range', ''),
            }
            metadatas.append(metadata)
            
            # Embedding
            embeddings_list.append(embedding)
        
        # Add to collection in batches
        batch_size = 100
        for i in tqdm(range(0, len(ids), batch_size), desc="Indexing batches"):
            batch_end = min(i + batch_size, len(ids))
            
            self.collection.add(
                ids=ids[i:batch_end],
                embeddings=embeddings_list[i:batch_end],
                documents=documents[i:batch_end],
                metadatas=metadatas[i:batch_end]
            )
        
        print(f"Successfully indexed {len(ids)} chunks")
        print(f"Collection count: {self.collection.count()}")
    
    def run_indexing(self) -> None:
        """Run the complete indexing pipeline"""
        print("=" * 60)
        print("Starting Julius Caesar Indexing Pipeline")
        print("=" * 60)
        
        # Load chunks
        self.load_chunks()
        
        # Check if already indexed
        if self.collection.count() > 0:
            print(f"Collection already contains {self.collection.count()} items")
            response = input("Do you want to re-index? (y/n): ").lower()
            if response != 'y':
                print("Skipping indexing")
                return
            else:
                print("Clearing existing collection...")
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Julius Caesar play chunks with metadata"}
                )
        
        # Embed chunks
        embeddings = self.embed_chunks()
        
        # Index into ChromaDB
        self.index_chunks(embeddings)
        
        print("=" * 60)
        print("Indexing Pipeline Complete!")
        print(f"Total chunks indexed: {self.collection.count()}")
        print("=" * 60)
    
    def test_retrieval(self, query: str, n_results: int = 3) -> None:
        """Test retrieval with a sample query"""
        print(f"\n{'=' * 60}")
        print(f"Test Query: '{query}'")
        print('=' * 60)
        
        # Embed query
        query_embedding = self.embedding_model.encode([query])[0].tolist()
        
        # Search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Display results
        print(f"\nTop {n_results} Results:")
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            print(f"\n--- Result {i+1} (Distance: {distance:.4f}) ---")
            print(f"Act {metadata['act']}, Scene {metadata['scene']}")
            print(f"Speaker: {metadata['speaker']}")
            print(f"Type: {metadata['type']}")
            print(f"Text: {doc[:200]}...")
            print("-" * 60)
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed collection"""
        total_count = self.collection.count()
        
        # Get all metadata to compute stats
        all_data = self.collection.get()
        metadatas = all_data['metadatas']
        
        # Count by type
        type_counts = {}
        speaker_counts = {}
        act_counts = {}
        
        for metadata in metadatas:
            chunk_type = metadata.get('type', 'unknown')
            type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
            
            speaker = metadata.get('speaker', '')
            if speaker:
                speaker_counts[speaker] = speaker_counts.get(speaker, 0) + 1
            
            act = metadata.get('act', 0)
            act_counts[act] = act_counts.get(act, 0) + 1
        
        stats = {
            'total_chunks': total_count,
            'chunks_by_type': type_counts,
            'top_10_speakers': sorted(speaker_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'chunks_by_act': dict(sorted(act_counts.items()))
        }
        
        return stats
    
    def print_stats(self) -> None:
        """Print collection statistics"""
        stats = self.get_collection_stats()
        
        print("\n" + "=" * 60)
        print("Collection Statistics")
        print("=" * 60)
        
        print(f"\nTotal Chunks: {stats['total_chunks']}")
        
        print("\nChunks by Type:")
        for chunk_type, count in stats['chunks_by_type'].items():
            print(f"  {chunk_type}: {count}")
        
        print("\nChunks by Act:")
        for act, count in stats['chunks_by_act'].items():
            print(f"  Act {act}: {count}")
        
        print("\nTop 10 Speakers:")
        for speaker, count in stats['top_10_speakers']:
            print(f"  {speaker}: {count}")


def main():
    """Main execution"""
    # Paths
    chunks_path = "data/chunks.json"
    db_path = "data/chroma_db"
    
    # Initialize indexer
    indexer = JuliusCaesarIndexer(
        chunks_path=chunks_path,
        db_path=db_path,
        embedding_model_name="BAAI/bge-base-en-v1.5"
    )
    
    # Run indexing
    indexer.run_indexing()
    
    # Print statistics
    indexer.print_stats()
    
    # Test retrieval
    test_queries = [
        "What does the Soothsayer say to Caesar?",
        "Brutus's internal conflict about killing Caesar",
        "Caesar's death scene"
    ]
    
    print("\n" + "=" * 60)
    print("Testing Retrieval")
    print("=" * 60)
    
    for query in test_queries:
        indexer.test_retrieval(query, n_results=3)


if __name__ == "__main__":
    main()
