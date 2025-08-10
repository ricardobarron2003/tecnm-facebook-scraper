# Usa una imagen base más ligera
FROM python:3.10-alpine

# Instala solo dependencias esenciales
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libffi-dev && \
    apk add --no-cache libstdc++

WORKDIR /app

# Instala pip dependencies primero para aprovechar caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps  # Elimina dependencias de compilación

# Copia solo los archivos necesarios
COPY app.py .
COPY chatbot.py .
COPY publicaciones_tec.txt .

# Configura variables de entorno
ENV PYTHONUNBUILD=1
ENV PORT=10000

# Usa un usuario no root para mayor seguridad
RUN adduser -D myuser
USER myuser

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--timeout", "120", "--workers", "1"]