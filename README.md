# Meeting Assistant

An agentic AI framework that processes meeting transcripts, generates summaries and follow-up emails, tracks contract information, and provides analytics - all through a user-friendly Gradio interface.

## Features

- **Transcript Processing**: Automatically reads meeting transcripts from text files
- **Summary Generation**: Creates concise meeting summaries with action items
- **Email Generation**: Produces professional follow-up emails in your writing style
- **Contract Tracking**: Extracts and stores contract information in a CSV database
- **Analytics**: Tracks performance metrics and usage statistics
- **User Interface**: Simple Gradio web interface to access all functionality

## Requirements

- Python 3.9+
- Ollama server running locally with gemma3:27b model available
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/meeting-assistant.git
cd meeting-assistant
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Make sure Ollama is installed and running with the gemma3:27b model:
```bash
ollama pull gemma3:27b
```

## Usage

### Directory Structure

Before running the application, ensure you have the following directory structure:
```
meeting-assistant/
├── meeting_assistant.py
├── gradio_app.py
├── minutes/ 
│   └── (your meeting transcript files)
├── output/
│   └── (generated summaries and emails)
└── contracts.csv (will be created automatically)
```

### File Naming Convention

Place your meeting transcript files in the `minutes` folder with the following naming convention:
```
ClientName_YYYYMMDD.txt
```

For example: `Acme_20250503.txt`

### Running the Application

To launch the Gradio interface:

```bash
python gradio_app.py
```

This will start a local web server that you can access at http://127.0.0.1:7860/

### Using the Interface

The Gradio interface has four tabs:

1. **Process Meeting**: Generate summaries and emails from the latest meeting transcript
2. **View Contracts**: See all stored contract information
3. **Contract Analysis**: Get insights from your contract data
4. **Analytics**: View processing metrics and statistics

## How It Works

The system uses LangGraph to create a pipeline of processing steps:

1. **Transcript Reading**: Loads the most recent transcript file
2. **Summarization**: Uses LLM to create meeting summary and action items
3. **Email Generation**: Creates follow-up email in your preferred style
4. **Data Extraction**: Uses the chatlas library to extract structured contract data
5. **Database Update**: Stores contract information in a CSV file
6. **Analytics**: Tracks performance metrics for continuous improvement

All AI processing is done locally through Ollama using the gemma3:27b model.

## Customization

- **Model**: You can change the LLM by modifying the model parameter in `meeting_assistant.py`
- **Email Style**: Adjust the system prompt in the `generate_email` function
- **Contract Fields**: Modify the schema in the `extract_contract_data` function

## Troubleshooting

- **No transcripts found**: Make sure your txt files are in the 'minutes' folder
- **Ollama connection error**: Ensure Ollama is running and the gemma3:27b model is available
- **Gradio interface issues**: Check that you have the latest version of Gradio installed

## License

MIT

## Credits

This project uses the following open-source technologies:
- LangGraph
- LangChain
- Ollama
- Chatlas
- Gradio
