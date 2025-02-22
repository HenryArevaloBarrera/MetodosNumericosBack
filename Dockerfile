# Usamos una imagen ligera de Python
FROM python:3.9-slim

# Establecer el directorio de trabajo en el contenedor
WORKDIR /app

# Copiar los archivos de dependencias y luego instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código fuente al contenedor
COPY . .

# Exponer el puerto 5000 para Flask
EXPOSE 5000

# Definir el comando para ejecutar la aplicación
CMD ["python", "app.py"]
