import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import MarkdownTextSplitter

def procesar_archivos_md(ruta_carpeta):
    documentos_procesados = []
    
    # 1. Configurar el "cortador" de texto (Chunking)
    # Cortamos cada 1000 caracteres, con un solapamiento de 100 para no cortar ideas por la mitad
    splitter = MarkdownTextSplitter(chunk_size=1000, chunk_overlap=100)

    # 2. Mapear y leer las fuentes
    for archivo in os.listdir(ruta_carpeta):
        if archivo.endswith(".md"):
            ruta_completa = os.path.join(ruta_carpeta, archivo)
            
            # Cargar el archivo
            loader = TextLoader(ruta_completa, encoding="utf-8")
            docs = loader.load()

            # Dividir en chunks
            chunks = splitter.split_documents(docs)

            # 3. Atribución de metadatos
            for chunk in chunks:
                chunk.metadata["fuente"] = archivo
                chunk.metadata["categoria"] = "Interno" # Etiqueta general
                documentos_procesados.append(chunk)
                
            print(f"✔️ {archivo} procesado: {len(chunks)} fragmentos generados.")

    return documentos_procesados

if __name__ == "__main__":
    carpeta = "documentos_oficiales"
    
    print("Iniciando extracción y chunking...\n" + "-"*40)
    chunks_finales = procesar_archivos_md(carpeta)
    
    print("-"*40)
    print(f"Total de fragmentos listos para indexar: {len(chunks_finales)}")
    
    # Imprimir una muestra para validar
    if chunks_finales:
        print("\nEjemplo del primer fragmento extraído:")
        print("METADATOS:", chunks_finales[0].metadata)
        print("CONTENIDO:\n", chunks_finales[0].page_content[:200], "...\n")