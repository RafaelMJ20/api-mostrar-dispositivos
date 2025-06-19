FROM python:3.9-slim

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    wireguard \
    iproute2 \
    iptables \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio para WireGuard
RUN mkdir -p /etc/wireguard

# Copiar la aplicación
WORKDIR /app
COPY . .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Hacer ejecutable el script de inicio
RUN chmod +x /start.sh

# Puerto expuesto (para Render)
EXPOSE $PORT

CMD ["/start.sh"]
