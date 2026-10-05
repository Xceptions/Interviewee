# AI Interviewer Agent (LangGraph + RAG + React)

A production-grade, local-first interactive job screening interview platform. The application uses an asynchronous **LangGraph state workflow loop** coupled with a **ChromaDB vector store** context retrieval component to evaluate candidate resumes using local **Ollama** LLM instances.

---

## 📁 System Architecture & Directory Layout

```text
interviewee/
├── backend/                       # Python Core API Ecosystem
│   ├── api/
│   │   └── main.py                # FastAPI endpoints & CORS definitions
│   ├── core/
│   │   ├── agent/
│   │   │   ├── graph.py           # LangGraph State Graph & node routers
│   │   │   └── trigger.py         # Native terminal conversation loop
|   |   ├── ingestion/
│   │   │   ├── parser.py          # Multi-layout PDF & Word Extraction service
│   │   │   └── chroma_service.py  # Chroma API Vector store sliding window ingestion 
│   │   └── config.py              # Pydantic Settings Path Resolver
│   ├── tests/
│   │   │   ├── test_agent.py      # Node architecture tests
│   │   │   ├── test_ingestion.py  # Ingestion pipeline tests
│   │   │   └── test_api.py        # API routing mock test engines
│   ├── pyproject.toml             # Local dynamic editable packaging manifest
│   └── .env                       # Machine environment parameters
├── datastore/
│   ├── uploads/                   # Bucket for storing the uploaded resumes
│   └── chroma_db/                 # Persistent storage vector database files
└── web/                           # Front-End Web Client Engine
    ├── src/
    │   ├── App.tsx                # Single-pane Interactive Chat UI Matrix
    │   ├── main.tsx               # Bootstrap client mounter
    │   └── index.css              # Structural baseline styles
    ├── index.html                 # Browser layout structural template
    ├── package.json               # Node Package configuration scripts
    ├── tsconfig.json              # TypeScript compilation rules
    └── vite.config.ts             # Vite bundler parameters
```




---

## 🛠️ Environmental Settings (`backend/.env`)

Configure the project workspace boundaries by creating a `.env` configuration template file inside the `backend/` path directory:

```env
CHROMA_DB_PATH=../datastore/chroma_db
CHROMA_COLLECTION_NAME=resumes
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

---

## 🚀 Execution & Quick-Start Walkthrough

### Prerequisites
Ensure your local **Ollama** server runtime instance is running and has the model pre-pulled on your system architecture:
```bash
ollama run llama3.2
```

### 1. Fire up the Backend API Server
Navigate to the `backend/` folder directory, install editable packagers, and kickstart the `uvicorn` workspace server:
```bash
cd backend
pip install -e .
pip install uvicorn pytest pydantic-settings
uvicorn api.main:app --reload
```
* **Interactive Document API Portal**: Once up, test raw endpoint integrations through the native Swagger documentation dashboard at **`http://127.0.0`**.

### 2. Boot Up the React App Web Client
Open a separate, dedicated operational terminal matrix, move into the client folder path, install node dependencies, and run the developer bundle:
```bash
cd web
npm install
npm run dev
```
* **Web UI Interface Portal**: Access the client interface panel directly by pointing your local desktop browser to **`http://localhost:5173`**.

---

## 🧪 Automated Testing Procedures

Our test suites run with standard Python isolation paradigms using `pytest` to prevent disk collisions. Execute the test modules right from the `backend/` repository folder level:

* Switch to tests:
  ```bash
  cd backend/tests
  ```

* Run LangGraph workflow step logic states and router routing validations:
  ```bash
  pytest tests/test_agent.py
  ```
* Run full mock FastAPI client integration tests:
  ```bash
  pytest tests/test_api.py
  ```
* Run internal resume parsing string text extractions and chunking checks:
  ```bash
  pytest tests/test_ingestion.py
  ```
* Run all tests:
  ```bash
  pytest
  ```