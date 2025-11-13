"""
Phase 3: RAG API Backend

FastAPI backend that orchestrates the RAG pipeline:
1. Receive query
2. Embed query
3. Retrieve relevant chunks from ChromaDB
4. Generate answer using Gemini
5. Return structured response
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import chromadb
from sentence_transformers import SentenceTransformer

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))
from A2_prompt_engineering import ShakespeareanScholar

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Shakespearean Scholar API",
    description="RAG system for Julius Caesar by William Shakespeare",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class QueryRequest(BaseModel):
    """Request model for query endpoint"""
    query: str = Field(..., description="Question about Julius Caesar")
    n_results: int = Field(5, description="Number of chunks to retrieve", ge=1, le=20)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What does the Soothsayer say to Caesar?",
                "n_results": 5
            }
        }


class Source(BaseModel):
    """Source chunk with metadata"""
    chunk: str = Field(..., description="Retrieved text chunk")
    metadata: Dict[str, Any] = Field(..., description="Chunk metadata")
    distance: Optional[float] = Field(None, description="Similarity distance")


class QueryResponse(BaseModel):
    """Response model for query endpoint"""
    answer: str = Field(..., description="Generated answer from Shakespearean Scholar")
    sources: List[Source] = Field(..., description="Retrieved source chunks")
    query: str = Field(..., description="Original query")
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "The Soothsayer warns Caesar to 'Beware the ides of March'...",
                "sources": [
                    {
                        "chunk": "SOOTHSAYER: Beware the ides of March.",
                        "metadata": {
                            "act": 1,
                            "scene": 2,
                            "speaker": "SOOTHSAYER",
                            "type": "dialogue"
                        },
                        "distance": 0.234
                    }
                ],
                "query": "What does the Soothsayer say to Caesar?"
            }
        }


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    db_count: Optional[int] = None


# Global variables for lazy loading
embedding_model = None
chroma_client = None
collection = None
scholar = None


def initialize_components():
    """Initialize all components (called on first request)"""
    global embedding_model, chroma_client, collection, scholar
    
    if embedding_model is None:
        print("Initializing components...")
        
        # Initialize embedding model
        print("Loading embedding model...")
        embedding_model = SentenceTransformer("BAAI/bge-base-en-v1.5")
        
        # Initialize ChromaDB
        print("Connecting to ChromaDB...")
        db_path = Path(__file__).parent.parent / "data" / "chroma_db"
        chroma_client = chromadb.PersistentClient(path=str(db_path))
        collection = chroma_client.get_collection(name="julius_caesar")
        
        # Initialize Shakespearean Scholar
        print("Initializing Shakespearean Scholar...")
        scholar = ShakespeareanScholar()
        
        print("All components initialized successfully!")


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    initialize_components()


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to the Shakespearean Scholar API",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        initialize_components()
        
        # Check database
        db_count = collection.count() if collection else 0
        
        if db_count == 0:
            return HealthResponse(
                status="warning",
                message="API is running but database is empty. Run indexing first.",
                db_count=db_count
            )
        
        return HealthResponse(
            status="healthy",
            message="All systems operational",
            db_count=db_count
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            message=f"Error: {str(e)}"
        )


@app.post("/query", response_model=QueryResponse)
async def query_rag_system(request: QueryRequest):
    """
    Main RAG endpoint: Query the Shakespearean Scholar
    
    This endpoint:
    1. Embeds the user's query
    2. Retrieves relevant chunks from ChromaDB
    3. Generates an answer using Gemini
    4. Returns the answer with sources
    """
    try:
        # Ensure components are initialized
        initialize_components()
        
        # Validate inputs
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Step 1: Embed the query
        print(f"\n{'='*80}")
        print(f"🔍 NEW QUERY: {request.query}")
        print(f"{'='*80}")
        query_embedding = embedding_model.encode([request.query])[0].tolist()
        print(f"✅ Query embedded into {len(query_embedding)}-dimensional vector")
        
        # Step 2: Retrieve relevant chunks
        print(f"\n🔍 Retrieving top {request.n_results} chunks from ChromaDB...")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=request.n_results
        )
        
        # Check if we got results
        if not results['documents'][0]:
            raise HTTPException(
                status_code=404,
                detail="No relevant information found. Please check if the database is properly indexed."
            )
        
        print(f"✅ Retrieved {len(results['documents'][0])} chunks\n")
        
        # Step 3: Format retrieved chunks
        retrieved_chunks = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            retrieved_chunks.append({
                'text': doc,
                'metadata': metadata,
                'distance': distance
            })
            # Log each retrieved chunk
            print(f"📚 CHUNK {i}:")
            print(f"   Act {metadata.get('act')}, Scene {metadata.get('scene')}")
            print(f"   Speaker: {metadata.get('speaker', 'N/A')}, Type: {metadata.get('type')}")
            print(f"   Distance: {distance:.4f}")
            print(f"   Text: {doc[:150]}{'...' if len(doc) > 150 else ''}")
            print()
        
        # Step 4: Generate answer using Gemini
        print(f"🤖 Sending to Gemini for answer generation...")
        answer = scholar.generate_answer(request.query, retrieved_chunks)
        print(f"✅ Answer generated successfully\n")
        
        # Step 5: Format response
        sources = [
            Source(
                chunk=chunk['text'],
                metadata=chunk['metadata'],
                distance=chunk['distance']
            )
            for chunk in retrieved_chunks
        ]
        
        response = QueryResponse(
            answer=answer,
            sources=sources,
            query=request.query
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"ERROR in /query endpoint: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/stats", response_model=Dict[str, Any])
async def get_stats():
    """Get database statistics"""
    try:
        initialize_components()
        
        # Get all data
        all_data = collection.get()
        metadatas = all_data['metadatas']
        
        # Calculate stats
        type_counts = {}
        act_counts = {}
        
        for metadata in metadatas:
            chunk_type = metadata.get('type', 'unknown')
            type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
            
            act = metadata.get('act', 0)
            act_counts[act] = act_counts.get(act, 0) + 1
        
        return {
            "total_chunks": collection.count(),
            "chunks_by_type": type_counts,
            "chunks_by_act": dict(sorted(act_counts.items())),
            "embedding_model": "BAAI/bge-base-en-v1.5",
            "collection_name": "julius_caesar"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@app.post("/search", response_model=List[Source])
async def search_chunks(
    query: str = Query(..., description="Search query"),
    n_results: int = Query(5, description="Number of results", ge=1, le=20)
):
    """
    Search for relevant chunks without generating an answer
    (Useful for debugging and testing retrieval)
    """
    try:
        initialize_components()
        
        # Embed query
        query_embedding = embedding_model.encode([query])[0].tolist()
        
        # Search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        
        # Format results
        sources = []
        for doc, metadata, distance in zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ):
            sources.append(Source(
                chunk=doc,
                metadata=metadata,
                distance=distance
            ))
        
        return sources
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Check for required environment variables
    if not os.getenv("GOOGLE_API_KEY"):
        print("WARNING: GOOGLE_API_KEY not found in environment variables")
        print("Please set it in a .env file")
    
    # Run the API
    uvicorn.run(
        "A2_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
