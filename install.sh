#!/bin/bash

# Meeting Assistant Installation Script

echo "=== Setting up Meeting Assistant ==="
echo "Creating agent_ai_process_imp conda environment with Python 3.12..."

# Check if conda is installed
if command -v conda >/dev/null 2>&1; then
    # Create conda environment
    conda create -y -n agent_ai_process_imp python=3.12
    
    # Activate the environment
    source "$(conda info --base)/etc/profile.d/conda.sh"
    conda activate agent_ai_process_imp
    
    echo "Conda environment 'agent_ai_process_imp' created and activated."
else
    echo "Conda not found. Please install Miniconda or Anaconda first:"
    echo "Visit https://docs.conda.io/en/latest/miniconda.html for installation instructions."
    exit 1
fi

# Create directory structure
echo "Creating directory structure..."
mkdir -p minutes output

# Copy sample transcript to minutes directory
cp sample_transcript.txt minutes/Acme_20250503.txt

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file from example
if [ ! -f .env ]; then
    echo "Creating .env configuration file..."
    cp .env.example .env
fi

echo "Checking for Ollama installation..."
if command -v ollama >/dev/null 2>&1; then
    echo "Ollama found. Checking for gemma3:27b model..."
    
    # Check if gemma3:27b is already pulled
    if ollama list | grep -q "gemma3:27b"; then
        echo "gemma3:27b model is installed."
    else
        echo "Pulling gemma3:27b model (this may take some time)..."
        ollama pull gemma3:27b
    fi
else
    echo "Ollama not found. Please install Ollama first:"
    echo "Visit https://ollama.com/download for installation instructions."
    echo "After installing Ollama, run: ollama pull gemma3:27b"
fi

echo ""
echo "=== Setup complete! ==="
echo "To use the application:"
echo "1. Activate the conda environment: conda activate agent_ai_process_imp"
echo "2. Start the application: python gradio_app.py"
echo ""
echo "A sample transcript has been placed in the minutes folder for testing."
