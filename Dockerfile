# Usa una imagen base ligera con Python 3.10
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Instala las dependencias del sistema necesarias para Selenium
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    wget \
    chromium \
    chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# Copia los archivos necesarios
COPY . .

# Instala las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Configura las variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
ENV DISPLAY=:99

# Comando para ejecutar la aplicación
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--timeout", "120", "--workers", "1"]