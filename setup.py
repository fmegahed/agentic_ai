from setuptools import setup, find_packages

setup(
    name="meeting_assistant",
    version="0.1.0",
    description="An agentic AI framework for processing meeting transcripts",
    author="Fadel M. Megahed",
    author_email="fmegahed@miamioh.edu",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.1.0",
        "langchain-core>=0.1.0",
        "langgraph>=0.0.20",
        "langchain-ollama>=0.0.1",
        "pandas>=2.0.0",
        "gradio>=4.0.0",
        "plotly>=5.18.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.12",
)
