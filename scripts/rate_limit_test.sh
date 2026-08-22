#!/usr/bin/env bash
# Requerimiento 10: dispara una ráfaga de peticiones contra el gateway y
# confirma que aparece un 429 — sin afectar el enrutamiento normal (las
# demás peticiones siguen respondiendo, solo el exceso se rechaza).

set -euo pipefail

API="${API_URL:-http://localhost:8081}"
N="${REQUESTS:-40}"
OK=0
FAIL=0

echo "== Rate limiting del gateway (Requerimiento 10) =="

# /api/v1/auth/introspect es barato (sin BD) y ya está protegido por
# auth_request; un token inválido responde 401 muy rápido, así que la ráfaga
# ejercita el límite sin necesitar una sesión real.
CODES=$(for _ in $(seq 1 "$N"); do
  curl -s -o /dev/null -w '%{http_code}\n' \
    -H "Authorization: Bearer token-invalido" \
    "$API/api/v1/auth/introspect" &
done; wait)

echo "$CODES" | sort | uniq -c | sed 's/^/  /'

if grep -q '429' <<<"$CODES"; then
  echo "  ✅ el gateway respondió 429 tras exceder el límite"
  OK=$((OK + 1))
else
  echo "  ❌ no se observó ningún 429 en la ráfaga de $N peticiones"
  FAIL=$((FAIL + 1))
fi

# El enrutamiento normal no debe verse afectado: una petición aislada
# después de la ráfaga (esperando a que expire la ventana) debe seguir
# respondiendo con normalidad (401, no 429/5xx).
sleep 2
SINGLE=$(curl -s -o /dev/null -w '%{http_code}' \
  -H "Authorization: Bearer token-invalido" "$API/api/v1/auth/introspect")
if [[ "$SINGLE" == "401" ]]; then
  echo "  ✅ el enrutamiento normal se restablece tras la ráfaga"
  OK=$((OK + 1))
else
  echo "  ❌ esperado 401 tras la ráfaga, obtenido $SINGLE"
  FAIL=$((FAIL + 1))
fi

echo
echo "Resultado: $OK pruebas correctas, $FAIL fallidas"
[[ "$FAIL" -eq 0 ]]
