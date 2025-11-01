# PostgreSQL + pgvector Setup Report

## Objective
Set up a containerized PostgreSQL database with pgvector extension as a vector store for a RAG application, with data persistence across container restarts.

## Initial Approach (Failed)
Started with a standard `postgres:15` image and attempted manual pgvector installation inside the container. This approach had critical flaws:
- Manual installations inside containers are ephemeral and lost on restart
- Required version-specific development packages
- Added unnecessary complexity

## Key Errors Encountered

### 1. Authentication Error
```
password authentication failed for user "raguser"
```
**Root cause**: Wrong psycopg driver version. LangChain's modern `PGVector` requires `psycopg` (v3), not `psycopg2`.

**Resolution**: 
- Changed connection string from `postgresql+psycopg2://` to `postgresql+psycopg://`
- Installed `psycopg` package instead of `psycopg2-binary`
- Used correct import: `from langchain_postgres import PGVector`

### 2. Schema Mismatch Error
```
column "id" of relation "langchain_pg_embedding" does not exist
```
**Root cause**: Pre-existing tables with incorrect schema.

**Resolution**: Dropped existing tables and let PGVector auto-create proper schema.

### 3. Missing Extension Error
```
could not access file "$libdir/vector": No such file or directory
```
**Root cause**: Manually installed pgvector was lost after container restart (ephemeral nature of containers).

**Resolution**: Switched to `pgvector/pgvector:pg16` image with pgvector pre-installed.

### 4. Database Incompatibility Error
```
database files are incompatible with server
The data directory was initialized by PostgreSQL version 15, which is not compatible with this version 16
```
**Root cause**: Volume contained Postgres 15 data, incompatible with Postgres 16.

**Resolution**: Removed volume with `docker-compose down -v` for clean initialization.

## Final Working Setup

### docker-compose.yml
```yaml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: raguser
      POSTGRES_PASSWORD: ragpass
      POSTGRES_DB: ragdb
    ports:
      - "5555:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  pgdata:
```

### Container Setup Commands
```bash
# Start container
docker-compose up -d

# Enable pgvector extension
docker exec -it <container_name> psql -U raguser -d ragdb -c "CREATE EXTENSION vector;"
```

### Python Integration
```python
from langchain_postgres import PGVector

CONNECTION_STRING = "postgresql+psycopg://raguser:ragpass@localhost:5555/ragdb"

vector_store = PGVector(
    embeddings=your_embedding_model,
    collection_name="my_documents",
    connection=CONNECTION_STRING,
    use_jsonb=True,
)

# Add documents
vector_store.add_documents(your_chunked_docs)

# Query top-k similar chunks
results = vector_store.similarity_search("user question", k=5)
```

### Required Python Packages
```bash
pip install langchain-postgres psycopg pgvector
```

## Key Learnings

1. **Use pre-built images**: `pgvector/pgvector` image eliminates manual installation hassles
2. **Driver compatibility matters**: Modern LangChain requires psycopg v3, not v2
3. **Volume persistence**: Data persists in Docker volumes, but must be compatible with image versions
4. **Clean slate approach**: When switching major versions, use `docker-compose down -v` to avoid conflicts
5. **Let libraries manage schema**: PGVector auto-creates necessary tables with correct structure

## Current Architecture
- **Application**: Runs locally (Python with Docling + LangChain)
- **Vector Store**: PostgreSQL 16 with pgvector in Docker container
- **Port**: Exposed on localhost:5555
- **Data Persistence**: Volume `pgdata` ensures data survives container restarts
- **Connection**: Application connects via psycopg3 driver to containerized database