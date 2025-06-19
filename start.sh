#!/bin/bash

# Configurar WireGuard
cat > /etc/wireguard/wg0.conf <<EOF
[Interface]
PrivateKey = $RENDER_PRIVATE_KEY
Address = $WG_LOCAL_IP

[Peer]
PublicKey = $MIKROTIK_PUBLIC_KEY
AllowedIPs = $WG_ALLOWED_IPS
Endpoint = $MIKROTIK_PUBLIC_IP:$WG_PORT
PersistentKeepalive = 25
EOF

# Configurar políticas de ruteo
iptables -A FORWARD -i wg0 -j ACCEPT
iptables -A FORWARD -o wg0 -j ACCEPT
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Iniciar VPN
wg-quick up wg0

# Esperar conexión
sleep 5

# Verificar conexión
wg show

# Iniciar aplicación Flask
exec gunicorn --bind 0.0.0.0:$PORT app:app
