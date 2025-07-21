"""
SmartCare Medical Chatbot
A Flask-based AI medical assistant with multi-source retrieval from MedlinePlus, Mayo Clinic, and Gale Encyclopedia.
"""

# =============================================================================
# IMPORTS
# =============================================================================

# Flask and authentication
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

# LangChain and AI components
from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain_pinecone import PineconeVectorStore
from src.helper import download_hugging_face_embeddings

# Utilities
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
import json

# =============================================================================
# CONFIGURATION
# =============================================================================

# Load environment variables
load_dotenv()

# Flask app configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# API Keys
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
os.environ["PINECONE_API_KEY"] = PINECONE_API_KEY
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

# =============================================================================
# DATABASE MODELS
# =============================================================================

class User(UserMixin, db.Model):
    """User model for authentication and user management."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Message(db.Model):
    """Message model for storing chat history with source attribution."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender = db.Column(db.String(10), nullable=False)  # 'user' or 'bot'
    text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    conversation_id = db.Column(db.String(50), nullable=False, default=lambda: str(datetime.now().timestamp()))
    sources = db.Column(db.Text, nullable=True)  # Store source URLs as JSON string
    
    def get_local_time_simple(self):
        """Return the timestamp as is (already in local time)."""
        return self.timestamp

# =============================================================================
# AI COMPONENTS SETUP
# =============================================================================

# Initialize embeddings and vector stores
embeddings = download_hugging_face_embeddings()
index_name = "medical-chatbot"

# === Gale Encyclopedia and Mayo Clinic integration is commented out for public release ===
# === To enable, ensure you have the rights to use these sources and uncomment below. ===
# docsearch_default = PineconeVectorStore.from_existing_index(
#     index_name=index_name,
#     embedding=embeddings,
#     namespace=""  # Default namespace (Gale Encyclopedia)
# )
# docsearch_mayo = PineconeVectorStore.from_existing_index(
#     index_name=index_name,
#     embedding=embeddings,
#     namespace="mayo_clinic"  # Mayo Clinic namespace
# )

# Only MedlinePlus (public domain) is active
# MedlinePlus vector store
# (See README for how to add your own sources)
docsearch_medlineplus = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embeddings,
    namespace="medlineplus"  # MedlinePlus namespace
)

# === Gale Encyclopedia and Mayo Clinic retrievers are commented out for public release ===
# retriever_default = docsearch_default.as_retriever(
#     search_type="similarity", 
#     search_kwargs={"k": 4}
# )
# retriever_mayo = docsearch_mayo.as_retriever(
#     search_type="similarity", 
#     search_kwargs={"k": 4}
# )

# Only MedlinePlus retriever is active
retriever_medlineplus = docsearch_medlineplus.as_retriever(
    search_type="similarity", 
    search_kwargs={"k": 4}
)

# Initialize LLM
llm = ChatGroq(
    groq_api_key=os.environ["GROQ_API_KEY"],
    model_name="llama3-8b-8192"
)

# =============================================================================
# PROMPT TEMPLATE IMPORT
# =============================================================================
from src.prompt import multi_source_prompt

# Create the QA chain
qa_chain = LLMChain(llm=llm, prompt=multi_source_prompt)

# =============================================================================
# CORE AI FUNCTIONS
# =============================================================================

def get_multi_source_context(question):
    """
    Retrieve context from multiple medical sources and merge them intelligently.
    Gale Encyclopedia and Mayo Clinic retrieval is commented out for public release.
    Only MedlinePlus (public domain) is active.
    """
    try:
        # === The following lines are commented out for public release ===
        # docs_default = retriever_default.get_relevant_documents(question)
        # docs_mayo = retriever_mayo.get_relevant_documents(question)
        # docs_medlineplus = retriever_medlineplus.get_relevant_documents(question)
        # print(f"Retrieved {len(docs_default)} docs from Gale, {len(docs_mayo)} from Mayo, {len(docs_medlineplus)} from MedlinePlus")
        #
        # Debug: Print metadata for first few docs from each source
        # if docs_medlineplus:
        #     print(f"First MedlinePlus doc metadata: {docs_medlineplus[0].metadata}")
        # if docs_mayo:
        #     print(f"First Mayo doc metadata: {docs_mayo[0].metadata}")
        # if docs_default:
        #     print(f"First Gale doc metadata: {docs_default[0].metadata}")
        #
        # Combine and deduplicate content
        # all_docs = docs_default + docs_mayo + docs_medlineplus
        #
        # Create a merged context with source attribution
        # context_parts = []
        # all_sources = []  # Track all available sources
        #
        # if docs_default:
        #     context_parts.append("GALE ENCYCLOPEDIA SOURCES:")
        #     for i, doc in enumerate(docs_default[:2]):  # Top 2 from Gale
        #         context_parts.append(f"Source {i+1}: {doc.page_content[:300]}...")
        #         if hasattr(doc, 'metadata') and 'source' in doc.metadata:
        #             all_sources.append({
        #                 'type': 'Gale Encyclopedia',
        #                 'url': doc.metadata['source'],
        #                 'content': doc.page_content[:100]  # First 100 chars for matching
        #             })
        #
        # if docs_mayo:
        #     context_parts.append("\nMAYO CLINIC SOURCES:")
        #     for i, doc in enumerate(docs_mayo[:2]):  # Top 2 from Mayo
        #         context_parts.append(f"Source {i+1}: {doc.page_content[:300]}...")
        #         if hasattr(doc, 'metadata') and 'source' in doc.metadata:
        #             all_sources.append({
        #                 'type': 'Mayo Clinic',
        #                 'url': doc.metadata['source'],
        #                 'content': doc.page_content[:100]  # First 100 chars for matching
        #             })

        # Only MedlinePlus retrieval is active
        docs_medlineplus = retriever_medlineplus.get_relevant_documents(question)
        print(f"Retrieved {len(docs_medlineplus)} docs from MedlinePlus")

        context_parts = []
        all_sources = []

        # === The following block is the only active source for public release ===
        if docs_medlineplus:
            context_parts.append("MEDLINEPLUS SOURCES:")
            for i, doc in enumerate(docs_medlineplus[:2]):  # Top 2 from MedlinePlus
                context_parts.append(f"Source {i+1}: {doc.page_content[:300]}...")
                if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                    title = doc.metadata.get('title', 'Unknown Topic')
                    all_sources.append({
                        'type': 'MedlinePlus',
                        'url': doc.metadata['source'],
                        'title': title,
                        'content': doc.page_content[:100]
                    })
        print(f"Total sources collected: {len(all_sources)}")
        return "\n".join(context_parts), all_sources
    except Exception as e:
        print(f"Error retrieving context: {e}")
        # === Fallback to single source (commented out for public release) ===
        # try:
        #     docs = retriever_default.get_relevant_documents(question)
        #     all_sources = []
        #     for doc in docs[:3]:
        #         if hasattr(doc, 'metadata') and 'source' in doc.metadata:
        #             all_sources.append({
        #                 'type': 'Gale Encyclopedia',
        #                 'url': doc.metadata['source'],
        #                 'content': doc.page_content[:100]
        #             })
        #     return "\n".join([doc.page_content[:300] for doc in docs[:3]]), all_sources
        # except:
        return "", []

def extract_used_sources(response, all_sources):
    """
    Determine which sources were actually used in the response and filter out conversational responses.
    
    Args:
        response (str): The AI's response
        all_sources (list): List of available sources
        
    Returns:
        list: Filtered list of sources to display
    """
    # Filter out sources for conversational responses
    conversational_phrases = [
        "hi", "hello", "hey", "how can i help", "you're welcome", 
        "take care", "great", "ok", "sounds good", "thank you",
        "pleasure chatting", "feel free to ask", "any new questions",
        "any concerns", "free to ask", "medical questions"
    ]
    
    response_lower = response.lower().strip()
    
    # Check if response is primarily conversational
    conversational_count = 0
    for phrase in conversational_phrases:
        if phrase in response_lower:
            conversational_count += 1
    
    # If response contains multiple conversational phrases or is short and conversational
    if conversational_count >= 2 or (conversational_count >= 1 and len(response_lower) < 100):
        print(f"Conversational response detected: '{response}' - no sources shown")
        return []
    
    # Show only the top 2 unique sources by URL, preserving order
    if not all_sources:
        print("No sources found for attribution.")
        return []
    
    print(f"All sources before filtering: {all_sources}")
    
    # Prioritize MedlinePlus sources (public domain, most trustworthy)
    medlineplus_sources = []
    other_sources = []
    
    for source in all_sources:
        if source.get('type') == 'MedlinePlus':
            medlineplus_sources.append(source)
        else:
            other_sources.append(source)
    
    # Combine: MedlinePlus first, then others
    prioritized_sources = medlineplus_sources + other_sources
    
    unique_sources = []
    seen = set()
    seen_medlineplus = False  # Track if we've already added a MedlinePlus source
    
    for source in prioritized_sources:
        url = source.get('url')
        source_type = source.get('type', 'Unknown')
        
        if url and url not in seen:
            # For MedlinePlus, only add the first one
            if source_type == 'MedlinePlus' and seen_medlineplus:
                continue
                
            seen.add(url)
            if source_type == 'MedlinePlus':
                seen_medlineplus = True
                
            source_name = extract_source_name(url, source.get('title'))
            unique_sources.append({
                'type': source_type,
                'name': source_name,
                'url': url
            })
        if len(unique_sources) >= 2:
            break
    
    print(f"Final sources selected: {unique_sources}")
    return unique_sources

def extract_source_name(url, title_from_metadata=None):
    """
    Extract a readable source name from URL or metadata.
    
    Args:
        url (str): The source URL
        title_from_metadata (str, optional): Title from document metadata
        
    Returns:
        str: Human-readable source name
    """
    if 'medlineplus.gov' in url:
        # Use the title from metadata if available (much more reliable)
        if title_from_metadata and title_from_metadata != 'Unknown Topic':
            return f"MedlinePlus - {title_from_metadata}"
        else:
            # Just show "MedlinePlus" without any title text
            return "MedlinePlus"
    # === Mayo Clinic and Gale Encyclopedia logic is commented out for public release ===
    # elif 'mayoclinic.org' in url:
    #     # Extract condition name from Mayo Clinic URL
    #     if '/diseases-conditions/' in url:
    #         condition = url.split('/diseases-conditions/')[1].split('/')[0]
    #         return f"Mayo Clinic - {condition.replace('-', ' ').title()}"
    #     return "Mayo Clinic"
    # elif 'gale' in url.lower() or 'encyclopedia' in url.lower():
    #     return "Gale Encyclopedia of Medicine"
    else:
        # Fallback: use domain name
        from urllib.parse import urlparse
        try:
            domain = urlparse(url).netloc
            return domain.replace('www.', '').title()
        except:
            return "Medical Source"

# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login."""
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration endpoint."""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists')
            return redirect(url_for('register'))
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password, 'pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login endpoint."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password, password):
            flash('Incorrect email or password')
            return redirect(url_for('login'))
        
        login_user(user)
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout endpoint."""
    logout_user()
    flash('Logged out successfully!')
    return redirect(url_for('login'))

# =============================================================================
# MAIN APPLICATION ROUTES
# =============================================================================

@app.route("/")
@login_required
def index():
    """Main chat interface."""
    # Get current conversation ID from session, or create a new one
    current_conversation = session.get('current_conversation_id')
    if not current_conversation:
        current_conversation = str(datetime.now().timestamp())
        session['current_conversation_id'] = current_conversation
    
    # Fetch messages only from the current conversation
    recent_messages = (
        Message.query
        .filter_by(user_id=current_user.id, conversation_id=current_conversation)
        .order_by(Message.timestamp.asc())
        .all()
    )
    
    return render_template('chat.html', messages=recent_messages)

@app.route("/get", methods=["GET", "POST"])
@login_required
def chat():
    """Main chat endpoint for processing user messages."""
    if request.method == "POST":
        msg = request.form.get("msg")
        if not msg:
            return "Error: No message received.", 400

        # Get current conversation ID
        current_conversation = session.get('current_conversation_id')
        if not current_conversation:
            current_conversation = str(datetime.now().timestamp())
            session['current_conversation_id'] = current_conversation

        # Save user message
        user_msg = Message(user_id=current_user.id, sender='user', text=msg, conversation_id=current_conversation)
        db.session.add(user_msg)
        db.session.commit()

        # Fetch recent conversation history for context
        N = 6
        recent_messages = (
            Message.query
            .filter_by(user_id=current_user.id, conversation_id=current_conversation)
            .order_by(Message.timestamp.desc())
            .limit(N)
            .all()
        )
        recent_messages = list(reversed(recent_messages))

        # Format chat history as a readable string
        chat_history = ""
        for m in recent_messages:
            sender = current_user.username if m.sender == 'user' else "SmartCare"
            chat_history += f"{sender}: {m.text}\n"

        # Get relevant context from vector store
        context, all_sources = get_multi_source_context(msg)
        
        # Debug: Print what context is being retrieved
        print(f"User message: {msg}")
        print(f"Retrieved context: {context[:200]}...")  # First 200 chars
        print(f"Chat history: {chat_history[:200]}...")  # First 200 chars

        # Generate AI response
        result = qa_chain.run({"context": context, "question": msg, "chat_history": chat_history})
        response = result
        
        # Debug: Print the response
        print(f"Bot response: {response[:200]}...")  # First 200 chars

        # Determine which sources were actually used in the response
        used_sources = extract_used_sources(response, all_sources)

        # Deduplicate sources by URL before storing
        if used_sources:
            seen_urls = set()
            unique_sources = []
            for source in used_sources:
                if source['url'] not in seen_urls:
                    seen_urls.add(source['url'])
                    unique_sources.append(source)
            used_sources = unique_sources

        # Store bot message with sources
        sources_json = json.dumps(used_sources) if used_sources else None
        bot_msg = Message(
            user_id=current_user.id, 
            sender='bot', 
            text=response, 
            conversation_id=current_conversation,
            sources=sources_json
        )
        db.session.add(bot_msg)
        db.session.commit()

        return jsonify({"response": response, "sources": used_sources})
    else:
        return "Please use POST to send messages.", 405

@app.route("/get_sources/<int:message_id>")
@login_required
def get_sources(message_id):
    """Get sources for a specific message."""
    message = Message.query.filter_by(id=message_id, user_id=current_user.id).first()
    if not message or not message.sources:
        return jsonify({"sources": []})
    
    try:
        sources = json.loads(message.sources)
        
        # Deduplicate sources by URL
        if sources:
            seen_urls = set()
            unique_sources = []
            for source in sources:
                if source['url'] not in seen_urls:
                    seen_urls.add(source['url'])
                    unique_sources.append(source)
            sources = unique_sources
        
        return jsonify({"sources": sources})
    except:
        return jsonify({"sources": []})

# =============================================================================
# HISTORY AND UTILITY ROUTES
# =============================================================================

@app.route("/history")
@login_required
def history():
    """Display chat history for the current user."""
    messages = (
        Message.query
        .filter_by(user_id=current_user.id)
        .order_by(Message.timestamp.desc())
        .all()
    )
    return render_template('history.html', messages=messages)

@app.route("/clear_history", methods=["POST"])
@login_required
def clear_history():
    """Clear all chat history for the current user."""
    try:
        # Delete all messages for the current user
        Message.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/clear_chat", methods=["POST"])
@login_required
def clear_chat():
    """Start a new conversation by creating a new conversation ID."""
    new_conversation_id = str(datetime.now().timestamp())
    session['current_conversation_id'] = new_conversation_id
    return jsonify({"status": "success", "message": "Chat cleared"})

# =============================================================================
# APPLICATION ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5050, debug=True)