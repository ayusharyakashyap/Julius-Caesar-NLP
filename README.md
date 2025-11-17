# The Shakespearean Scholar - A Containerized RAG System

## Project Overview

This project implements a full-stack, containerized Retrieval-Augmented Generation (RAG) system that serves as an expert AI tutor on William Shakespeare's "The Tragedy of Julius Caesar". The system is designed to answer questions with academic rigor, citing textual evidence, tailored for ICSE Class 10 students.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                       │
│                   (Streamlit Frontend)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP Requests
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │             RAG Pipeline Orchestrator                │   │
│  │  1. Query Embedding                                  │   │
│  │  2. Vector Search (ChromaDB)                         │   │
│  │  3. Context Assembly                                 │   │
│  │  4. LLM Generation (Gemini API)                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    ChromaDB Vector Store                    │
│  - Embedded chunks from Julius Caesar                       │
│  - Metadata: act, scene, speaker, type                      │
└─────────────────────────────────────────────────────────────┘
```

## Design Choices & Justifications

### 1. Data ETL & Chunking Strategy

**Parsing Approach:**
- Used `pdfplumber` for robust table handling and text extraction
- Custom regex patterns to remove Folger artifacts (FTLN numbers, headers, footers)
- Scene detection using ACT/SCENE markers
- Speaker detection using dialogue patterns

**Chunking Strategy:**
- **Logical chunking by scene and speech** rather than fixed-size chunks
- Rationale: Preserves semantic integrity of soliloquies, dialogues, and dramatic context
- Each chunk includes metadata:
  - `act`: Act number
  - `scene`: Scene number
  - `speaker`: Character name (if dialogue)
  - `type`: 'stage_direction', 'dialogue', 'soliloquy', or 'scene_intro'
  - `line_range`: Original line numbers for citation

### 2. Embedding Model

**Choice: `BAAI/bge-base-en-v1.5`**

Justification:
- State-of-the-art performance on MTEB benchmark for retrieval tasks
- 768-dimensional embeddings provide good semantic representation
- Optimized for passage retrieval which matches our use case
- Better than all-MiniLM-L6-v2 for complex literary text

### 3. Vector Store

**Choice: ChromaDB**

Justification:
- Easy to persist and containerize
- Built-in metadata filtering capabilities
- Lightweight and suitable for single-document corpus
- Excellent Python integration

### 4. Generation Model

**Choice: Google Gemini 2.0 Flash (via langchain-google-genai)**

Justification:
- High-quality generation with strong reasoning capabilities
- Excellent at following complex system prompts
- Good at literary analysis and maintaining persona
- API-based approach simplifies deployment vs. local Ollama setup
- Fast response times suitable for interactive use

### 5. Prompt Engineering

The system prompt emphasizes:
- **Persona**: Expert Shakespearean Scholar
- **Audience**: ICSE Class 10 students
- **Constraints**: Only use provided context, always cite sources
- **Tone**: Academic, insightful, and clear
- **Format**: Structured answers with textual evidence

## Setup & Installation

### Prerequisites
- Docker and Docker Compose installed
- Python 3.11+ (for local development)
- Google Gemini API key

### Environment Setup

1. Clone the repository
2. Create a `.env` file in the root directory:
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
```

3. Place the `julius-caesar.pdf` file in the `data/` directory

### Running the System

**Option 1: Using Docker (Recommended)**

```bash
# Build and start all services
docker-compose up --build

# The API will be available at http://localhost:8000
# The Streamlit UI will be available at http://localhost:8501
# API documentation at http://localhost:8000/docs
```

**Option 2: Local Development**

```bash
# Install dependencies
pip install -r requirements.txt

# Run ETL and indexing (first time only)
python src/A2_etl_chunking.py
python src/A2_indexing.py

# Start the API server
cd api
uvicorn A2_api:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start the frontend
cd frontend
streamlit run A2_frontend.py
```

## API Endpoints

### POST /query
Query the RAG system with a question about Julius Caesar.

**Request:**
```json
{
  "query": "What does the Soothsayer say to Caesar?"
}
```

**Response:**
```json
{
  "answer": "The Soothsayer warns Caesar to 'Beware the ides of March'...",
  "sources": [
    {
      "chunk": "SOOTHSAYER: Beware the ides of March...",
      "metadata": {
        "act": 1,
        "scene": 2,
        "speaker": "SOOTHSAYER",
        "type": "dialogue"
      }
    }
  ]
}
```

### GET /health
Health check endpoint.

## Project Structure

```
.
├── README.md
├── EVALUATION.md
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
├── data/
│   ├── julius-caesar.pdf          # Input PDF
│   ├── processed_chunks.jsonl     # Cleaned, chunked data
│   └── chroma_db/                 # Persisted vector store
├── src/
│   ├── A2_etl_chunking.py         # Phase 1: ETL & Chunking
│   ├── A2_indexing.py             # Phase 2: Embedding & Indexing
│   └── A2_prompt_engineering.py   # Phase 4: Prompts & LLM logic
├── api/
│   └── A2_api.py                  # Phase 3: FastAPI backend
├── frontend/
│   └── A2_frontend.py             # Phase 7: Streamlit UI
├── evaluation/
│   ├── evaluation.json            # Test questions
│   ├── A2_evaluation.py           # Evaluation script
│   └── results/                   # Evaluation outputs
└── A2_<roll_number>_infer.ipynb   # Inference notebook
```

## Evaluation

The system is evaluated on:
- **25 baseline factual questions** (provided)
- **10+ analytical questions** (custom additions)

Metrics:
- **Faithfulness**: Are answers grounded in retrieved context?
- **Answer Relevancy**: Do answers directly address the question?
- **Context Precision**: Are retrieved chunks relevant?

See `EVALUATION.md` for detailed results and analysis.

## Development Notes

### Data Quality Improvements
- Scene-based chunking preserves dramatic context
- Metadata enables precise source attribution
- Clean removal of Folger artifacts prevents noise

### Known Limitations
- Cross-scene comparative questions may require multiple retrievals
- Very specific line-level queries depend on chunk granularity
- Character analysis limited to information in retrieved chunks

## Team Contributions

[To be filled with actual team member contributions]

## License

Academic project for IIITB Advanced NLP course.
