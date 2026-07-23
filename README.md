# 🤖 AluraAgente - ONE IA FOR TECH | Santo Pegasus

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)
![Pinecone](https://img.shields.io/badge/Pinecone-000000?style=for-the-badge&logo=pinecone&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)

## 📌 Project Overview

This project is the solution to the **AluraAgente Challenge** for building a corporate virtual assistant. It implements an advanced **RAG (Retrieval-Augmented Generation)** architecture to answer employee questions based strictly on the internal knowledge base of *Santo Pegasus Soluciones*.

> **🚀 Live Demo:** You can test the application live in production here: [https://santo-pegasus-ai.onrender.com/](https://santo-pegasus-ai.onrender.com/)

---

## 🎯 Project Goal

Centralize information from Human Resources, Software Architecture, and Security, allowing employees to make queries in natural language. The system ensures accurate answers, mitigation of hallucinations, and explicit citation of the official documents used as sources.

---

## 🏗️ System Architecture (RAG Pipeline)

The project is designed following generative AI best practices:

1. **Structural Extraction and Chunking:**
   Markdown documents (`.md`) are processed using `MarkdownHeaderTextSplitter` to preserve the semantic coherence of tables and logical sections, avoiding blind text cuts.
2. **Vector Indexing & Cloud Storage:**
   Text fragments are transformed into high-performance vector embeddings via OpenAI (`text-embedding-3-small`) and stored securely in **Pinecone (Cloud Vector Database)** for rapid retrieval.
3. **Query Expansion (Query Rewriting):**
   Colloquial user queries go through a rewriting phase with the LLM to optimize technical vocabulary before searching the database.
4. **Direct Context Retrieval:**
   The retriever queries the cloud index to fetch the most relevant documentation chunks dynamically.
5. **Safe Response Generation:**
   OpenAI (`gpt-4o-mini`) is used with strict *System Prompts* and *Conversational Bypass* (Intent Routing) to avoid unnecessary searches on basic greetings and to ensure the AI admits when it doesn't have the information, appending mandatory source citations.

---

## 🛠️ Tech Stack

* **Base Language:** Python 3.10+
* **LLM & Embeddings:** OpenAI (`gpt-4o-mini`, `text-embedding-3-small`)
* **RAG Framework:** LangChain
* **Vector Database:** Pinecone (Cloud)
* **Frontend Interface:** Streamlit
* **Containerization & Deployment:** Docker & Render

---

## 🚀 How to Run the Project Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/tu-usuario/santos-pegasus-ai.git
   cd santos-pegasus-ai
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:** Create a `.env` file in the project root and add your API Keys:
   ```env
   OPENAI_API_KEY=sk-YOUR_OPENAI_API_KEY
   PINECONE_API_KEY=pc-YOUR_PINECONE_API_KEY
   ```

5. **Run the web interface:**
   ```bash
   streamlit run src/app.py
   ```

---

Developed for the AluraAgente Challenge - ONE AI FOR TECH.
