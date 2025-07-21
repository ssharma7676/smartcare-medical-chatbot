"""
Pinecone index creation and data upload script.
Creates a new Pinecone index and uploads medical data embeddings.
Used for initial setup of the vector database for the medical chatbot.
"""

from src.helper import load_pdf_file, text_split, download_hugging_face_embeddings
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Get Pinecone API key
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY

# Process and prepare data
extracted_data = load_pdf_file(data='Data/')
text_chunks = text_split(extracted_data)
embeddings = download_hugging_face_embeddings()

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)

# Index configuration
index_name = "medical-chatbot"

# Create Pinecone index
pc.create_index(
    name=index_name,
    dimension=384,
    metric="cosine", 
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    )
)

# Upload documents to Pinecone
docsearch = PineconeVectorStore.from_documents(
    documents=text_chunks,
    index_name=index_name,
    embedding=embeddings,
)