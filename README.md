# DataPilot — Autonomous AI Data Analyst Platform

An autonomous agentic data analysis and intelligence platform. DataPilot automates the entire analytical lifecycle: dataset ingestion and profiling, hypothesis planning, exploratory data analysis, statistical testing, machine learning modeling, and validated executive report generation with interactive Plotly visualizations.

---

## Architecture Overview

DataPilot is organized into three microservices:

1. **Frontend (`/frontend`)**:
   - Modern monochrome UI built with **React**, **Vite**, **TypeScript**, and **Tailwind CSS**.
   - Interactive charting powered by **Plotly.js**.
   - Complete analytical workspace: dataset ingestion, live trace logging, empirical visualization cards, and PDF report export.

2. **Backend API Gateway (`/backend`)**:
   - Built with **Node.js**, **Express**, and **TypeScript**.
   - Handles dataset uploads, session state persistence via **MongoDB (Mongoose)**, and proxies analysis workflows to the AI microservice.
   - Provides full CRUD endpoints for datasets and analysis sessions.

3. **AI Microservice (`/ai-service`)**:
   - Built with **FastAPI** and Python.
   - Orchestrates multi-agent analysis pipelines using **Pandas**, **SciPy**, **Scikit-Learn**, and **Plotly**.
   - Autonomous agents include: Data Profiler, EDA Agent, Statistical Testing Agent, ML Agent, Visualization Agent, Validation Agent, and Executive Report Agent.

---

## Quick Start

### Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- MongoDB (Running locally or connection string in environment)

### 1. AI Service Setup
```bash
cd ai-service
pip install -r requirements.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Backend Gateway Setup
```bash
cd backend
npm install
npm run dev
```

### 3. Frontend Client Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## Features
- **Clean Ingestion**: Drag & drop or browse CSV and Excel datasets.
- **Dynamic Query Suggestions**: Automatically tailored queries based on the columns of your uploaded dataset.
- **Full Analytical Execution**: Profiling, EDA, ANOVA/t-test, correlation analysis, and predictive models.
- **Session & Work Management**: Option to delete analyzed work and clear sessions or datasets anytime.
- **Executive PDF Export**: Verified intelligence summaries and exportable reports.
