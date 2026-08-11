#!/usr/bin/env bash
# Demostración de disponibilidad: se apaga una instancia del Tier 2 y el sistema
# sigue atendiendo gracias a la redundancia activa + el reintento del gateway.

set -euo pipefail

API="${API_URL:-http://localhost:8081}"
WEB="${WEB_URL:-http://localhost:8080}"
PETICIONES="${PETICIONES:-30}"

medir() {  # medir <etiqueta>
  local ok=0 err=0
  for _ in $(seq 1 "$PETICIONES"); do
    if [[ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "$API/health/ready")" == "200" ]]; then
      ok=$((ok + 1))
    else
      err=$((err + 1))
    fi
  done
  echo "  $1: $ok/$PETICIONES peticiones exitosas ($err fallidas)"
}

echo "== 1. Estado inicial (dos instancias del Tier 2) =="
docker compose ps --format '  {{.Service}}\t{{.State}}'
medir "línea base"

echo
echo "== 2. Se detiene auth-service-1 =="
docker compose stop auth-service-1 >/dev/null
sleep 2
medir "con una instancia caída"
echo "  web sigue respondiendo: HTTP $(curl -s -o /dev/null -w '%{http_code}' "$WEB/login")"

echo
echo "== 3. Se restablece la instancia =="
docker compose start auth-service-1 >/dev/null
sleep 8
medir "tras la recuperación"

echo
echo "Conclusión: la caída de una instancia del Tier 2 no interrumpe el servicio."
echo "Los eventos quedaron registrados; véalos con: docker compose logs gateway"
