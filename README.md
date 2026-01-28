# CodeGraph

AI-powered code understanding system that answers questions about any codebase by navigating its actual structure.

## Features

- 🔍 **Graph-based navigation** - Treats code as an interconnected system
- 🧠 **Multi-hop reasoning** - Follows chains of logic across files
- 📝 **Verifiable answers** - Every claim backed by code citations
- 🎨 **Interactive visualization** - Explore code relationships visually
- 🔌 **LLM agnostic** - Works with OpenAI, Anthropic, Groq, and more

## Quick Start

### Prerequisites

- Docker & Docker Compose
- API key for at least one LLM provider

### Setup

1. Clone and configure:
```bash
cp .env.example .env
# Edit .env with your API keys
```

2. Start all services:
```bash
docker compose up --build
```

3. Open http://localhost:3000

### Development Mode

**Backend only:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend only:**
```bash
cd frontend
npm install
npm run dev
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React UI  │────▶│   FastAPI   │────▶│  LLM APIs   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ NetworkX │ │ ChromaDB │ │ Postgres │
        │  Graph   │ │ Vectors  │ │ Metadata │
        └──────────┘ └──────────┘ └──────────┘
```

## License

MIT
