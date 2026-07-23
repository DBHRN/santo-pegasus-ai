import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pathlib import Path

# Cargar variables de entorno apuntando a la raíz del proyecto
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("PINECONE_API_KEY"):
    raise ValueError("⚠️ Faltan llaves de API en el archivo .env")

def cargar_modelos():
    print("Cargando embeddings de OpenAI...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    # Conexión al índice en la nube de Pinecone
    index_name = "santo-pegasus-index"
    db = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings
    )
    
    # Retornamos solo la base de datos (eliminamos el cross_encoder para ahorrar memoria RAM)
    return db, None

def hacer_pregunta(db, pregunta_original):

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
    # PASO 2: RECUPERACIÓN DIRECTA DESDE PINECONE
    # ==========================================
    # Pedimos directamente los 4 mejores chunks para ahorrar procesamiento local
    retriever_base = db.as_retriever(search_kwargs={"k": 4})
    mejores_docs = retriever_base.invoke(pregunta_mejorada)

    contexto_texto = "\n\n".join(
        [f"[Fuente: {d.metadata.get('fuente', 'Desconocida')} | Sección: {d.metadata.get('Header 2', 'General')}]\n{d.page_content}" 
         for d in mejores_docs]
    )

    # ==========================================
    # PASO 3: RESPUESTA FINAL
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

    return respuesta