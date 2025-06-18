from flask import Flask, jsonify, request
from flask_cors import CORS
from requests.auth import HTTPBasicAuth
import requests
import logging

# =======================
# Configuración general
# =======================
app = Flask(__name__)
CORS(app)  # Habilita CORS para peticiones desde frontend

# Logging para depuración
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configuración del Router MikroTik
MIKROTIK_HOST = 'http://192.168.88.1'  # Dirección REST API del router
USERNAME = 'admin'
PASSWORD = '1234567890'


# =======================
# Ruta: Ver dispositivos conectados
# =======================
@app.route('/devices', methods=['GET'])
def get_connected_devices():
    """
    Devuelve la lista de dispositivos DHCP conectados (leases) con:
    - hostname
    - ip_address
    - mac_address
    - comment
    - status
    """
    url = f"{MIKROTIK_HOST}/rest/ip/dhcp-server/lease"
    try:
        response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
        response.raise_for_status()
        leases = response.json()

        connected_devices = []
        for lease in leases:
            # Filtrar dispositivos con estado "bound" (conectados)
            if lease.get("status") == "bound":
                connected_devices.append({
                    "hostname": lease.get("host-name", "Sin nombre"),
                    "ip_address": lease.get("address"),
                    "mac_address": lease.get("mac-address"),
                    "comment": lease.get("comment", ""),
                    "status": lease.get("status")
                })

        return jsonify(connected_devices)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener leases DHCP: {str(e)}")
        return jsonify({'error': str(e)}), 500


# =======================
# Ruta de prueba de conexión/login (opcional)
# =======================
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username == USERNAME and password == PASSWORD:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "message": "Credenciales incorrectas"}), 401


# =======================
# Ejecutar servidor
# =======================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
