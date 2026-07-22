# 🤖 AluraAgente - ONE IA FOR TECH | Santo Pegasus

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=chainlink&logoColor=white)
![Hugging Face](https://img.shields.io/badge/Hugging_Face-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![SQLite](https://img.shields.io/badge/ChromaDB-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Oracle Cloud](https://img.shields.io/badge/Oracle_Cloud-F80000?style=for-the-badge&logo=oracle&logoColor=white)

## 📌 Project Overview

This project is the solution to the **AluraAgente Challenge** for building a corporate virtual assistant. It implements an advanced **RAG (Retrieval-Augmented Generation)** architecture to answer employee questions based strictly on the internal knowledge base of *Santo Pegasus Soluciones*.

---

## 🎯 Project Goal

Centralize information from Human Resources, Software Architecture, and Security, allowing employees to make queries in natural language. The system ensures accurate answers, mitigation of hallucinations, and explicit citation of the official documents used as sources.

---

## 🏗️ System Architecture (RAG Pipeline)

The project is designed following generative AI best practices:

1. **Structural Extraction and Chunking:**
   Markdown documents (`.md`) are processed using `MarkdownHeaderTextSplitter` to preserve the semantic coherence of tables and logical sections, avoiding blind text cuts.
2. **Vector Indexing (Embeddings):**
   Text fragments are transformed into vectors using the multilingual model `paraphrase-multilingual-MiniLM-L12-v2` and stored locally in **ChromaDB**.
3. **Query Expansion (Query Rewriting):**
   Colloquial user queries go through a rewriting phase with the LLM to optimize technical vocabulary before searching the database.
4. **Native Reranking:**
   A broad search ($K=15$) is performed and then filtered using a Cross-Encoder (`ms-marco-MiniLM-L-6-v2`) via `sentence-transformers`, ensuring the LLM only receives the top 4 most relevant fragments.
5. **Safe Response Generation:**
   OpenAI (`gpt-4o-mini`) is used with strict *System Prompts* and *Conversational Bypass* (Intent Routing) to avoid unnecessary searches on basic greetings and to ensure the AI admits when it doesn't have the information.

---

## 🛠️ Tech Stack

* **Base Language:** Python 3.10+
* **LLM Models:** OpenAI (`gpt-4o-mini`)
* **RAG Framework:** LangChain
* **Embeddings & Reranking:** HuggingFace / Sentence-Transformers
* **Vector Database:** ChromaDB
* **Frontend:** Streamlit
* **Deployment:** Docker & Oracle Cloud Infrastructure (OCI)

---

## 🚀 How to Run the Project Locally

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/tu-usuario/santos-pegasus-ai.git](https://github.com/tu-usuario/santos-pegasus-ai.git)
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

4. **Set up environment variables:** Create a `.env` file in the project root and add your OpenAI API Key:
   ```
   OPENAI_API_KEY=sk-YOUR_API_KEY
   ```

5. **Run the web interface:**
   ```bash
   streamlit run src/app.py
   ```

---

Developed for the AluraAgente Challenge - ONE AI FOR TECH.
