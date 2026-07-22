# Usar una imagen oficial de Python ligera
FROM python:3.10-slim

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar el archivo de dependencias primero (aprovecha el caché de Docker)
COPY requirements.txt .

# Instalar las dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación
COPY agente_respuestas.py .
COPY app.py .

# Copiar la base de datos vectorial ya generada para que el agente tenga memoria
COPY chroma_db/ ./chroma_db/

# Exponer el puerto que usa Streamlit por defecto
EXPOSE 8501

# Comando para ejecutar la aplicación
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]