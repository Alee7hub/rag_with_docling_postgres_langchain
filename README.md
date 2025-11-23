# Agentic RAG Application with Docling, LangChain & PostgreSQL

An educational agentic RAG (Retrieval-Augmented Generation) application that demonstrates document parsing, vector storage, and intelligent question-answering using modern AI tools.

## 🎯 Overview

This project showcases a complete RAG pipeline that:
- **Parses** various document formats (PDF, Markdown, DOCX, HTML, TXT) using [Docling](https://github.com/DS4SD/docling)
- **Chunks** documents intelligently using hybrid chunking with context preservation
- **Stores** embeddings in PostgreSQL with pgvector extension
- **Retrieves** relevant context using semantic search
- **Answers** questions through a LangChain agent powered by OpenAI's GPT models

## 🏗️ Architecture

```
User Query → LangChain Agent → Retrieval Tool → PGVector (PostgreSQL) → Context → GPT Model → Response
```

**Key Components:**
- **Docling**: Advanced document parser supporting multiple formats
- **LangChain**: Framework for building the agent and orchestrating RAG workflow
- **PostgreSQL + pgvector**: Vector database running in Docker
- **OpenAI**: Embeddings (text-embedding-3-small) and LLM (gpt-4o-mini)

## 📋 Prerequisites

- **Python**: 3.13 or higher
- **Docker**: For running PostgreSQL with pgvector
- **OpenAI API Key**: For embeddings and language model
- **Poetry** or **uv**: For dependency management (recommended)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd langchain_docling_postgres
```

### 2. Set Up Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```bash
# Required
OPENAI_API_KEY="your-openai-api-key-here"

# Path to your raw documents directory
RAW_DOCUMENTS_DIR="documents/raw"

# PostgreSQL Configuration
POSTGRES_USER=raguser
POSTGRES_PASSWORD=ragpass
POSTGRES_DB=ragdb
POSTGRES_PORT=5555

# Optional: LangSmith for tracing
LANGSMITH_TRACING=true
LANGSMITH_API_KEY="your-langsmith-api-key-here"
LANGSMITH_PROJECT="your-project-name"
```

### 3. Install Dependencies

Using **uv** (recommended):
```bash
uv sync
```

Or using **pip**:
```bash
pip install -r requirements.txt
```

Or using **Poetry**:
```bash
poetry install
```

### 4. Start PostgreSQL with pgvector

```bash
docker-compose up -d
```

Verify the container is running:
```bash
docker ps
```

### 5. Enable pgvector Extension

Connect to the database and enable the pgvector extension:

```bash
docker exec -it <container_name> psql -U raguser -d ragdb -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

Replace `<container_name>` with your actual container name (find it using `docker ps`).

### 6. Process and Load Documents

The project includes sample documents in `documents/raw/`. To process and load them into the vector store, simply run:

```bash
python load_chunk_embed_ingest.py

# or
uv run load_chunk_embed_ingest.py
```

This automated script will:
1. Read all documents from the directory specified in `RAW_DOCUMENTS_DIR` (default: `documents/raw/`)
2. Parse documents using Docling (supports PDF, MD, DOCX, HTML, TXT, etc.)
3. Chunk them using Docling's HybridChunker with context preservation
4. Generate embeddings using OpenAI's text-embedding-3-small
5. Store everything in PostgreSQL/pgvector

**Alternative: Using Jupyter Notebook** (recommended for learning and experimentation)

If you want to understand the process step-by-step or experiment with parameters, take a look at:

```bash
notebooks/docling_test.ipynb
notebooks/load_chunk_to_langchain_docs.py
notebooks/load_chunk_embed_ingest_test.ipynb
```

These notebooks provide the same functionality with detailed explanations and the ability to inspect intermediate results.

### 7. Run the Application

```bash
python main.py

# or
uv run main.py
```

You'll see an interactive prompt where you can ask questions about your documents:

```
============================================================
Welcome to the Agentic RAG Application!
============================================================
Ask questions about your financial documents and reports.
Type 'exit' or 'quit' to end the session.

Your question: What is the mission of the company?
```

## 📁 Project Structure

```
langchain_docling_postgres/
├── main.py                      # Entry point - interactive CLI
├── agent.py                     # LangChain agent configuration
├── tools.py                     # RAG retrieval tool definition
├── load_chunk_embed_ingest.py   # Document processing & embedding script
├── docker-compose.yml           # PostgreSQL + pgvector setup
├── pyproject.toml               # Project dependencies
├── requirements.txt             # pip dependencies
├── .env.example                 # Environment variables template
├── documents/
│   ├── raw/                     # Place your documents here
│   └── processed/               # Processed document outputs
└── notebooks/
    ├── docling_test.ipynb       # Document processing pipeline (interactive)
    └── ...                      # Other experimental notebooks
```

## 🔧 Configuration

### Database Connection

The vector store connection is configured in `tools.py`:

```python
CONNECTION_STRING = "postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:{POSTGRES_PORT}/{POSTGRES_DB}"
```

Update credentials if you changed them in `.env`.

### Chunking Parameters

Adjust chunking in `load_chunk_embed.py` by modifying the function call:

```python
all_chunks = process_documents_to_langchain(
    documents_dir=raw_docs_dir,
    max_tokens=512  # Adjust chunk size (default: 512)
)
```

Or edit the HybridChunker configuration within the function for more control:

```python
chunker = HybridChunker(
    tokenizer=tokenizer,
    max_tokens=512,  # Adjust chunk size
    merge_peers=True  # Merge related chunks
)
```

### Retrieval Parameters

Modify the number of retrieved documents in `tools.py`:

```python
retrieved_docs = vectorstore.similarity_search(query, k=3)  # Change k value
```

## 📝 Adding Your Own Documents

1. Place your documents (PDF, MD, DOCX, HTML, TXT, etc.) in `documents/raw/`
2. Ensure `RAW_DOCUMENTS_DIR` in `.env` points to the correct directory
3. Run the processing script:
   ```bash
   python load_chunk_embed_ingest.py

   # or
   uv run load_chunk_embed_ingest.py
   ```
4. Documents will be automatically parsed, chunked, embedded, and stored in PostgreSQL

## 🐛 Troubleshooting

### Database Connection Errors

**Error**: `password authentication failed`

**Solution**: Ensure you're using `psycopg` (v3), not `psycopg2`:
```bash
pip install psycopg
```

### Missing pgvector Extension

**Error**: `could not access file "$libdir/vector"`

**Solution**: Enable the extension:
```bash
docker exec -it <container_name> psql -U raguser -d ragdb -c "CREATE EXTENSION vector;"
```

### Version Incompatibility

**Error**: `database files are incompatible with server`

**Solution**: Clean the Docker volume and restart:
```bash
docker-compose down -v
docker-compose up -d
```

### Model Not Found

**Error**: Model `gpt-5-mini` not found

**Note**: Check `agent.py` - the model name might need updating to a valid OpenAI model like `gpt-4o-mini` or `gpt-3.5-turbo`.

## 📚 Learn More

- [Docling Documentation](https://github.com/DS4SD/docling)
- [LangChain Documentation](https://python.langchain.com/)
- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [OpenAI API Documentation](https://platform.openai.com/docs)

## 🤝 Contributing

This is an educational project. Feel free to fork, experiment, and learn!

## ✨ Acknowledgments

- Built with [Docling](https://github.com/DS4SD/docling) for document parsing
- Powered by [LangChain](https://github.com/langchain-ai/langchain)
- Vector storage with [pgvector](https://github.com/pgvector/pgvector)
