# Quick Start Guide

## Prerequisites
- Python 3.11+
- Docker and Docker Compose
- Google Gemini API Key

## Setup

### 1. Clone and Setup
```bash
# Make setup script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

### 2. Configure Environment
```bash
# Copy .env template
cp .env.example .env

# Edit .env and add your API key
nano .env
# Add: GOOGLE_API_KEY=your_api_key_here
```

### 3. Add Data
Place `julius-caesar.pdf` in the `data/` directory.

## Running the System

### Option 1: Docker (Recommended)
```bash
# Build and start all services
docker-compose up --build

# The system will be available at:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Frontend: http://localhost:8501
```

### Option 2: Local Development
```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Run ETL pipeline
python src/A2_etl_chunking.py

# 3. Run indexing
python src/A2_indexing.py

# 4. Start API (in terminal 1)
cd api
uvicorn A2_api:app --reload --host 0.0.0.0 --port 8000

# 5. Start frontend (in terminal 2)
cd frontend
streamlit run A2_frontend.py
```

## Running Evaluation
```bash
# Make sure API is running, then:
python evaluation/A2_evaluation.py

# Results will be saved to:
# - EVALUATION.md (main report)
# - evaluation/results/ (detailed results)
```

## Testing the API

### Using curl
```bash
# Health check
curl http://localhost:8000/health

# Query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What does the Soothsayer say to Caesar?"}'
```

### Using the interactive docs
Navigate to http://localhost:8000/docs

## Project Structure
```
.
├── README.md                  # Main documentation
├── QUICKSTART.md             # This file
├── EVALUATION.md             # Evaluation report
├── docker-compose.yml        # Docker orchestration
├── Dockerfile                # API container
├── Dockerfile.frontend       # Frontend container
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
├── data/
│   ├── julius-caesar.pdf     # Input PDF (you provide)
│   ├── processed_chunks.jsonl # Generated chunks
│   └── chroma_db/            # Vector database
├── src/
│   ├── A2_etl_chunking.py    # Phase 1: ETL
│   ├── A2_indexing.py        # Phase 2: Indexing
│   └── A2_prompt_engineering.py # Phase 4: Prompts
├── api/
│   └── A2_api.py             # Phase 3: FastAPI backend
├── frontend/
│   └── A2_frontend.py        # Phase 7: Streamlit UI
├── evaluation/
│   ├── evaluation.json       # Test questions
│   ├── A2_evaluation.py      # Evaluation script
│   └── results/              # Evaluation outputs
└── A2_infer.ipynb           # Inference notebook
```

## Common Issues

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn A2_api:app --port 8001
```

### ChromaDB Not Found
Make sure you've run the indexing step:
```bash
python src/A2_indexing.py
```

### API Key Error
Check that your `.env` file has:
```
GOOGLE_API_KEY=your_actual_key_here
```

## Next Steps
1. Explore the API documentation at `/docs`
2. Try the Streamlit interface at `:8501`
3. Run evaluation to test system performance
4. Review `EVALUATION.md` for analysis

## Support
For issues, check:
- README.md for detailed documentation
- API docs at http://localhost:8000/docs
- Logs from `docker-compose up`
