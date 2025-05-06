"""
Meeting Assistant - Gradio Interface

This script provides a Gradio interface for the Meeting Assistant framework.
It allows users to:
1. Process meeting transcripts
2. View meeting summaries and generated emails
3. View and analyze contract data
4. Check analytics on processing history
5. Generate workflow diagram
"""

import os
import pandas as pd
import gradio as gr
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Import the core meeting assistant functionality
from meeting_assistant import run_meeting_assistant, save_workflow_diagram, get_processed_files

# Ensure directories exist
os.makedirs("minutes", exist_ok=True)
os.makedirs("output", exist_ok=True)
os.makedirs("logs", exist_ok=True)

def process_meeting():
    """Process the most recent meeting transcript."""
    message, final_state = run_meeting_assistant()
    
    if final_state is None:
        return message, "", "", ""
    
    # Format the results
    summary_with_actions = final_state["summary"]
    if final_state["action_items"]:
        summary_with_actions += "\n\nAction Items:\n"
        for item in final_state["action_items"]:
            summary_with_actions += f"- {item}\n"
    
    # Read contracts CSV if it exists
    contracts_html = "<p>No contracts data available yet.</p>"
    if os.path.exists("output/contracts.csv"):
        contracts_df = pd.read_csv("output/contracts.csv")
        contracts_html = contracts_df.to_html(classes="table table-striped")
    
    # Show client info
    client_info = f"Client: {final_state['client_name']}\nMeeting Date: {final_state['meeting_date']}"
    
    return summary_with_actions, final_state["email_content"], contracts_html, client_info

def view_contracts():
    """View the contracts CSV as a dataframe."""
    if os.path.exists("output/contracts.csv"):
        contracts_df = pd.read_csv("output/contracts.csv")
        return contracts_df.to_html(classes="table table-striped")
    else:
        return "<p>No contracts data available yet.</p>"

def analyze_contracts():
    """Create visualizations of contract data."""
    if not os.path.exists("output/contracts.csv"):
        return "No contract data available yet."
    
    contracts_df = pd.read_csv("output/contracts.csv")
    
    if len(contracts_df) < 1:
        return "Not enough contract data for analysis."
    
    # Convert meeting_date to datetime if it exists
    if 'meeting_date' in contracts_df.columns:
        contracts_df['meeting_date'] = pd.to_datetime(contracts_df['meeting_date'], errors='coerce')
    
    # Create a basic analysis report
    report = ""
    
    # Count clients
    if 'client_name' in contracts_df.columns:
        client_counts = contracts_df['client_name'].value_counts()
        report += f"### Client Activity\n"
        for client, count in client_counts.items():
            report += f"- {client}: {count} meetings\n"
    
    # Timeline of meetings if dates are available
    if 'meeting_date' in contracts_df.columns and not contracts_df['meeting_date'].isna().all():
        report += f"\n### Timeline\n"
        report += f"- First meeting: {contracts_df['meeting_date'].min().strftime('%Y-%m-%d')}\n"
        report += f"- Last meeting: {contracts_df['meeting_date'].max().strftime('%Y-%m-%d')}\n"
        report += f"- Total span: {(contracts_df['meeting_date'].max() - contracts_df['meeting_date'].min()).days} days\n"
    
    # Project scope analysis
    if 'project_scope' in contracts_df.columns:
        report += f"\n### Project Scope Overview\n"
        report += f"- Projects with defined scope: {contracts_df['project_scope'].count()}\n"
        if contracts_df['project_scope'].nunique() > 0:
            report += f"- Unique project types: {contracts_df['project_scope'].nunique()}\n"
    
    return report

def view_analytics():
    """Create visualizations of analytics data."""
    analytics_file = "logs/meeting_analytics.csv"
    
    if not os.path.exists(analytics_file):
        return "No analytics data available yet."
    
    analytics_df = pd.read_csv(analytics_file)
    
    if len(analytics_df) < 1:
        return "Not enough analytics data for visualization."
    
    # Convert timestamp to datetime
    analytics_df['timestamp'] = pd.to_datetime(analytics_df['timestamp'])
    
    # Calculate some stats
    total_meetings = len(analytics_df)
    success_rate = (analytics_df['success'].sum() / total_meetings) * 100
    avg_processing_time = analytics_df['processing_time'].mean()
    avg_action_items = analytics_df['action_items_count'].mean()
    
    report = f"""
    ## Analytics Summary
    
    - Total meetings processed: {total_meetings}
    - Success rate: {success_rate:.1f}%
    - Average processing time: {avg_processing_time:.2f} seconds
    - Average action items per meeting: {avg_action_items:.1f}
    
    ### Recent Activity
    
    """
    
    # Get recent entries
    recent_df = analytics_df.sort_values('timestamp', ascending=False).head(5)
    for _, row in recent_df.iterrows():
        report += f"- {row['timestamp'].strftime('%Y-%m-%d %H:%M')}: {row['client_name']} ({row['processing_time']}s, {row['action_items_count']} actions)\n"
    
    return report

def create_workflow_diagram():
    """Generate and display the workflow diagram."""
    try:
        # Generate the diagram
        diagram_path = save_workflow_diagram()
        
        if diagram_path and os.path.exists(diagram_path):
            if diagram_path.endswith('.png'):
                # Return the path to be displayed as an image
                return diagram_path, f"Workflow diagram saved to {diagram_path}"
            elif diagram_path.endswith('.html'):
                # Display the HTML content for the user
                with open(diagram_path, 'r') as f:
                    html_content = f.read()
                return None, f"<p>Workflow diagram saved to {diagram_path}</p><p>You can open this file in a web browser to view the diagram.</p>"
            elif diagram_path.endswith('.md'):
                # Show a message about the Mermaid file
                with open(diagram_path, 'r') as f:
                    md_content = f.read()
                return None, f"<p>Workflow diagram saved as Mermaid markdown to {diagram_path}</p><p>To view it, copy the content below and paste it into https://mermaid.live</p><pre>{md_content}</pre>"
            else:
                return None, f"Workflow diagram saved to {diagram_path}"
        else:
            return None, "Failed to generate workflow diagram"
    except Exception as e:
        return None, f"Error generating workflow diagram: {str(e)}"

def list_processed_files():
    """Show a list of all processed files."""
    processed_files = get_processed_files()
    
    if not processed_files:
        return "No files have been processed yet."
    
    report = "## Processed Files\n\n"
    for filename, timestamp in sorted(processed_files.items(), key=lambda x: x[1], reverse=True):
        # Convert ISO timestamp to datetime for better formatting
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp
            
        report += f"- **{filename}**: {formatted_time}\n"
    
    return report

def create_gradio_app():
    """Create a Gradio app for the meeting assistant."""
    
    with gr.Blocks(title="Meeting Assistant") as app:
        gr.Markdown("# Meeting Assistant")
        gr.Markdown("This application processes meeting transcripts from the 'minutes' folder, generates summaries, action items, follow-up emails, and updates contract information.")
        
        with gr.Tab("Process Meeting"):
            process_btn = gr.Button("Process Latest Meeting")
            client_info = gr.Textbox(label="Client Information", lines=2)
            summary_output = gr.Textbox(label="Meeting Summary and Action Items", lines=10)
            email_output = gr.Textbox(label="Follow-up Email", lines=10)
            contracts_output = gr.HTML(label="Contracts Data")
            
            process_btn.click(
                fn=process_meeting,
                outputs=[summary_output, email_output, contracts_output, client_info]
            )
        
        with gr.Tab("View Contracts"):
            view_btn = gr.Button("View Contracts Database")
            contracts_view = gr.HTML()
            
            view_btn.click(
                fn=view_contracts,
                outputs=[contracts_view]
            )
        
        with gr.Tab("Contract Analysis"):
            analyze_btn = gr.Button("Analyze Contract Data")
            analysis_output = gr.Markdown()
            
            analyze_btn.click(
                fn=analyze_contracts,
                outputs=[analysis_output]
            )
        
        with gr.Tab("Analytics"):
            analytics_btn = gr.Button("View Processing Analytics")
            analytics_output = gr.Markdown()
            
            analytics_btn.click(
                fn=view_analytics,
                outputs=[analytics_output]
            )
            
        with gr.Tab("Workflow Diagram"):
            diagram_btn = gr.Button("Generate Workflow Diagram")
            diagram_image = gr.Image(label="Workflow Diagram")
            diagram_output = gr.HTML(label="Diagram Information")
            
            diagram_btn.click(
                fn=create_workflow_diagram,
                outputs=[diagram_image, diagram_output]
            )
            
        with gr.Tab("Processed Files"):
            files_btn = gr.Button("View Processed Files")
            files_output = gr.Markdown()
            
            files_btn.click(
                fn=list_processed_files,
                outputs=[files_output]
            )
    
    return app

if __name__ == "__main__":
    # Create and launch the Gradio app
    app = create_gradio_app()
    app.launch()
