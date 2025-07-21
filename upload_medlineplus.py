"""
MedlinePlus data upload script.
Parses MedlinePlus XML data, chunks the content, and uploads to Pinecone.
Creates embeddings for medical information from MedlinePlus health topics.
"""

from dotenv import load_dotenv
load_dotenv()

import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Load and parse the XML file
tree = ET.parse('Data/medlineplus/HealthTopics.xml')
root = tree.getroot()

topics = []
for topic in root.findall('health-topic'): 
    title = topic.attrib.get('title')
    url = topic.attrib.get('url')
    summary_elem = topic.find('full-summary')
    if summary_elem is not None:
        # Unescape HTML and strip tags
        html_summary = summary_elem.text or ""
        text_summary = BeautifulSoup(html_summary, "html.parser").get_text(separator="\n")
    else:
        text_summary = ""
    topics.append({
        "title": title,
        "url": url,
        "summary": text_summary
    })

print(f"Extracted {len(topics)} topics.")

# Chunk the summaries
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
all_chunks = []
for topic in topics:
    docs = splitter.create_documents([topic["summary"]])
    for i, doc in enumerate(docs):
        # Add metadata for attribution
        doc.metadata = {
            "source": topic["url"],
            "title": topic["title"],
            "source_name": "MedlinePlus"
        }
        all_chunks.append(doc)

print(f"Total chunks created: {len(all_chunks)}")

# Ebed and upsert to pinecone
from langchain_pinecone import PineconeVectorStore
from src.helper import download_hugging_face_embeddings

embeddings = download_hugging_face_embeddings()
index_name = "medical-chatbot"
docsearch = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings
)
docsearch.add_documents(all_chunks, namespace="medlineplus")
print("MedlinePlus chunks uploaded to Pinecone under 'medlineplus namespace.")