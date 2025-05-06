# Project Structure

Here's the complete structure of the Meeting Assistant project:

```
meeting-assistant/
├── meeting_assistant.py        # Core framework
├── gradio_app.py               # Gradio web interface
├── run.py                      # CLI runner script
├── requirements.txt            # Python dependencies
├── setup.py                    # Package installation
├── README.md                   # Documentation
├── install.sh                  # Installation script
├── .env.example                # Environment configuration template
├── sample_transcript.txt       # Example meeting transcript
├── minutes/                    # Directory for transcript files
│   └── Acme_20250503.txt       # Sample transcript (copied during install)
└── output/                     # Generated content directory
    └── .gitkeep                # Empty file to ensure directory is created
└── logs/                  # Log files
    └── meeting_assistant.log   # Log file for the meeting assistant
    └── meeting_analytics.csv"  # CSV file for meeting analytics
```

## Files Description

1. **meeting_assistant.py**
   - Core framework implementing the LangGraph pipeline
   - Handles transcript reading, summarization, email generation, etc.
   - Includes analytics tracking and logging

2. **gradio_app.py**
   - Provides the web interface
   - Includes tabs for processing, viewing contracts, analytics, etc.

3. **run.py**
   - CLI runner script for both web interface and direct processing
   - Provides command-line options for different functions

4. **requirements.txt**
   - Lists all Python package dependencies

5. **setup.py**
   - Enables package installation via pip

6. **README.md**
   - Comprehensive documentation on installation and usage

7. **install.sh**
   - Creates conda environment
   - Sets up directory structure
   - Installs dependencies
   - Checks for Ollama installation

8. **.env.example**
   - Template for environment configuration
   - Contains settings for model, paths, etc.

9. **sample_transcript.txt**
   - Example meeting transcript for testing

## How to Run

1. **First-time Setup**:
   ```bash
   bash install.sh
   ```

2. **Start the Web Interface**:
   ```bash
   conda activate agent_ai_process_imp
   python run.py --web
   ```

3. **Process Latest Transcript**:
   ```bash
   conda activate agent_ai_process_imp
   python run.py --process
   ```
