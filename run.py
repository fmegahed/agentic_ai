#!/usr/bin/env python3
"""
Meeting Assistant Launcher Script

This script provides a simple CLI interface to run either:
1. The gradio web interface
2. Process a specific transcript directly
3. Generate workflow diagram

Usage:
    python run.py --web             # Start the web interface
    python run.py --process         # Process the latest transcript
    python run.py --file filename   # Process a specific transcript file
    python run.py --diagram         # Generate workflow diagram
"""

import argparse
import os
import sys
from rich.console import Console
from rich.panel import Panel

# Import both components
from meeting_assistant import run_meeting_assistant, save_workflow_diagram
import gradio_app

console = Console()

def main():
    """Parse arguments and launch the appropriate function"""
    # Ensure directories exist
    os.makedirs("minutes", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    parser = argparse.ArgumentParser(description="Meeting Assistant")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--web", action="store_true", help="Launch the web interface")
    group.add_argument("--process", action="store_true", help="Process latest transcript")
    group.add_argument("--file", type=str, help="Process a specific transcript file")
    group.add_argument("--diagram", action="store_true", help="Generate workflow diagram")
    
    args = parser.parse_args()
    
    # Show welcome message
    console.print(Panel.fit(
        "[bold blue]Meeting Assistant[/bold blue]\n"
        "[italic]An AI-powered meeting processing system[/italic]",
        border_style="blue"
    ))
    
    if args.diagram:
        console.print("[yellow]Generating workflow diagram...[/yellow]")
        diagram_path = save_workflow_diagram()
        
        if diagram_path:
            console.print(f"[green]Success:[/green] Workflow diagram saved to {diagram_path}")
        else:
            console.print("[red]Error:[/red] Failed to generate workflow diagram")
            
    elif args.web or not (args.process or args.file or args.diagram):
        # Default to web interface if no options specified
        console.print("[yellow]Starting web interface...[/yellow]")
        gradio_app.create_gradio_app().launch()
    
    elif args.process:
        console.print("[yellow]Processing latest transcript...[/yellow]")
        message, state = run_meeting_assistant()
        
        if state:
            console.print(f"[green]Success:[/green] {message}")
            console.print(f"[bold]Client:[/bold] {state['client_name']}")
            console.print(f"[bold]Date:[/bold] {state['meeting_date']}")
            console.print(f"[bold]Action Items:[/bold] {len(state['action_items'])}")
            
            # Display output locations
            summary_file = f"output/{state['client_name']}_{state['meeting_date']}_summary.txt"
            email_file = f"output/{state['client_name']}_{state['meeting_date']}_email.txt"
            
            console.print(f"\nSummary saved to: [cyan]{summary_file}[/cyan]")
            console.print(f"Email saved to: [cyan]{email_file}[/cyan]")
            console.print(f"Contract data appended to: [cyan]output/contracts.csv[/cyan]")
            console.print(f"Analytics saved to: [cyan]logs/meeting_analytics.csv[/cyan]")
        else:
            console.print(f"[red]Error:[/red] {message}")
    
    elif args.file:
        console.print(f"[yellow]Processing specific file not yet implemented[/yellow]")
        console.print(f"Requested file: {args.file}")
    
if __name__ == "__main__":
    main()
