# DataPilot — Autonomous Agentic AI Data Analyst Platform

DataPilot is an autonomous agentic data analysis and intelligence platform. It elevates data exploration from static rules into an adaptive, LLM-powered multi-agent system orchestrating hypothesis planning, vector-retrieval augmented guidance (RAG), empirical statistical calculations in a secure sandbox, two-layer claim verification, and observation-grounded executive reporting.

---

## Architecture Overview

```mermaid
flowchart TD
    User([User / Browser]) <--> FE[React / Vite / TS Frontend]
    FE <--> BE[Node.js / Express Gateway]
    BE <--> AI[FastAPI Python Microservice]

    subgraph AI_Engine [Autonomous Multi-Agent System]
        LG[LangGraph StateGraph Engine]
        LLM[LLM Service: Gemini / OpenAI / Claude / Ollama]
        RAG[ChromaDB Knowledge Store & Data Dictionaries]
        SB[Subprocess Code Sandbox & AST Validator]

        LG --> N1[1. Profile Node]
        N1 --> N2[2. Plan Node + RAG Guidance]
        N2 --> N3[3. Execute Step Node]
        N3 --> SB
        N3 --> N4[4. Reflect Node: Adaptive Loop]
        N4 -- Add Step / Iterate --> N3
        N4 -- Completed --> N5[5. Validate Claims Node: 2-Layer Audit]
        N5 --> N6[6. Grounded Report Node: [obs-x] Citations]
    end

    AI --> LG
    RAG -. Best Practice Guides .-> N2
    RAG -. Data Dictionaries .-> N2
    LLM -. Structured Reasoning .-> LG
```

DataPilot is organized into three microservices:

1. **Frontend (`/frontend`)**:
   - Modern monochrome UI built with **React**, **Vite**, **TypeScript**, and **Tailwind CSS**.
   - Interactive charting powered by **Plotly.js**.
   - Features: Autonomous plan cards with reasoning traces, live execution logs with token/latency telemetry, RAG guidance source tags, citation pills (`[obs-1]`), and PDF report export.

2. **Backend API Gateway (`/backend`)**:
   - Built with **Node.js**, **Express**, and **TypeScript**.
   - Handles dataset uploads, session state persistence via **MongoDB (Mongoose)**, and proxies analysis workflows to the AI microservice.
   - Manages Human-in-the-Loop decision points for ML model execution.

3. **AI Microservice (`/ai-service`)**:
   - Built with **FastAPI** and Python.
   - **Multi-Provider LLM Client (`app/core/llm.py`)**: Seamless support for Google Gemini, OpenAI, Anthropic Claude, and Ollama with Pydantic structured output validation, token tracking, cost estimation, and 2x self-repair retry loops.
   - **Autonomous Planner (`app/agents/planner.py`)**: Builds analysis plans with verified tool schemas and fuzzy column name matching, falling back to deterministic templates when LLM is unavailable.
   - **LangGraph Agent Loop (`app/agents/orchestrator.py`)**: Compiles a stateful `StateGraph` with reflection nodes, step budget enforcement (default 12 steps), and Human-in-the-Loop interruption checkpointers (`MemorySaver`).
   - **Real RAG Layer (`app/core/knowledge.py`)**: Persistent **ChromaDB** vector store with markdown header chunking, statistical rulebooks, per-dataset data dictionaries, and past session summaries.
   - **Subprocess Sandbox (`app/tools/sandbox.py`)**: AST safety validator prohibiting dangerous imports, file writing, and dunder reflection; isolated subprocess runner with 5-second CPU timeout and 1-turn LLM code self-repair.
   - **Grounded Reporting & 2-Layer Validation (`app/agents/report_agent.py`, `app/agents/validation_agent.py`)**: Enforces `[obs-x]` observation citations, verifies numerical claims within tolerance, and audits causal claims on correlational findings.

---

## Quick Start

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- MongoDB (Running locally or connection string in environment)

---

### 1. AI Service Setup

```bash
cd ai-service
pip install -r requirements.txt
```

#### Configure Environment Variables
Copy `.env.example` to `.env` in `ai-service/`:

```bash
cp .env.example .env
```

Set your preferred LLM provider:

```ini
# Provider options: gemini | openai | anthropic | ollama
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini-2.5-flash

# Or for OpenAI:
# LLM_PROVIDER=openai
# OPENAI_API_KEY=your_openai_api_key_here
# LLM_MODEL=gpt-4o

# Or for Anthropic:
# LLM_PROVIDER=anthropic
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# LLM_MODEL=claude-3-5-sonnet-20241022

# Or for local Ollama:
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434/v1
# LLM_MODEL=llama3
```

#### Run the AI Service
```bash
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

#### Run Test Suite
```bash
python -m pytest -v
```

---

### 2. Backend Gateway Setup

```bash
cd backend
npm install
npm run dev
```

The backend starts at `http://localhost:5000`.

---

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Core Capabilities

- **Zero Row Leakage**: Raw dataset rows are never sent to the LLM. Only profiles, schemas, and aggregated observation summaries are provided for planning and reporting.
- **Provider-Agnostic LLMs**: Seamlessly switch between Gemini, OpenAI, Claude, or local Ollama with identical structured output validation.
- **Dynamic Retrieval-Augmented Guidance (RAG)**: Integrates statistical best-practice rulebooks, machine learning evaluation criteria, and per-dataset data dictionaries into the agent workflow.
- **Safe Sandboxed Execution**: Custom Python code generated by the agent is inspected by an AST parser and executed in a 5s isolated subprocess with automatic code self-repair.
- **Two-Layer Validation**: Prevents hallucinated metrics by checking empirical tolerance and flagging unwarranted causal claims.
- **Human-in-the-Loop Confirmation**: Pauses execution when complex operations (such as ML model fitting) are scheduled, resuming only upon user approval.
