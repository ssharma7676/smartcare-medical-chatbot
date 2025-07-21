# SmartCare Medical Chatbot

SmartCare is a full-stack AI-powered medical chatbot that provides users with reliable, conversational health information. It integrates modern AI, semantic search, and a sleek interface to deliver an intuitive healthcare experience.

---

## ⚠️ Data Sources & Copyright

SmartCare is designed to work only with public domain medical sources.

- ✅ **MedlinePlus:** Included (public domain)
- 🚫 **Mayo Clinic & Gale Encyclopedia:** Not public domain — no data, code, or embeddings from these are included

> **Important:** Do not use or distribute non-public domain content with this project.

### Adding Your Own Data Sources
- Add your ingestion code to `src/`
- Update the retriever logic in `app.py`
- Refer to `upload_medlineplus.py` for a working example

---

## ✨ Features

- Conversational AI powered by Groq (or OpenAI, configurable)
- Multi-source retrieval with clickable source attributions
- User authentication (login, registration, session management)
- Contextual memory for more natural dialogue
- Chat history for revisiting past conversations
- Responsive UI built for clarity and accessibility
- Speech-to-text using the Web Speech API
- Text-to-speech playback for bot responses
- Clear chat functionality to start fresh conversations

---

## 🚀 Getting Started

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/smartcare-medical-chatbot.git
   cd smartcare-medical-chatbot
   ```
2. **Create and Activate a Virtual Environment**
   - macOS/Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   - Windows:
     ```bash
     python -m venv venv
     .\venv\Scripts\activate
     ```
3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Set Up Environment Variables**
   Create a `.env` file in the root directory:
   ```env
   PINECONE_API_KEY=your-pinecone-key
   GROQ_API_KEY=your-groq-key
   SECRET_KEY=your-flask-secret
   ```
5. **Initialize the Database**
   ```bash
   python recreate_db.py
   ```
6. **Upload MedlinePlus Data**
   ```bash
   python upload_medlineplus.py
   ```
7. **Launch the App**
   ```bash
   python app.py
   ```
   Visit: [http://localhost:5050](http://localhost:5050)

---

## 💬 How to Use

- Register or log in with your credentials
- Ask medical questions in the chat
- Click “Show sources” to view references
- Use the mic to speak, or the speaker icon to listen to responses
- Click “Clear Chat” to reset the conversation
- Visit “My History” to revisit past sessions

---

## 🛠️ Extend the Project

You can customize or expand SmartCare to fit your needs:
- Add custom ingestion logic (see `upload_medlineplus.py`)
- Modify the retrieval pipeline in `app.py` for new sources
- Swap or extend vector DBs (Pinecone, Chroma, etc.)

---

## 📄 License & Disclaimer

This project is for educational and demonstration purposes only.

- No copyrighted or proprietary data is included.
- Always consult a licensed medical professional for real medical advice. 