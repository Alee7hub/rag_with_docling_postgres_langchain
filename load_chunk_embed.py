import os
from pathlib import Path
from docling.document_converter import DocumentConverter
from langchain_core.documents import Document
from docling.chunking import HybridChunker
from transformers import AutoTokenizer
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# get raw documents directory from environment variable
raw_docs_dir = os.getenv("RAW_DOCUMENTS_DIR")

# PostgreSQL Configuration
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")

# Connection string
CONNECTION_STRING = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:{POSTGRES_PORT}/{POSTGRES_DB}"

# initiate embeddings model
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Function to process documents and return LangChain Document objects
def process_documents_to_langchain(documents_dir: str, max_tokens: int = 512):
    """Process multiple documents and return a list of LangChain Document objects.
    
    Docling automatically handles all supported file formats (.pdf, .md, .docx, .html, .txt, etc.)
    
    Args:
        documents_dir: Directory containing documents to process
        max_tokens: Maximum tokens per chunk
        
    Returns:
        List of LangChain Document objects with page_content and metadata
    """
    
    print("=" * 60)
    print("BATCH HYBRID CHUNKING - TO LANGCHAIN DOCUMENTS")
    print("=" * 60)
    
    # Get all files from directory (excluding directories)
    documents_path = Path(documents_dir)
    all_files = [f for f in documents_path.iterdir() if f.is_file()]
    all_files = sorted(all_files)  # Sort for consistent ordering
    
    if not all_files:
        print(f"\n✗ No files found in {documents_dir}")
        return []
    
    print(f"\nFound {len(all_files)} documents to process")
    print(f"Max tokens per chunk: {max_tokens}\n")
    
    # Initialize tokenizer once (reuse for all documents)
    print("Initializing tokenizer...")
    model_id = "sentence-transformers/all-MiniLM-L6-v2"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    # Create chunker once (reuse for all documents)
    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=max_tokens,
        merge_peers=True
    )
    
    langchain_documents = []
    total_chunks = 0
    successful_docs = 0
    failed_docs = []
    
    # Process each document
    for file_path in all_files:
        try:
            print(f"\n📄 Processing: {file_path.name}")
            
            # Convert document
            print("   Converting document...")
            converter = DocumentConverter()
            result = converter.convert(str(file_path))
            doc = result.document
            
            # Generate chunks
            print("   Generating chunks...")
            chunk_iter = chunker.chunk(dl_doc=doc)
            chunks = list(chunk_iter)
            
            print(f"   Creating {len(chunks)} LangChain Document objects...")
            
            # Convert each chunk to LangChain Document
            for i, chunk in enumerate(chunks):
                # Use contextualize to preserve headings and metadata
                contextualized_text = chunker.contextualize(chunk=chunk)
                
                # Create LangChain Document with metadata
                langchain_doc = Document(
                    page_content=contextualized_text,
                    metadata={
                        "source": str(file_path),
                        "source_name": file_path.name,
                        "chunk_index": total_chunks + i,
                        "document_chunk_index": i,
                        "total_chunks_in_document": len(chunks)
                    }
                )
                
                langchain_documents.append(langchain_doc)
            
            total_chunks += len(chunks)
            successful_docs += 1
            print(f"   ✓ Success! Total chunks so far: {total_chunks}")
            
        except Exception as e:
            print(f"   ✗ Error processing {file_path.name}: {e}")
            failed_docs.append(file_path.name)
    
    # Final summary
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"✓ Successfully processed: {successful_docs}/{len(all_files)} documents")
    print(f"✓ Total LangChain Documents created: {len(langchain_documents)}")
    
    if failed_docs:
        print(f"\n✗ Failed documents ({len(failed_docs)}):")
        for doc in failed_docs:
            print(f"   - {doc}")
    
    print("\n" + "=" * 60)
    print("LANGCHAIN DOCUMENTS READY")
    print("=" * 60)
    print("✓ Each chunk is a LangChain Document object")
    print("✓ page_content: Contextualized chunk text with headings")
    print("✓ metadata: source, source_name, chunk_index, etc.")
    print("✓ Ready for vector store ingestion (Chroma, FAISS, Pinecone, etc.)")
    
    return langchain_documents

# Initialize vector store
vectorstore = PGVector(
    connection=CONNECTION_STRING,
    embeddings=embeddings,
    collection_name="my_documents",  # table name
    use_jsonb=True,
)

if __name__ == "__main__":
    
    # Process documents and get LangChain Document objects
    all_chunks = process_documents_to_langchain(raw_docs_dir)

    # Add documents
    vectorstore.add_documents(all_chunks)
