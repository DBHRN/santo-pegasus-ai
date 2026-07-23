FROM python:3.12-slim

WORKDIR src/app

# Actualización limpia y directa de paquetes esenciales
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar los requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente al contenedor
COPY . .

# Exponer el puerto que usa Streamlit por defecto en Render
EXPOSE 8501

# Comando para ejecutar la aplicación de Streamlit
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]