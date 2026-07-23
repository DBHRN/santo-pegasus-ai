FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema necesarias para compilaciones básicas
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar los requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente al contenedor
COPY . .

# Exponer el puerto que usa Streamlit por defecto en Render
EXPOSE 8501

# Comando para ejecutar la aplicación de Streamlit apuntando a tu app en src/
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]