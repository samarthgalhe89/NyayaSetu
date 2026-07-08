# ⚖️ NyayaSetu
**Your AI Legal Rights Navigator**

NyayaSetu is an AI-powered legal rights assistant for Indian citizens, built using a Retrieval-Augmented Generation (RAG) architecture. It allows users to ask legal questions in plain language and receives structured answers based on actual Indian legal provisions, complete with actionable steps and citations.

## 🌟 Features

- **Semantic Search**: Understands the intent behind your questions, not just exact keywords.
- **Category-Aware**: Automatically detects if your question is about consumer rights, property, RTI, etc., to narrow down searches.
- **Section-Aware Chunking**: Keeps legal provisions intact for better AI understanding.
- **Deduplication Engine**: Prevents identical chunks from bloating the vector store.
- **Glassmorphic UI**: A highly creative, minimalist, and responsive vanilla HTML/CSS/JS frontend.

## 🛠️ Technology Stack

- **Backend Framework**: FastAPI & Uvicorn
- **LLM Provider**: Groq (llama-3.1-8b-instant) via LangChain
- **Vector Database**: ChromaDB (persistent, local)
- **Embeddings**: SentenceTransformers (all-MiniLM-L6-v2)
- **Frontend**: Pure HTML5, CSS3 Custom Properties, Vanilla JavaScript
- **Configuration**: Pydantic Settings

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.12+
- `uv` (recommended) or `pip`

### 2. Installation

Clone this repository or download the source code, then install dependencies:

```bash
uv sync
```
*(Or use `pip install -r requirements.txt` if you prefer).*

### 3. Configuration

Create a `.env` file in the root directory and add your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Ingesting Legal Documents

Before the AI can answer questions, it needs legal knowledge.

1. Place your Indian Legal Act PDFs inside `data/legal_acts/`.
2. Run the ingestion script:

```bash
python scripts/ingest_legal_docs.py
```

This will automatically parse, chunk, embed, and store the legal acts in the ChromaDB vector database.

### 5. Running the Server

Start the application:

```bash
python main.py
```

- Open your browser and navigate to **http://localhost:8000** to use the UI.
- API documentation (Swagger) is available at **http://localhost:8000/docs**.

---

## 📁 Project Structure

```
RAG/
├── .env                            # Secrets (GROQ_API_KEY=xxx)
├── .gitignore                      # Git ignore rules
├── pyproject.toml                  # Dependencies & project metadata
├── main.py                         # 🚀 Entry point for the server
├── README.md                       # This file
│
├── api/                            # ⚙️ FastAPI Backend
│   ├── main.py                     # App creation + static mounting
│   ├── routes.py                   # API endpoints
│   └── schemas.py                  # Pydantic request/response models
│
├── ui/                             # 🖥️ Vanilla HTML/CSS/JS Frontend
│   ├── index.html                  # Main UI page
│   └── static/
│       ├── css/style.css           # Custom glassmorphic styling
│       └── js/app.js               # UI logic and API fetching
│
├── src/                            # 🔧 Core RAG Engine
│   ├── config.py                   # Centralized configuration
│   ├── ingestion/                  # PDF Parsing (legal-aware)
│   ├── processing/                 # Document Chunking
│   ├── embeddings/                 # SentenceTransformer wrapping
│   ├── vectorstore/                # ChromaDB management
│   ├── retrieval/                  # Semantic search engine
│   └── generation/                 # LLM Prompts & Clients
│
├── scripts/
│   └── ingest_legal_docs.py        # Pipeline execution script
│
└── data/
    ├── legal_acts/                 # Place your PDFs here
    └── vector_store/               # ChromaDB storage (auto-created)
```

## ⚠️ Disclaimer

**This is AI-generated legal information for educational purposes only.** It is not a substitute for professional legal advice. For specific legal guidance, please consult a qualified lawyer or visit your nearest District Legal Services Authority (DLSA) for free legal aid.
