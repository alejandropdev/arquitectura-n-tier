#!/usr/bin/env bash
# Prueba end-to-end contra el despliegue en Docker:
# registro -> login -> panel -> cierre de sesión, atravesando los tres tiers.

set -euo pipefail

WEB="${WEB_URL:-http://localhost:8080}"
API="${API_URL:-http://localhost:8081}"
USER="smoke_$(date +%s)"
PASS="Segura123"
COOKIES="$(mktemp)"
TRACE="smoke-$(date +%s)"
OK=0
FAIL=0

check() {  # check <descripción> <esperado> <obtenido>
  if [[ "$2" == "$3" ]]; then
    echo "  ✅ $1"
    OK=$((OK + 1))
  else
    echo "  ❌ $1 (esperado: $2, obtenido: $3)"
    FAIL=$((FAIL + 1))
  fi
}

echo "== Salud de los tiers =="
check "gateway responde"        "200" "$(curl -s -o /dev/null -w '%{http_code}' "$WEB/gateway/health")"
check "Tier 1 vivo"             "200" "$(curl -s -o /dev/null -w '%{http_code}' "$WEB/health")"
check "Tier 1 listo"            "200" "$(curl -s -o /dev/null -w '%{http_code}' "$WEB/health/ready")"
check "Tier 2 vivo"             "200" "$(curl -s -o /dev/null -w '%{http_code}' "$API/health")"
check "Tier 2 listo (Tier 3 ok)" "200" "$(curl -s -o /dev/null -w '%{http_code}' "$API/health/ready")"

echo "== Flujo de usuario por la web (Tier 1 -> 2 -> 3) =="
REG=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$WEB/register" \
  -H "X-Request-ID: $TRACE" \
  --data-urlencode "username=$USER" \
  --data-urlencode "email=$USER@example.com" \
  --data-urlencode "password=$PASS" \
  --data-urlencode "password_confirm=$PASS")
check "registro desde la web" "200" "$REG"

LOGIN=$(curl -s -o /dev/null -w '%{http_code}' -c "$COOKIES" -X POST "$WEB/login" \
  -H "X-Request-ID: $TRACE" \
  --data-urlencode "username=$USER" --data-urlencode "password=$PASS")
check "login exitoso (redirección)" "303" "$LOGIN"

DASH=$(curl -s -b "$COOKIES" "$WEB/dashboard")
if grep -q "$USER" <<<"$DASH"; then
  echo "  ✅ panel muestra al usuario autenticado"; OK=$((OK + 1))
else
  echo "  ❌ panel no muestra al usuario"; FAIL=$((FAIL + 1))
fi

BAD=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$WEB/login" \
  --data-urlencode "username=$USER" --data-urlencode "password=ClaveMala1")
check "credenciales incorrectas rechazadas" "401" "$BAD"

echo "== API del Tier 2 =="
DUP=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/api/v1/auth/register" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$USER\",\"email\":\"$USER@example.com\",\"password\":\"$PASS\"}")
check "usuario duplicado -> 409" "409" "$DUP"

WEAK=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/api/v1/auth/register" \
  -H 'Content-Type: application/json' \
  -d '{"username":"debil_user","email":"debil@example.com","password":"sindigitos"}')
check "contraseña débil -> 422" "422" "$WEAK"

TOKEN=$(curl -s -X POST "$API/api/v1/auth/login" -H 'Content-Type: application/json' \
  -d "{\"username\":\"$USER\",\"password\":\"$PASS\"}" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
[[ -n "$TOKEN" ]] && { echo "  ✅ el microservicio emite JWT"; OK=$((OK + 1)); } \
                  || { echo "  ❌ no se obtuvo JWT"; FAIL=$((FAIL + 1)); }

VER=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/api/v1/auth/verify" \
  -H 'Content-Type: application/json' -d "{\"token\":\"$TOKEN\"}")
check "token válido verificado" "200" "$VER"

INV=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$API/api/v1/auth/verify" \
  -H 'Content-Type: application/json' -d '{"token":"no-es-un-jwt"}')
check "token inválido -> 401" "401" "$INV"

rm -f "$COOKIES"
echo
echo "Resultado: $OK pruebas correctas, $FAIL fallidas   (traza: $TRACE)"
echo "Vea los logs correlacionados con:  docker compose logs | grep $TRACE"
[[ "$FAIL" -eq 0 ]]
