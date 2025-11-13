"""
Test script to view retrieved chunks before sending to Gemini
"""

import chromadb
from sentence_transformers import SentenceTransformer

# Initialize components
print("Loading embedding model...")
embedding_model = SentenceTransformer("BAAI/bge-base-en-v1.5")

print("Connecting to ChromaDB...")
chroma_client = chromadb.PersistentClient(path="data/chroma_db")
collection = chroma_client.get_collection(name="julius_caesar")

print(f"Total chunks in database: {collection.count()}\n")
print("="*80)

# Get user query
query = input("Enter your question about Julius Caesar: ")
print("\n" + "="*80)

# How many chunks to retrieve
n_results = 5

# Step 1: Embed the query
print(f"\n🔍 Embedding your query...")
query_embedding = embedding_model.encode([query])[0].tolist()
print(f"✅ Query embedded into {len(query_embedding)}-dimensional vector")

# Step 2: Retrieve relevant chunks
print(f"\n🔍 Searching ChromaDB for top {n_results} relevant chunks...")
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=n_results
)

# Step 3: Display retrieved chunks
print(f"\n✅ Retrieved {len(results['documents'][0])} chunks\n")
print("="*80)
print("📚 RETRIEVED CHUNKS (These will be sent to Gemini)")
print("="*80 + "\n")

for i, (doc, metadata, distance) in enumerate(zip(
    results['documents'][0],
    results['metadatas'][0],
    results['distances'][0]
), 1):
    print(f"{'='*80}")
    print(f"CHUNK {i}")
    print(f"{'='*80}")
    print(f"📝 Text:")
    print(f"   {doc[:300]}{'...' if len(doc) > 300 else ''}")
    print(f"\n📍 Metadata:")
    print(f"   Act: {metadata.get('act')}, Scene: {metadata.get('scene')}")
    print(f"   Speaker: {metadata.get('speaker', 'N/A')}")
    print(f"   Type: {metadata.get('type')}")
    print(f"   Chunk ID: {metadata.get('chunk_id', 'N/A')}")
    print(f"\n📊 Similarity Distance: {distance:.4f} (lower = more relevant)")
    print()

print("="*80)
print("✅ These chunks would now be sent to Gemini for answer generation")
print("="*80)
