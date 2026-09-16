# Self Learning Research Agent

A multi-agent research system built with **Python, LangChain, and LangGraph**.

The project takes a research topic from the user, creates a research plan, searches for relevant information, extracts useful content, combines the findings, and generates a structured research report with sources and citations.

The system can work with both **local LLMs** and **cloud-based LLM providers**.

---

## Overview

The research process is divided into four main agents:

### 1. Research Planner

The planner receives the research topic and creates a structured plan.

It:

* Understands the research topic
* Defines research objectives
* Generates search queries
* Creates an outline for the final report

### 2. Research Searcher

The searcher performs the actual information gathering.

It:

* Uses web search tools
* Searches for relevant sources
* Extracts content from webpages
* Evaluates source credibility
* Collects useful research information

### 3. Research Synthesizer

The synthesizer processes the information collected by the searcher.

It:

* Reviews the collected sources
* Identifies important findings
* Combines information from different sources
* Handles conflicting information
* Produces a set of research findings

### 4. Report Writer

The report writer converts the findings into a final report.

It:

* Organizes the findings into sections
* Writes the final report
* Adds citations
* Creates a references section

---

## Architecture

The current workflow is:

```text
                 User Research Topic
                         |
                         v
                +------------------+
                | Research Planner |
                +------------------+
                         |
                         v
                +-------------------+
                | Research Searcher |
                +-------------------+
                         |
                         v
               +---------------------+
               | Research Synthesizer|
               +---------------------+
                         |
                         v
                +------------------+
                |   Report Writer  |
                +------------------+
                         |
                         v
                  Final Report
```

The workflow is managed using **LangGraph**, which maintains the research state and controls the execution of each stage.

---

## Main Features

* Multi-agent research workflow
* Web search and webpage content extraction
* Source credibility evaluation
* Research planning
* Research synthesis
* Citation-supported reports
* Local LLM support through Ollama
* Cloud LLM support
* Research result caching
* Checkpointing and state persistence
* LLM usage tracking
* Retry and error-handling mechanisms
* Chainlit web interface
* Markdown, HTML, and text report output

---

## Technologies

The project uses:

* **Python**
* **LangChain**
* **LangGraph**
* **Pydantic**
* **Chainlit**
* **Ollama**
* **Gemini**
* **OpenAI-compatible APIs**
* **llama.cpp**
* **SQLite**

---

## Project Structure

```text
self-learning-research-agent/
│
├── agents.py
├── callbacks.py
├── config.py
├── exceptions.py
├── graph.py
├── llm_tracker.py
├── state.py
│
├── main.py
├── app.py
├── chainlit.md
│
├── requirements.txt
├── pyproject.toml
├── .env
├── .gitignore
├── LICENSE
└── README.md
```

### Important Files

#### `agents.py`

Contains the main research agents:

* `ResearchPlanner`
* `ResearchSearcher`
* `ResearchSynthesizer`
* `ReportWriter`

#### `graph.py`

Defines the LangGraph workflow and controls the order in which the research stages are executed.

#### `state.py`

Contains the Pydantic models used to store and pass research information between the different stages.

#### `config.py`

Contains the configuration for:

* LLM providers
* Models
* Search settings
* Report settings
* Credibility thresholds
* Other application settings

#### `callbacks.py`

Handles progress updates while the research process is running.

#### `llm_tracker.py`

Tracks LLM calls and token usage during research.

#### `exceptions.py`

Contains the custom exceptions used throughout the project for handling errors related to configuration, planning, searching, synthesis, and report generation.

#### `main.py`

Main entry point for running the research workflow.

#### `app.py`

Provides the Chainlit interface for interacting with the research agent.

---

## Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd self-learning-research-agent
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

**Windows:**

```bash
.venv\Scripts\activate
```

**Linux/macOS:**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

Create a `.env` file in the project root.

The project supports different LLM providers.

### Ollama

Ollama can be used to run models locally.

First, make sure Ollama is installed and running.

For example:

```bash
ollama pull qwen2.5:7b
```

Then configure:

```env
MODEL_PROVIDER=ollama
MODEL_NAME=qwen2.5:7b
OLLAMA_BASE_URL=http://localhost:11434
```

### Gemini

```env
MODEL_PROVIDER=gemini
MODEL_NAME=gemini-2.5-flash
GOOGLE_API_KEY=your_api_key
```

### OpenAI

```env
MODEL_PROVIDER=openai
MODEL_NAME=your_model
OPENAI_API_KEY=your_api_key
```

### llama.cpp

If you are running a local llama.cpp server:

```env
MODEL_PROVIDER=llamacpp
MODEL_NAME=your_model
LLAMACPP_BASE_URL=http://localhost:8080
```

---

## Running the Agent

### Command Line

Run:

```bash
python main.py
```

### Chainlit Interface

To start the web interface:

```bash
chainlit run app.py
```

After starting Chainlit, open the local address displayed in the terminal.

The interface allows the user to provide a research topic and view the research process and final result.

---

## Research Workflow

When a user provides a research topic, the system processes it through the following stages:

### Step 1 — Planning

The planner analyzes the topic and creates:

* Research objectives
* Search queries
* Report sections

### Step 2 — Searching

The search agent uses the generated queries to find relevant information.

The retrieved sources are then processed and their credibility is evaluated.

### Step 3 — Synthesis

The collected information is analyzed to identify the important findings.

The synthesizer combines information from multiple sources and prepares the research findings.

### Step 4 — Report Generation

The report writer uses the findings to generate the final research report with organized sections, citations, and references.

```text
Topic
  |
  v
Planning
  |
  v
Searching
  |
  v
Synthesis
  |
  v
Report Generation
  |
  v
Final Report
```

---

## Configuration Options

Research behavior can be adjusted through the project configuration.

Some of the available settings include:

* LLM provider
* Model name
* Search provider
* Maximum search queries
* Maximum search results
* Minimum source credibility score
* Maximum report sections
* Minimum section length
* Citation style
* Research caching
* Checkpointing

---

## Output

The final output is a structured research report containing:

* Research findings
* Organized sections
* Source information
* Citations
* References

The project supports report output in:

* Markdown
* HTML
* Text

---

## License

This project is licensed under the **MIT License**.

See the [`LICENSE`](LICENSE) file for the complete license text.
