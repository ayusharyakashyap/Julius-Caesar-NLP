#!/bin/bash

# Setup script for The Shakespearean Scholar RAG System

echo "========================================"
echo "Setting up Shakespearean Scholar"
echo "========================================"

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your GOOGLE_API_KEY"
    echo ""
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p data
mkdir -p data/chroma_db
mkdir -p evaluation/results

# Check for PDF
if [ ! -f "data/julius-caesar.pdf" ]; then
    echo ""
    echo "⚠️  WARNING: julius-caesar.pdf not found in data/ directory"
    echo "   Please download and place it in data/"
    echo ""
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your GOOGLE_API_KEY"
echo "2. Place julius-caesar.pdf in data/ directory"
echo "3. Run the ETL pipeline:"
echo "   python src/A2_etl_chunking.py"
echo "4. Run the indexing:"
echo "   python src/A2_indexing.py"
echo "5. Start the API:"
echo "   cd api && uvicorn A2_api:app --reload"
echo ""
echo "Or use Docker:"
echo "   docker-compose up --build"
echo ""
