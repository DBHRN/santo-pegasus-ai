import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

def procesar_archivos_md(ruta_carpeta):
    documentos_procesados = []

    # 1. Definir los niveles de encabezados que queremos rastrear
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]
    
    # Splitter Inteligente: Corta el documento respetando las secciones Markdown
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

    # Splitter Secundario: Por si una sección bajo un título es extremadamente larga
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)

    for archivo in os.listdir(ruta_carpeta):
        if archivo.endswith(".md"):
            ruta_completa = os.path.join(ruta_carpeta, archivo)
            
            with open(ruta_completa, "r", encoding="utf-8") as f:
                texto = f.read()
            
            # Primer corte: Lógico (por títulos)
            md_header_splits = markdown_splitter.split_text(texto)
            
            # Segundo corte: Tamaño (por seguridad para el modelo)
            chunks = text_splitter.split_documents(md_header_splits)

            for chunk in chunks:
                chunk.metadata["fuente"] = archivo
                chunk.metadata["categoria"] = "Interno"
                documentos_procesados.append(chunk)
                
            print(f"✔️ {archivo} extraído lógicamente en {len(chunks)} chunks.")

    return documentos_procesados

def crear_indice_vectorial(chunks):
    print("\nCargando modelo de embeddings multilingüe...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    
    directorio_db = "./chroma_db"
    
    print("Generando embeddings y guardando en ChromaDB...")
    db = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=directorio_db)
    return db

if __name__ == "__main__":
    carpeta = "documentos_oficiales"
    
    print("--- ETAPA 2: EXTRACCIÓN ESTRUCTURAL ---")
    chunks_finales = procesar_archivos_md(carpeta)
    
    if chunks_finales:
        print("\n--- ETAPA 3: INDEXACIÓN VECTORIAL ---")
        base_de_datos = crear_indice_vectorial(chunks_finales)
        print("\n🚀 ¡Indexación estructural completada!")