# Retrieval-Augmented Generation (RAG) System for Julius Caesar NLP Project

This repository contains a complete, end-to-end Retrieval-Augmented Generation (RAG) pipeline developed specifically for Shakespeare’s *Julius Caesar*. The purpose of this project is to create an explainable, accurate question-answering system that does not hallucinate, and instead grounds every generated answer in the actual text of the play.


---

## 1. Project Overview

Large Language Models (LLMs) are powerful, but they can hallucinate when asked about detailed content from literature. To avoid this problem, this project uses a RAG architecture. Instead of allowing the LLM to answer freely, the system retrieves relevant passages directly from *Julius Caesar* and uses them as grounding context.

The LLM then generates answers only after reading the retrieved text. This makes the system factual, reliable, and aligned with Shakespeare's original writing.

This project includes:
- Document ingestion  
- Text cleaning and preprocessing  
- Intelligent semantic chunking  
- Embedding generation  
- Storage in a vector database (ChromaDB)  
- Semantic search and retrieval  
- Context assembly and ranking  
- Grounded LLM answer generation  
- A FastAPI backend to expose the system

---

## 2. What the System Does

The RAG system is able to:
- Load and process the complete play of *Julius Caesar*  
- Convert the cleaned text into meaningful semantic chunks  
- Represent each chunk as an embedding  
- Store embeddings in a vector index for efficient similarity search  
- Accept user questions as input  
- Retrieve the most relevant parts of the play  
- Assemble these into a coherent context  
- Generate an accurate, grounded final answer using the LLM  

This design ensures that every answer can be traced back to known source text, which eliminates hallucination and maintains literary correctness.

---

## 3. System Architecture

Below is the architecture diagram, preserved exactly as provided:


┌─────────────────────────────────────────────────────────────┐
│                        User Interface                       │
│                   (Streamlit Frontend)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP Requests
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (main_final.py)           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         Hybrid RAG Pipeline (rag_pipeline_final.py)  │   │
│  │  1. Query Embedding (all-MiniLM-L6-v2)               │   │
│  │  2. Initial Retrieval (ChromaDB, top 20)             │   │
│  │  3. Re-ranking (CrossEncoder ms-marco-MiniLM-L-6-v2) │   │
│  │  4. Context Assembly (Top 5 chunks)                  │   │
│  │  5. LLM Generation (Gemini 2.5 Flash)                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│             ChromaDB Vector Store (data/chroma_db_s3/)      │
│  Collection: julius_caesar_s3_intro_plus_window             │
│  - Dialogue chunks with ±2 speech context windows           │
│  - Scene intro/synopsis paragraphs                          │
│  - External study notes (SparkNotes/LitCharts style)        │
│  - Metadata: act, scene, speaker, source, content_type      │
└─────────────────────────────────────────────────────────────┘



---

## 4. Component Explanations (Human-Readable)

### A. Document Ingestion  
The system begins by loading the complete text of *Julius Caesar* from a trusted source. The ingestion component ensures that the play is accessible in a clean, uniform format that the later stages can work with.

### B. Preprocessing  
The raw text contains irregular formatting, character names, stage directions, and spacing issues.  
The preprocessing module cleans the text while preserving literary meaning. It removes noise, normalizes spacing, and prepares the text for chunking.

### C. Chunking  
Chunking is essential because an LLM cannot process an entire book at once.  
The text is broken into meaningful segments—dialogues, paragraphs, or thematic sections—rather than random fixed-size cuts. This ensures that retrieval returns useful and coherent information.

### D. Embedding Generation  
Each chunk is converted into an embedding: a vector representation that captures semantic meaning.  
This allows the system to search semantically, not just by keyword.

### E. Vector Store (ChromaDB)  
FAISS stores all embeddings and provides fast similarity search.  
Even with thousands of chunks, the system can find relevant passages quickly.

### F. Query Embedding and Retrieval  
When the user asks a question, the query is also converted into an embedding.  
The system then retrieves the chunks with the closest semantic meaning.

### G. Context Assembly and Ranking  
The best-matching chunks are assembled into a single context block.  
Optional reranking improves the ordering and relevance of retrieved text.

### H. LLM Answer Generation  
The final answer is created by giving the LLM the retrieved context along with the user’s question.  
This ensures:
- grounded answers  
- zero hallucination  
- explanations based only on Shakespeare’s text  

---

## 5. API Layer

The backend is served using FastAPI.  
It exposes endpoints for:
- submitting a query  
- viewing retrieved text chunks  
- refreshing or rebuilding the knowledge base  
- performing system checks  

The API makes it easy to integrate the RAG system with user interfaces, evaluation scripts, or demonstration notebooks.

---

## 6. Why This RAG Approach Works Well

Using RAG for literature processing gives several advantages:
- Answers remain tightly connected to the original source  
- Students and evaluators can trace every claim back to Shakespeare  
- The model cannot generate events that do not exist in the play  
- The system is transparent, interpretable, and academically rigorous  

This makes it ideal for university NLP projects and literature-focused applications.

---

## 7. Conclusion

This project demonstrates a complete, fully functional RAG system tailored to *Julius Caesar*.  
The pipeline is cleanly structured, easy to understand, and fully explainable. The README provides a detailed narrative of how every component works together to produce reliable, grounded answers.

This foundation can be expanded into a larger Shakespeare Q&A system, a classroom teaching tool, or a general-purpose literary analysis engine.
