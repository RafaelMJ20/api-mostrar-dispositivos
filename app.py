from flask import Flask, jsonify, request
from flask_cors import CORS
from requests.auth import HTTPBasicAuth
import requests
import logging
import os
import sys

# =======================
# Configuración general
# =======================
app = Flask(__name__)
CORS(app)  # Habilita CORS para peticiones desde frontend

# Configuración avanzada de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuración del Router MikroTik (ahora con variables de entorno)
MIKROTIK_HOST = os.getenv('MIKROTIK_HOST', 'http://192.168.88.1')  # Dirección API
USERNAME = os.getenv('MIKROTIK_USER', 'admin')
PASSWORD = os.getenv('MIKROTIK_PASSWORD', '1234567890')
REQUEST_TIMEOUT = 10  # segundos

# =======================
# Funciones de verificación
# =======================
def verify_mikrotik_connection():
    """Verifica la conexión con el MikroTik al iniciar"""
    test_url = f"{MIKROTIK_HOST}/rest/system/resource"
    try:
        logger.info(f"Intentando conectar con MikroTik en: {MIKROTIK_HOST}")
        response = requests.get(
            test_url,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        logger.info("Conexión con MikroTik establecida correctamente")
        return True
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al conectar con MikroTik después de {REQUEST_TIMEOUT}s")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de conexión con MikroTik: {str(e)}")
    return False

# Verificar conexión al iniciar
if not verify_mikrotik_connection():
    logger.warning("ADVERTENCIA: No se pudo establecer conexión inicial con MikroTik")

# =======================
# Ruta: Ver dispositivos conectados (mejorada)
# =======================
@app.route('/devices', methods=['GET'])
def get_connected_devices():
    """Obtiene dispositivos conectados con verificación de conexión"""
    if not verify_mikrotik_connection():
        return jsonify({
            'error': 'No se pudo conectar al router MikroTik',
            'solution': 'Verifique la conectividad de red y credenciales'
        }), 502  # Bad Gateway

    url = f"{MIKROTIK_HOST}/rest/ip/dhcp-server/lease"
    try:
        logger.debug(f"Solicitando leases DHCP desde: {url}")
        response = requests.get(
            url,
            auth=HTTPBasicAuth(USERNAME, PASSWORD),
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        leases = response.json()
        connected_devices = [
            {
                "hostname": lease.get("host-name", "Sin nombre"),
                "ip_address": lease.get("address"),
                "mac_address": lease.get("mac-address"),
                "comment": lease.get("comment", ""),
                "status": lease.get("status"),
                "last_seen": lease.get("last-seen", "")
            }
            for lease in leases if lease.get("status") == "bound"
        ]
        
        logger.info(f"Devueltos {len(connected_devices)} dispositivos conectados")
        return jsonify(connected_devices)
        
    except requests.exceptions.Timeout:
        logger.error("Timeout al obtener dispositivos")
        return jsonify({'error': 'El router no respondió a tiempo'}), 504
    except requests.exceptions.RequestException as e:
        logger.error(f"Error al obtener dispositivos: {str(e)}")
        return jsonify({'error': str(e)}), 500

# =======================
# Ruta de estado del servicio
# =======================
@app.route('/status', methods=['GET'])
def service_status():
    """Endpoint para verificar el estado del servicio y conexión"""
    connection_ok = verify_mikrotik_connection()
    return jsonify({
        'service': 'running',
        'mikrotik_connection': connection_ok,
        'mikrotik_host': MIKROTIK_HOST,
        'timestamp': datetime.datetime.now().isoformat()
    }), 200 if connection_ok else 503

# =======================
# Ruta de login (mejorada)
# =======================
@app.route('/login', methods=['POST'])
def login():
    """Autenticación con registro de intentos"""
    data = request.get_json()
    if not data:
        logger.warning("Intento de login sin datos")
        return jsonify({"success": False, "message": "Datos no proporcionados"}), 400
        
    username = data.get('username')
    password = data.get('password')
    
    logger.debug(f"Intento de login para usuario: {username}")
    
    if username == USERNAME and password == PASSWORD:
        logger.info("Login exitoso")
        return jsonify({
            "success": True,
            "message": "Autenticación exitosa"
        }), 200
    else:
        logger.warning(f"Intento fallido para usuario: {username}")
        return jsonify({
            "success": False,
            "message": "Credenciales incorrectas"
        }), 401

# =======================
# Ejecutar servidor
# =======================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor en puerto {port}")
    app.run(debug=False, host='0.0.0.0', port=port)
