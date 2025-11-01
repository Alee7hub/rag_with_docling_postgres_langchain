from langchain.tools import tool
from langchain_postgres import PGVector
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# initiate embeddings model
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Connection string
CONNECTION_STRING = "postgresql+psycopg://raguser:ragpass@localhost:5555/ragdb"

# Initialize vector store
vectorstore = PGVector(
    connection=CONNECTION_STRING,
    embeddings=embeddings,
    collection_name="my_documents",  # table name
    use_jsonb=True,
)

@tool(response_format="content_and_artifact")
def retrieve_context(query: str):
    """Retrieve information to help answer a query."""
    retrieved_docs = vectorstore.similarity_search(query, k=3)
    serialized = "\n\n".join(
        (f"Source: {doc.metadata}\nContent: {doc.page_content}")
        for doc in retrieved_docs
    )
    return serialized, retrieved_docs