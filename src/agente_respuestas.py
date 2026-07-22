import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Importamos CrossEncoder de forma nativa
from sentence_transformers import CrossEncoder

# 1. Cargar las variables de entorno
load_dotenv()

if not os.environ.get("OPENAI_API_KEY"):
    raise ValueError("⚠️ No se encontró OPENAI_API_KEY en el archivo .env")

# Cargamos el modelo de Reranking globalmente
print("Cargando modelo de Reranking...")
cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def cargar_modelos():
    print("Cargando embeddings...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    db = Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    
    print("Cargando modelo de Reranking...")
    cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    
    return db, cross_encoder

def hacer_pregunta(db, cross_encoder, pregunta_original):

    entrada_limpia = pregunta_original.lower().strip().replace("!", "").replace("¡", "").replace("?", "").replace("¿", "")
    saludos_y_cortesias = ["hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "saludos", "hey", "gracias", "muchas gracias", "ok", "vale", "entendido"]
    
    if entrada_limpia in saludos_y_cortesias:
        if "gracias" in entrada_limpia:
            return "¡De nada! Estoy aquí para ayudarte. ¿Tienes alguna otra duda sobre los manuales de Santo Pegasus?"
        else:
            return "¡Hola! Soy el asistente virtual de Santo Pegasus.\n\n¿En qué te puedo ayudar hoy con nuestras políticas, manuales técnicos o arquitectura?"
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # ==========================================
    # PASO 1: EXPANSIÓN DE CONSULTA (Query Rewriting)
    # ==========================================
    rewrite_prompt = ChatPromptTemplate.from_template(
        "Eres un experto en bases de conocimiento corporativas. "
        "Tu tarea es tomar la pregunta coloquial de un usuario y reescribirla "
        "para que use vocabulario técnico, sea clara y sea ideal para buscar en una base de datos vectorial.\n"
        "Pregunta original: {pregunta}\n"
        "Pregunta optimizada:"
    )
    
    rewriter_chain = rewrite_prompt | llm | StrOutputParser()
    pregunta_mejorada = rewriter_chain.invoke({"pregunta": pregunta_original})

    # ==========================================
    # PASO 2: RECUPERACIÓN AMPLIA
    # ==========================================
    retriever_base = db.as_retriever(search_kwargs={"k": 15})
    docs_candidatos = retriever_base.invoke(pregunta_mejorada)

    # ==========================================
    # PASO 3: RECLASIFICACIÓN NATIVA (Reranking)
    # ==========================================
    pares_evaluacion = [[pregunta_mejorada, doc.page_content] for doc in docs_candidatos]
    puntajes = cross_encoder.predict(pares_evaluacion)
    
    docs_con_puntajes = list(zip(docs_candidatos, puntajes))
    docs_con_puntajes.sort(key=lambda x: x[1], reverse=True)
    
    mejores_docs = [doc for doc, score in docs_con_puntajes[:4]]

    contexto_texto = "\n\n".join(
        [f"[Fuente: {d.metadata.get('fuente', 'Desconocida')} | Sección: {d.metadata.get('Header 2', 'General')}]\n{d.page_content}" 
         for d in mejores_docs]
    )

    # ==========================================
    # PASO 4: RESPUESTA FINAL
    # ==========================================
    system_prompt = (
        "Eres el asistente virtual corporativo de Santo Pegasus Soluciones, una empresa de tecnología especializada en el desarrollo de productos digitales para el sector de salud y servicios profesionales.\n"
        "Responde a la pregunta del usuario basándote ÚNICAMENTE en el contexto proporcionado.\n\n"
        "Reglas estrictas:\n"
        "1. Si el contexto contiene la respuesta, respóndela de forma clara y directa.\n"
        "2. Si respondes usando el contexto, DEBES agregar al final una cita obligatoria con este formato: [Fuente: <Nombre del documento> | Sección: <Nombre de la sección>].\n"
        "3. Si te preguntan qué es Santo Pegasus o quién eres, usa tu conocimiento base para responder amablemente sin necesidad de citar documentos.\n"
        "4. Si el contexto NO contiene la respuesta a otras preguntas operativas, tu única respuesta debe ser exactamente: 'No encontré esta información en los documentos disponibles.' No agregues nada más.\n\n"
        "Contexto recuperado:\n{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    qa_chain = prompt | llm | StrOutputParser()
    
    respuesta = qa_chain.invoke({"context": contexto_texto, "input": pregunta_original})

    # RETORNAMOS LA RESPUESTA PARA QUE STREAMLIT LA USE
    return respuesta