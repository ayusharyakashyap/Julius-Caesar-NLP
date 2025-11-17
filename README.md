# Retrieval-Augmented Generation (RAG) System for *Julius Caesar*

This repository contains a complete, production-ready Retrieval-Augmented Generation (RAG) system designed specifically for Shakespeare’s *The Tragedy of Julius Caesar*. The objective of this project is to build an academically reliable, explainable question-answering system that bases every generated answer on actual passages from the play. This removes hallucinations and ensures precision suitable for ICSE-level literature work.

The system combines dialogue chunks, contextual windows, scene introductions, and external notes to build a rich retrieval base. A hybrid retrieval pipeline is used to identify, rank, assemble, and provide accurate grounded answers.

---

## 1. Project Overview

Large Language Models often hallucinate when answering detailed literature-based questions. To prevent this, the system implements a Hybrid RAG pipeline. Instead of letting the LLM generate answers using memorized or approximate knowledge, the system retrieves the most relevant passages from a structured database of Julius Caesar content.

This ensures that every answer remains:

- text-accurate  
- non-hallucinated  
- traceable  
- academically reliable  

The project includes:

- Full ingestion of Julius Caesar (dialogues, scene intros, notes)  
- Text cleaning and structured metadata extraction  
- Semantic chunking with contextual windows  
- Transformer-based embedding generation  
- Vector indexing with ChromaDB  
- Two-stage retrieval (semantic + reranking)  
- Grounded answer generation using Gemini  
- FastAPI backend  
- Optional Streamlit user interface  

---

## 2. What the System Does

The system functions as a complete end-to-end retrieval-augmented generation pipeline. It:

- Loads the full text of the play and supporting notes  
- Cleans and preprocesses the raw content  
- Breaks the text into meaningful, retrieval-friendly chunks  
- Converts chunks into embeddings  
- Stores embeddings in ChromaDB  
- Accepts a user query and embeds it  
- Retrieves the most contextually relevant chunks  
- Reranks them with a cross-encoder  
- Assembles the final grounding context  
- Generates a citation-rich, text-supported answer via Gemini  

Every answer is grounded strictly in the retrieved text chunks.

---

## 3. Full System Architecture

Below is the architecture diagram, preserved exactly as provided:

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│                   (Streamlit Frontend)                       │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP Requests
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (main_final.py)            │
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
│             ChromaDB Vector Store (data/chroma_db_s3/)       │
│  Collection: julius_caesar_s3_intro_plus_window             │
│  - Dialogue chunks with ±2 speech context windows           │
│  - Scene intro/synopsis paragraphs                          │
│  - External study notes (SparkNotes/LitCharts style)        │
│  - Metadata: act, scene, speaker, source, content_type      │
└─────────────────────────────────────────────────────────────┘
```

---

---

## 4. Component Explanations

### A. Document Ingestion
The system loads the entire text of *Julius Caesar* along with external study-note content. These documents form the knowledge base used by the retrieval system.

### B. Preprocessing and Cleaning
Raw literary text contains noise such as broken formatting, inconsistent stage directions, and unwanted characters. The system performs:

- artifact removal  
- whitespace normalization  
- extraction of speakers and stage directions  
- reconstruction of act/scene metadata  

This prepares the text for structured chunking.

### C. Semantic Chunking
The play is divided into semantically meaningful chunks, usually based on speeches or short sections of dialogue. Each chunk contains:

- speech text  
- ±2-speech context  
- speaker metadata  
- act/scene information  
- content type (dialogue, intro, analysis)  

This helps the retriever locate relevant, context-rich information.

### D. Embedding Generation
Each chunk is encoded into a dense vector using all-MiniLM-L6-v2. These embeddings represent the meaning of each chunk for retrieval.

### E. Vector Store (ChromaDB)
All chunk embeddings are stored in ChromaDB. This vector index supports:

- persistent storage  
- metadata filtering  
- fast similarity search  

### F. Query Embedding and Retrieval
User queries are embedded, and the most similar 20 chunks are retrieved using vector similarity.

### G. Cross-Encoder Reranking
The retrieved candidates are reranked using ms-marco-MiniLM-L-6-v2 to improve precision. The top 5 final chunks are selected.

### H. LLM Answer Generation
Gemini 2.5 Flash receives:

- the user question  
- the top 5 ranked chunks  

and generates a grounded, citation-aware answer.

---

## 5. Data ETL Pipeline

The ETL pipeline resolves multiple issues found in raw text:

- incorrect speaker extraction  
- malformed or misplaced stage directions  
- inconsistent act/scene boundaries  
- overlapping chunks  
- NaN or infinite numeric values in metadata  

The result is a consistent, high-quality dataset ready for embedding.

---

## 6. Installation and Setup

### Prerequisites

- Python 3.11+  
- Google Gemini API key  
- ChromaDB  
- Optional: Streamlit, Docker  

### Steps

1. Clone the repository  
2. Create a virtual environment  
3. Install dependencies via requirements.txt  
4. Create a `.env` file containing your Gemini API key  
5. Add the required data files to the `data/` directory:
   - julius-caesar.pdf  
   - julius-caeser-notes.pdf  
   - chunks_unstructured_new3.json  

---

## 7. Running the System

### Step 1: ETL and Indexing  
Run the ETL script and indexing script to create:

- chunks_s3_intro_plus_window.json  
- chroma_db_s3/ vector index  

### Step 2: Start the FastAPI Server  
The backend API will be available at:

- http://localhost:8000/query  
- http://localhost:8000/docs  

### Step 3: Query the System  
You can query using Python, curl, or any API client.

### Step 4: Run Evaluation  
The evaluation pipeline generates:

- EVALUATION.md  
- CSV and JSON evaluation outputs  

---

