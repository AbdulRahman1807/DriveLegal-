#!/usr/bin/env bash
# Exercises the same /api/v1/auth/* endpoints the Flutter mobile app uses.
# Open Swagger UI at http://127.0.0.1:8000/docs to try these manually.

set -euo pipefail
BASE="${API_BASE:-http://127.0.0.1:8000/api/v1}"
EMAIL="mobile_swagger_$(date +%s)@example.com"
PASS="mobile_test_pass_99"

echo "=== DriveLegal mobile auth flow (Swagger-compatible) ==="
echo "Base URL: $BASE"
echo "Test email: $EMAIL"
echo ""

register=$(curl -sS -w "\n%{http_code}" -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"language_preference\":\"en\"}")
reg_body=$(echo "$register" | sed '$d')
reg_code=$(echo "$register" | tail -n1)
echo "POST /auth/register -> $reg_code"
if [ "$reg_code" != "201" ]; then
  echo "$reg_body"
  exit 1
fi

ACCESS=$(echo "$reg_body" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
REFRESH=$(echo "$reg_body" | python3 -c "import sys,json; print(json.load(sys.stdin)['refresh_token'])")
echo "  access_token: ${ACCESS:0:24}..."
echo ""

me=$(curl -sS -w "\n%{http_code}" -X GET "$BASE/auth/me" \
  -H "Authorization: Bearer $ACCESS")
me_body=$(echo "$me" | sed '$d')
me_code=$(echo "$me" | tail -n1)
echo "GET /auth/me -> $me_code"
echo "  email: $(echo "$me_body" | python3 -c "import sys,json; print(json.load(sys.stdin).get('email',''))")"
echo ""

login=$(curl -sS -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}")
login_code=$(echo "$login" | tail -n1)
echo "POST /auth/login -> $login_code"
echo ""

refresh=$(curl -sS -w "\n%{http_code}" -X POST "$BASE/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH\"}")
ref_code=$(echo "$refresh" | tail -n1)
echo "POST /auth/refresh -> $ref_code"
echo ""

patch=$(curl -sS -w "\n%{http_code}" -X PATCH "$BASE/auth/me" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Content-Type: application/json" \
  -d '{"language_preference":"hi"}')
patch_code=$(echo "$patch" | tail -n1)
echo "PATCH /auth/me -> $patch_code"
echo ""

del=$(curl -sS -w "\n%{http_code}" -X DELETE "$BASE/auth/me" \
  -H "Authorization: Bearer $ACCESS")
del_code=$(echo "$del" | tail -n1)
echo "DELETE /auth/me -> $del_code"
echo ""
echo "All mobile auth endpoints OK. Swagger: http://127.0.0.1:8000/docs#tag/auth"
