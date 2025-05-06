"""
Meeting Assistant - An Agentic AI Framework

This script uses LangGraph to create a pipeline that:
1. Reads meeting transcripts from txt files
2. Summarizes meetings and generates action items
3. Creates follow-up emails
4. Updates a contracts CSV

The Gradio interface is defined in a separate file.
"""

# Standard library imports
import os
import csv
import glob
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Third-party imports
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel

# LangChain and LangGraph imports
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate

# Initialize logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/meeting_assistant.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables
load_dotenv()

# Get model settings from environment variables or use defaults
LLM_MODEL = "gemma3:27b"

# Initialize LLM
llm = ChatOllama(
    model=LLM_MODEL,
    temperature=0, 
    timeout=240 
)

llm_json = ChatOllama(
    model=LLM_MODEL,
    temperature=0,
    timeout=240,
    format="json"
)

output_parser = StrOutputParser()

#------------------------------------------------------------------------------
# Data Models
#------------------------------------------------------------------------------

class MeetingAssistantState(Dict):
    """State for the Meeting Assistant agent."""
    transcript: str
    summary: str
    action_items: List[str]
    email_content: str
    contract_data: Dict[str, Any]
    client_name: str
    meeting_date: str


class ContractDataModel(BaseModel):
    """Data model for contract information extraction."""
    client_name: str
    project_scope: str
    budget: str
    timeline: str
    main_contact: str
    follow_up_date: str
    special_requirements: str


class MeetingAnalytics:
    """Analytics for the Meeting Assistant."""
    
    def __init__(self, log_file: str = "logs/meeting_analytics.csv") -> None:
        """Initialize the analytics tracker.
        
        Args:
            log_file: Path to the CSV file for storing analytics data.
        """
        self.log_file = log_file
        self.current_session: Dict[str, Any] = {}
        
        # Create log file with headers if it doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'timestamp', 'client_name', 'meeting_date', 
                    'transcript_length', 'summary_length', 'action_items_count',
                    'processing_time', 'success'
                ])
    
    def start_session(self, client_name: str, meeting_date: str) -> None:
        """Start tracking a processing session.
        
        Args:
            client_name: Name of the client for the current meeting.
            meeting_date: Date of the meeting being processed.
        """
        self.current_session = {
            'timestamp': datetime.now().isoformat(),
            'client_name': client_name,
            'meeting_date': meeting_date,
            'start_time': time.time(),
            'success': False
        }
        logging.info(f"Started processing session for {client_name} on {meeting_date}")
    
    def end_session(self, state: Optional[Dict[str, Any]], success: bool = True) -> None:
        """End a processing session and log the results.
        
        Args:
            state: The current state dictionary containing processing results.
            success: Whether the processing completed successfully.
        """
        if not self.current_session:
            logging.warning("Tried to end analytics session that wasn't started")
            return
        
        processing_time = time.time() - self.current_session['start_time']
        
        # Update session data
        self.current_session.update({
            'transcript_length': len(state.get('transcript', '')) if state else 0,
            'summary_length': len(state.get('summary', '')) if state else 0,
            'action_items_count': len(state.get('action_items', [])) if state else 0,
            'processing_time': round(processing_time, 2),
            'success': success
        })
        
        # Log to file
        with open(self.log_file, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                self.current_session['timestamp'],
                self.current_session['client_name'],
                self.current_session['meeting_date'],
                self.current_session['transcript_length'],
                self.current_session['summary_length'],
                self.current_session['action_items_count'],
                self.current_session['processing_time'],
                self.current_session['success']
            ])
        
        logging.info(f"Completed processing in {processing_time:.2f}s with success={success}")
        
        # Print summary stats
        if success:
            logging.info(
                f"Process stats: {self.current_session['action_items_count']} action items, "
                f"transcript length: {self.current_session['transcript_length']} chars, "
                f"summary length: {self.current_session['summary_length']} chars"
            )


#------------------------------------------------------------------------------
# Tracking Processed Files
#------------------------------------------------------------------------------
def get_processed_files() -> dict:
    """Get a dictionary of already processed files and their timestamps.
    
    Returns:
        Dictionary mapping filenames to processing timestamps
    """
    processed_log_file = "logs/processed_files.json"
    try:
        if os.path.exists(processed_log_file):
            with open(processed_log_file, 'r') as f:
                return json.load(f)
        else:
            return {}
    except Exception as e:
        logging.error(f"Error reading processed files log: {str(e)}")
        return {}

def mark_file_as_processed(filename: str, timestamp: str) -> None:
    """Mark a file as processed by recording it in the processed files log.
    
    Args:
        filename: The name of the processed file
        timestamp: When the file was processed
    """
    processed_log_file = "logs/processed_files.json"
    try:
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Read existing log
        processed_files = get_processed_files()
        
        # Add new entry
        processed_files[filename] = timestamp
        
        # Write updated log
        with open(processed_log_file, 'w') as f:
            json.dump(processed_files, f, indent=2)
            
        logging.info(f"Marked file as processed: {filename}")
    except Exception as e:
        logging.error(f"Error updating processed files log: {str(e)}")


#------------------------------------------------------------------------------
# Core Pipeline Functions
#------------------------------------------------------------------------------

def initialize_state() -> MeetingAssistantState:
    """Initialize the state dictionary.
    
    Returns:
        An empty state dictionary with all required keys.
    """
    return {
        "transcript": "",
        "summary": "",
        "action_items": [],
        "email_content": "",
        "contract_data": {},
        "client_name": "",
        "meeting_date": ""
    }


def read_transcript(state: MeetingAssistantState) -> MeetingAssistantState:
    """Read meeting transcript from files in minutes subfolder.
    
    Only processes files that haven't been processed before.
    
    Args:
        state: The current state dictionary.
        
    Returns:
        Updated state with transcript and metadata.
    """
    transcript_files = glob.glob("minutes/*.txt")
    
    if not transcript_files:
        state["transcript"] = "No transcript files found."
        logging.warning("No transcript files found in minutes directory")
        return state
    
    # Get the list of already processed files
    processed_files = get_processed_files()
    
    # Filter out already processed files
    new_files = []
    for file_path in transcript_files:
        filename = os.path.basename(file_path)
        if filename not in processed_files:
            new_files.append(file_path)
    
    if not new_files:
        state["transcript"] = "No new transcript files to process."
        logging.info("All transcript files have already been processed")
        return state
    
    # Get the most recent new file by modification time
    latest_file = max(new_files, key=os.path.getmtime)
    filename = os.path.basename(latest_file)
    
    try:
        with open(latest_file, 'r') as file:
            state["transcript"] = file.read()
        
        # Log file info
        file_size = os.path.getsize(latest_file)
        logging.info(f"Read transcript file: {latest_file} ({file_size} bytes)")
        
        # Extract filename parts for metadata
        filename_parts = os.path.splitext(filename)[0].split('_')
        
        # Try to extract client name and date from filename
        if len(filename_parts) >= 2:
            state["client_name"] = filename_parts[0]
            state["meeting_date"] = filename_parts[1]
            logging.info(f"Extracted metadata - Client: {state['client_name']}, Date: {state['meeting_date']}")
        else:
            logging.warning(f"Couldn't extract proper metadata from filename: {filename}")
            state["client_name"] = "Unknown"
            state["meeting_date"] = datetime.now().strftime("%Y%m%d")
        
        # Store the current file being processed in the state
        state["current_file"] = filename
        
    except Exception as e:
        logging.error(f"Error reading transcript file {latest_file}: {str(e)}")
        state["transcript"] = f"Error reading file: {str(e)}"
    
    return state


def summarize_meeting(state: MeetingAssistantState) -> MeetingAssistantState:
    """Summarize the meeting transcript and generate action items.
    
    Args:
        state: The current state dictionary with transcript.
        
    Returns:
        Updated state with summary and action items.
    """
    if not state["transcript"] or state["transcript"] == "No transcript files found.":
        state["summary"] = "No transcript available to summarize."
        logging.warning("No transcript available to summarize")
        return state
    
    logging.info(f"Summarizing meeting transcript ({len(state['transcript'])} chars)")
    start_time = time.time()
    
    try:
        # Create prompt for summarization
        summarize_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="You are an expert meeting assistant. Summarize the following meeting transcript into a concise summary and list of actionable items."),
            HumanMessage(content=f"Here is the meeting transcript:\n\n{state['transcript']}\n\nPlease provide a summary of the discussion and a list of action items.")
        ])
        
        # Create the chain
        summarize_chain = summarize_prompt | llm | output_parser
        
        # Run the chain
        result = summarize_chain.invoke({"transcript": state["transcript"]})
        
        # Parse the result to extract summary and action items
        parts = result.split("Action Items:")
        
        if len(parts) > 1:
            state["summary"] = parts[0].strip()
            action_text = parts[1].strip()
            state["action_items"] = [item.strip().strip('- ') for item in action_text.split('\n') if item.strip()]
            logging.info(f"Extracted {len(state['action_items'])} action items")
        else:
            state["summary"] = result.strip()
            state["action_items"] = []
            logging.warning("No action items found in summary")
        
        # Log performance
        processing_time = time.time() - start_time
        logging.info(f"Summarization completed in {processing_time:.2f}s")
        logging.debug(f"Summary length: {len(state['summary'])} chars")
        
    except Exception as e:
        logging.error(f"Error summarizing meeting: {str(e)}")
        state["summary"] = "Error generating summary."
        state["action_items"] = []
    
    return state


def generate_email(state: MeetingAssistantState) -> MeetingAssistantState:
    """Generate a follow-up email based on meeting summary and action items.
    
    Args:
        state: The current state dictionary with summary and action items.
        
    Returns:
        Updated state with email content.
    """
    try:
        summary = state["summary"]
        actions = "\n".join([f"- {a}" for a in state["action_items"]])
        prompt = f"""
You are an expert at writing professional follow-up emails.

Meeting with: {state['client_name']}
Date: {state['meeting_date']}

Summary:
{summary}

Action Items:
{actions}

Write a concise and professional follow-up email summarizing key points and next steps.
"""
        response = llm.invoke([HumanMessage(content=prompt)])
        state["email_content"] = output_parser.invoke(response)
    except Exception as e:
        logging.exception("Error generating email")
        state["email_content"] = "Error generating follow-up email."
    return state


def extract_contract_data(state: MeetingAssistantState) -> MeetingAssistantState:
    """Extract structured contract data from the meeting transcript.

    Args:
        state: The current state dictionary with transcript.

    Returns:
        Updated state with extracted contract data.
    """
    try:
        # Define prompt for LLM to extract contract data in structured JSON format
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are an expert at extracting contract information from meeting transcripts.
Extract the following details in a structured JSON format:
- client_name: The name of the client or company
- project_scope: A brief description of the project scope
- budget: The budget amount mentioned, if any
- timeline: The project timeline or deadline
- main_contact: The main point of contact at the client
- follow_up_date: The date for follow-up, if mentioned
- special_requirements: Any special requirements or considerations

Format the response as valid JSON with these exact keys."""),
            HumanMessage(content=f"Here is the meeting transcript:\n\n{state['transcript']}")
        ])

        # Create and run the extraction chain
        extract_chain = prompt | llm_json | output_parser
        json_result = extract_chain.invoke({})

        # Try to parse the result as JSON
        import json
        try:
            contract_data = json.loads(json_result)
        except json.JSONDecodeError:
            logging.warning("Couldn't parse JSON response, using fallback extraction")
            contract_data = {
                "client_name": state.get("client_name", "Unknown"),
                "project_scope": "Unknown",
                "budget": "Unknown",
                "timeline": "Unknown",
                "main_contact": "Unknown",
                "follow_up_date": "Unknown",
                "special_requirements": "Unknown"
            }

        # Add meeting date and update state
        contract_data["meeting_date"] = state["meeting_date"]
        state["contract_data"] = contract_data

    except Exception as e:
        logging.exception("Error extracting contract data")
        state["contract_data"] = {
            "client_name": state.get("client_name", "Unknown"),
            "project_scope": "Error in extraction",
            "budget": "Unknown",
            "timeline": "Unknown",
            "main_contact": "Unknown",
            "follow_up_date": "Unknown",
            "special_requirements": f"Error: {str(e)}",
            "meeting_date": state.get("meeting_date", "Unknown")
        }

    return state


def update_contracts_csv(state: MeetingAssistantState) -> MeetingAssistantState:
    """Update or create a contracts CSV with the extracted data.
    
    Args:
        state: The current state dictionary with contract data.
        
    Returns:
        Updated state (unchanged).
    """
    if not state["contract_data"] or "status" in state["contract_data"]:
        logging.warning("No valid contract data to update CSV")
        return state
    
    logging.info("Updating contracts CSV")
    
    try:
        csv_file = "output/contracts.csv"
        contract_data = state["contract_data"]
        
        # Check if file exists to determine if we need to write headers
        file_exists = os.path.isfile(csv_file)
        
        with open(csv_file, mode='a', newline='') as file:
            fieldnames = list(contract_data.keys())
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            # Write header if file is being created
            if not file_exists:
                writer.writeheader()
                logging.info("Created new contracts CSV file")
            
            # Write data row
            writer.writerow(contract_data)
            logging.info(f"Appended data for {contract_data.get('client_name', 'unknown client')} to CSV")
        
    except Exception as e:
        logging.error(f"Error updating contracts CSV: {str(e)}")
    
    return state


def save_outputs(state: MeetingAssistantState) -> MeetingAssistantState:
    """Save the generated content to files.
    
    Args:
        state: The current state dictionary with all generated content.
        
    Returns:
        Updated state (unchanged).
    """
    os.makedirs("output", exist_ok=True)
    
    try:
        # Save summary
        if state["summary"]:
            summary_file = f"output/{state['client_name']}_{state['meeting_date']}_summary.txt"
            with open(summary_file, 'w') as file:
                file.write(state["summary"])
                if state["action_items"]:
                    file.write("\n\nAction Items:\n")
                    for item in state["action_items"]:
                        file.write(f"- {item}\n")
            logging.info(f"Saved summary to {summary_file}")
        
        # Save email
        if state["email_content"]:
            email_file = f"output/{state['client_name']}_{state['meeting_date']}_email.txt"
            with open(email_file, 'w') as file:
                file.write(state["email_content"])
            logging.info(f"Saved email to {email_file}")
            
    except Exception as e:
        logging.error(f"Error saving outputs: {str(e)}")
    
    return state

#------------------------------------------------------------------------------
# LangGraph Workflow
#------------------------------------------------------------------------------

def create_meeting_assistant_graph() -> Any:
    """Create the LangGraph workflow for the meeting assistant.
    
    Returns:
        Compiled StateGraph workflow.
    """
    workflow = StateGraph(MeetingAssistantState)
    
    # Add nodes
    workflow.add_node("read_transcript", read_transcript)
    workflow.add_node("summarize_meeting", summarize_meeting)
    workflow.add_node("generate_email", generate_email)
    workflow.add_node("extract_contract_data", extract_contract_data)
    workflow.add_node("update_contracts_csv", update_contracts_csv)
    workflow.add_node("save_outputs", save_outputs)
    
    # Set up the flow
    workflow.add_edge("read_transcript", "summarize_meeting")
    workflow.add_edge("summarize_meeting", "generate_email")
    workflow.add_edge("generate_email", "extract_contract_data")
    workflow.add_edge("extract_contract_data", "update_contracts_csv")
    workflow.add_edge("update_contracts_csv", "save_outputs")
    workflow.add_edge("save_outputs", END)
    
    # Set the entry point
    workflow.set_entry_point("read_transcript")
    
    return workflow.compile()


def save_workflow_diagram() -> str:
    """Save a visualization of the Meeting Assistant workflow.
    
    Returns:
        Path to the saved workflow diagram file.
    """
    # Ensure the output directory exists
    os.makedirs("output", exist_ok=True)
    
    # We need to create a COMPILED workflow
    workflow = create_meeting_assistant_graph()
    
    # Try to use draw_png first
    output_path_png = "output/meeting_assistant_workflow.png"
    try:
        workflow.get_graph().draw_png(output_path_png)
        logging.info(f"Workflow visualization saved to {output_path_png}")
        return output_path_png
    except Exception as e:
        logging.warning(f"Could not generate PNG diagram: {str(e)}")
    
    # Fall back to generating Mermaid code
    try:
        # Get the Mermaid code
        mermaid_code = workflow.get_graph().draw_mermaid()
        
        # Save as Markdown
        mermaid_path = "output/meeting_assistant_workflow.md"
        with open(mermaid_path, "w") as f:
            f.write("```mermaid\n")
            f.write(mermaid_code)
            f.write("\n```")
        
        # Create an HTML viewer
        html_path = "output/meeting_assistant_workflow.html"
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meeting Assistant Workflow Diagram</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
        }}
        .diagram-container {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <h1>Meeting Assistant Workflow Diagram</h1>
    <div class="diagram-container">
        <div class="mermaid">
{mermaid_code}
        </div>
    </div>
</body>
</html>"""
        
        with open(html_path, "w") as f:
            f.write(html_content)
        
        logging.info(f"Workflow visualization saved as Mermaid to {mermaid_path}")
        logging.info(f"Interactive HTML diagram created at {html_path}")
        
        return html_path
    except Exception as e:
        logging.error(f"Error generating diagram: {str(e)}")
        return None



#------------------------------------------------------------------------------
# Main Application Functions
#------------------------------------------------------------------------------

def run_meeting_assistant() -> tuple[str, Optional[Dict[str, Any]]]:
    """Run the meeting assistant pipeline and track analytics.
    
    Only processes new files that haven't been processed before.
    
    Returns:
        Tuple containing (status message, final state)
    """
    os.makedirs("minutes", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    logging.info("Starting Meeting Assistant")
    
    # Initialize the graph
    meeting_graph = create_meeting_assistant_graph()
    
    # Run the graph
    state = initialize_state()
    
    try:
        # Get initial transcript info to start analytics
        transcript_state = read_transcript(state)
        
        if transcript_state["transcript"] == "No transcript files found.":
            logging.warning("No meeting transcripts found")
            return "No meeting transcripts found in the 'minutes' folder.", None
        
        if transcript_state["transcript"] == "No new transcript files to process.":
            logging.info("No new files to process")
            return "No new meeting transcripts to process.", None
        
        # Start analytics session
        analytics.start_session(
            transcript_state["client_name"],
            transcript_state["meeting_date"]
        )
        
        # Run the full graph
        final_state = meeting_graph.invoke(state)
        
        # Mark the file as processed
        if "current_file" in transcript_state:
            mark_file_as_processed(
                transcript_state["current_file"],
                datetime.now().isoformat()
            )
        
        # End analytics session with success
        analytics.end_session(final_state, success=True)
        
        logging.info(f"Successfully processed meeting for {final_state['client_name']}")
        return "Meeting processed successfully", final_state
        
    except Exception as e:
        logging.error(f"Error processing meeting: {str(e)}")
        analytics.end_session(state, success=False)
        return f"Error processing meeting: {str(e)}", None



#------------------------------------------------------------------------------
# Main Program Entry
#------------------------------------------------------------------------------

# Create analytics instance
analytics = MeetingAnalytics()

if __name__ == "__main__":
    # Just create necessary directories and exit
    os.makedirs("minutes", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    logging.info("Meeting Assistant core module ready")
