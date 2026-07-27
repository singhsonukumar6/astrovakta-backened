#!/bin/bash
# Comprehensive endpoint test — all registered backend routes
# Run: bash test_all_endpoints.sh

set -eo pipefail

BASE="http://127.0.0.1:5000"
API_KEY="avk_275725f91c83cc7dcb171be153bcffb6"
JWT_TOKEN=""

PASS=0; FAIL=0; SKIP=0
ERRORS=()

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { ((PASS++)); echo -e "  ${GREEN}✓${NC} $1"; }
fail() { ((FAIL++)); echo -e "  ${RED}✗${NC} $1 — $2"; ERRORS+=("$1: $2"); }
header() { echo -e "\n${CYAN}━━━ $1 ━━━${NC}"; }

check() {
  local label="$1" method="$2" url="$3" data="$4" expect="$5"
  local curl_args=(-s -o /dev/null -w '%{http_code}' -X "$method" "$url")
  curl_args+=(-H "X-API-Key: $API_KEY")
  if [[ -n "$data" ]]; then
    curl_args+=(-H 'Content-Type: application/json')
    curl_args+=(-d "$data")
  fi
  local http_code
  http_code=$(curl "${curl_args[@]}" 2>/dev/null || echo "000")
  if [[ "$http_code" == "$expect" ]]; then ok "$label ($http_code)"
  else fail "$label" "expected $expect, got $http_code"; fi
}

# Helper: merge extra fields into a JSON base string
mj() {
  python3 -c "
import sys, json
base = json.loads(sys.argv[1])
extra = json.loads('{' + sys.argv[2] + '}')
base.update(extra)
print(json.dumps(base))
" "$1" "$2"
}

check_jwt() {
  local label="$1" method="$2" url="$3" data="$4" expect="$5"
  local curl_args=(-s -o /dev/null -w '%{http_code}' -X "$method" "$url")
  curl_args+=(-H "Authorization: Bearer $JWT_TOKEN")
  if [[ -n "$data" ]]; then
    curl_args+=(-H 'Content-Type: application/json')
    curl_args+=(-d "$data")
  fi
  local http_code
  http_code=$(curl "${curl_args[@]}" 2>/dev/null || echo "000")
  if [[ "$http_code" == "$expect" ]]; then ok "$label ($http_code)"
  else fail "$label" "expected $expect, got $http_code"; fi
}

BD='{"dateOfBirth":"1990-05-15","timeOfBirth":"14:30","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}'
BDC="$BD, \"houseSystem\":\"W\", \"nodeMode\":\"mean\""
COM='{"maleDateOfBirth":"1990-05-15","maleTimeOfBirth":"14:30","maleLatitude":28.6139,"maleLongitude":77.2090,"maleTimezone":"Asia/Kolkata","femaleDateOfBirth":"1992-08-20","femaleTimeOfBirth":"10:00","femaleLatitude":28.6139,"femaleLongitude":77.2090,"femaleTimezone":"Asia/Kolkata"}'

# ════════════════════════════════════════════════════════════════════════════════
header "0. HEALTH & AUTH"
# ════════════════════════════════════════════════════════════════════════════════
check "GET /health" GET "$BASE/health" "" "200"
UNIQUE_EMAIL="test_$(date +%s)@test.com"
check "POST /auth/register" POST "$BASE/auth/register" "{\"email\":\"$UNIQUE_EMAIL\",\"password\":\"test1234\",\"name\":\"Test Runner\"}" "200"
check "POST /auth/login" POST "$BASE/auth/login" '{"email":"admin@astrovakta.com","password":"admin123"}' "200"

# Get JWT token for auth-required endpoints
JWT_RESP=$(curl -s -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@astrovakta.com","password":"admin123"}' 2>/dev/null || echo '{}')
JWT_TOKEN=$(echo "$JWT_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('token',d.get('access_token','')))" 2>/dev/null || echo "")

if [[ -n "$JWT_TOKEN" ]]; then
  check_jwt "GET /auth/me" GET "$BASE/auth/me" "" "200"
  check_jwt "GET /auth/keys" GET "$BASE/auth/keys" "" "200"
fi

# ════════════════════════════════════════════════════════════════════════════════
header "1. KUNDLI"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /api/kundli" POST "$BASE/api/kundli" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "2. BIRTH CHART & PLANETS"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /horoscope/planet-details" POST "$BASE/horoscope/planet-details" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "3. BHAVA CHALIT"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /horoscope/bhava-chalit" POST "$BASE/horoscope/bhava-chalit" "$BD" "200"
check "POST /horoscope/bhava-chalit/cusps" POST "$BASE/horoscope/bhava-chalit/cusps" "$BD" "200"
check "POST /horoscope/bhava-chalit/compare" POST "$BASE/horoscope/bhava-chalit/compare" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "4. DASHA"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /horoscope/dasha/vimshottari" POST "$BASE/horoscope/dasha/vimshottari" "$BD" "200"
check "POST /horoscope/dasha/current" POST "$BASE/horoscope/dasha/current" "$BD" "200"
check "POST /horoscope/dasha/timeline" POST "$BASE/horoscope/dasha/timeline" "$BD" "200"
check "POST /horoscope/dasha/details" POST "$BASE/horoscope/dasha/details" "$(mj "$BD" '"planet":"Saturn"')" "200"
check "POST /horoscope/dasha/chara" POST "$BASE/horoscope/dasha/chara" "$BD" "200"
check "POST /dasha/yogini" POST "$BASE/dasha/yogini" "$BD" "200"
check "POST /dasha/ashtottari" POST "$BASE/dasha/ashtottari" "$BD" "200"
check "POST /dasha/kalachakra" POST "$BASE/dasha/kalachakra" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "5. DOSHA"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /horoscope/dosha/compute" POST "$BASE/horoscope/dosha/compute" "$BD" "200"
check "POST /horoscope/dosha/severity" POST "$BASE/horoscope/dosha/severity" "$BD" "200"
check "POST /horoscope/dosha/remedies" POST "$BASE/horoscope/dosha/remedies" "$BD" "200"
check "POST /horoscope/dosha/dhaiya" POST "$BASE/horoscope/dosha/dhaiya" "$BD" "200"
check "POST /horoscope/dosha/compatibility-impact" POST "$BASE/horoscope/dosha/compatibility-impact" \
  "$(mj "$BD" '"partnerDateOfBirth":"1992-08-20","partnerTimeOfBirth":"10:00","partnerLatitude":28.6139,"partnerLongitude":77.2090,"partnerTimezone":"Asia/Kolkata"')" "200"
check "POST /api/dosha/nadi-dosha" POST "$BASE/api/dosha/nadi-dosha" "$COM" "200"
check "POST /api/dosha/bhakoot-dosha" POST "$BASE/api/dosha/bhakoot-dosha" "$COM" "200"
check "POST /api/dosha/yoni-compatibility" POST "$BASE/api/dosha/yoni-compatibility" "$COM" "200"
check "POST /api/dosha/manglik-detailed" POST "$BASE/api/dosha/manglik-detailed" "$BD" "200"
check "POST /api/dosha/shrapit" POST "$BASE/api/dosha/shrapit" "$BD" "200"
check "POST /api/dosha/grahan" POST "$BASE/api/dosha/grahan" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "6. YOGA"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /horoscope/yoga/detailed" POST "$BASE/horoscope/yoga/detailed" "$(mj "$BD" '"yogaName":"Gaja Kesari Yoga"')" "200"
check "POST /horoscope/yoga/score" POST "$BASE/horoscope/yoga/score" "$BD" "200"
check "POST /horoscope/yoga/predictions" POST "$BASE/horoscope/yoga/predictions" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "7. PANCHANG"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /horoscope/panchang" POST "$BASE/horoscope/panchang" "$BD" "200"
check "POST /horoscope/panchang/rahu-kaal" POST "$BASE/horoscope/panchang/rahu-kaal" "$BD" "200"
check "POST /horoscope/panchang/yamaganda" POST "$BASE/horoscope/panchang/yamaganda" "$BD" "200"
check "POST /horoscope/panchang/gulika-kaal" POST "$BASE/horoscope/panchang/gulika-kaal" "$BD" "200"
check "POST /horoscope/panchang/gulika-position" POST "$BASE/horoscope/panchang/gulika-position" "$BD" "200"
check "POST /horoscope/panchang/hora" POST "$BASE/horoscope/panchang/hora" "$BD" "200"
check "POST /horoscope/panchang/choghadiya" POST "$BASE/horoscope/panchang/choghadiya" "$BD" "200"
check "POST /horoscope/panchang/abhijit-muhurat" POST "$BASE/horoscope/panchang/abhijit-muhurat" "$BD" "200"
check "POST /horoscope/panchang/panchaka" POST "$BASE/horoscope/panchang/panchaka" "$BD" "200"
check "POST /horoscope/panchang/roga-nidana" POST "$BASE/horoscope/panchang/roga-nidana" "$BD" "200"
check "POST /horoscope/panchang/moonrise" POST "$BASE/horoscope/panchang/moonrise" "$BD" "200"
check "POST /horoscope/panchang/moonset" POST "$BASE/horoscope/panchang/moonset" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "8. MUHURAT"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /horoscope/muhurat/cesarean" POST "$BASE/horoscope/muhurat/cesarean" \
  '{"dateOfBirth":"2026-08-15","timeOfBirth":"14:30","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata","houseSystem":"W"}' "200"
check "POST /horoscope/muhurat/naming-ceremony" POST "$BASE/horoscope/muhurat/naming-ceremony" \
  '{"dateOfBirth":"2026-08-15","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata","houseSystem":"W"}' "200"
check "POST /horoscope/muhurat/marriage" POST "$BASE/horoscope/muhurat/marriage" \
  '{"dateOfBirth":"2026-08-15","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata","houseSystem":"W"}' "200"
check "POST /horoscope/muhurat/house-warming" POST "$BASE/horoscope/muhurat/house-warming" \
  '{"dateOfBirth":"2026-08-15","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata","houseSystem":"W"}' "200"
check "POST /horoscope/muhurat/business-opening" POST "$BASE/horoscope/muhurat/business-opening" \
  '{"dateOfBirth":"2026-08-15","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata","houseSystem":"W"}' "200"
check "POST /horoscope/muhurat/vehicle-purchase" POST "$BASE/horoscope/muhurat/vehicle-purchase" \
  '{"dateOfBirth":"2026-08-15","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata","houseSystem":"W"}' "200"
check "POST /horoscope/muhurat/property-purchase" POST "$BASE/horoscope/muhurat/property-purchase" \
  '{"dateOfBirth":"2026-08-15","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata","houseSystem":"W"}' "200"
check "POST /horoscope/muhurat/engagement" POST "$BASE/horoscope/muhurat/engagement" \
  '{"dateOfBirth":"2026-08-15","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata","houseSystem":"W"}' "200"
check "POST /horoscope/muhurat/griha-pravesh" POST "$BASE/horoscope/muhurat/griha-pravesh" \
  '{"dateOfBirth":"2026-08-15","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata","houseSystem":"W"}' "200"

# ════════════════════════════════════════════════════════════════════════════════
header "9. TRANSIT"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /horoscope/transit" POST "$BASE/horoscope/transit" "$BD" "200"
check "POST /horoscope/transit/current" POST "$BASE/horoscope/transit/current" "$BD" "200"
check "POST /horoscope/transit/monthly" POST "$BASE/horoscope/transit/monthly" "$BD" "200"
check "POST /horoscope/transit/prediction" POST "$BASE/horoscope/transit/prediction" "$BD" "200"
check "POST /horoscope/transit/timing" POST "$BASE/horoscope/transit/timing" "$(mj "$BD" '"event":"career_change"')" "200"
check "POST /horoscope/transit/by-planet" POST "$BASE/horoscope/transit/by-planet" "$(mj "$BD" '"planet":"Saturn"')" "200"
check "POST /api/transit/planet-transit" POST "$BASE/api/transit/planet-transit" "$(mj "$BD" '"planetName":"Saturn"')" "200"
check "POST /api/transit/retrograde" POST "$BASE/api/transit/retrograde" "$BD" "200"
check "POST /api/transit/exalted" POST "$BASE/api/transit/exalted" "$BD" "200"
check "POST /api/transit/debilitated" POST "$BASE/api/transit/debilitated" "$BD" "200"
check "POST /api/transit/combust" POST "$BASE/api/transit/combust" "$BD" "200"
check "POST /api/transit/aspect" POST "$BASE/api/transit/aspect" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "10. COMPATIBILITY"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /horoscope/compat" POST "$BASE/horoscope/compat" "$COM" "200"
check "POST /horoscope/compat/detailed" POST "$BASE/horoscope/compat/detailed" "$COM" "200"
check "POST /api/compat/nadi" POST "$BASE/api/compat/nadi" "$COM" "200"
check "POST /api/compat/bhakoot" POST "$BASE/api/compat/bhakoot" "$COM" "200"
check "POST /api/compat/yoni" POST "$BASE/api/compat/yoni" "$COM" "200"
check "POST /api/compat/tara" POST "$BASE/api/compat/tara" "$COM" "200"
check "POST /api/compat/gana" POST "$BASE/api/compat/gana" "$COM" "200"
check "POST /api/compat/gun-milan" POST "$BASE/api/compat/gun-milan" "$COM" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "11. VARSHAPHAL"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /horoscope/varshaphal" POST "$BASE/horoscope/varshaphal" "$BD" "200"
check "POST /horoscope/varshaphal/prediction" POST "$BASE/horoscope/varshaphal/prediction" "$BD" "200"
check "POST /horoscope/varshaphal/tajika-aspects" POST "$BASE/horoscope/varshaphal/tajika-aspects" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "12. SPECIAL PREDICTIONS"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /horoscope/business" POST "$BASE/horoscope/business" "$BD" "200"
check "POST /horoscope/child" POST "$BASE/horoscope/child" "$BD" "200"
check "POST /horoscope/education" POST "$BASE/horoscope/education" "$BD" "200"
check "POST /horoscope/foreign" POST "$BASE/horoscope/foreign" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "13. CHART SVG"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /chart/svg" POST "$BASE/chart/svg" "$(mj "$BD" '"width":600,"height":600')" "200"
check "POST /chart/navamsa-svg" POST "$BASE/chart/navamsa-svg" "$BD" "200"
check "POST /chart/east-svg" POST "$BASE/chart/east-svg" "$BD" "200"
check "POST /chart/grid-svg" POST "$BASE/chart/grid-svg" "$BD" "200"
check "POST /chart/divisional-svg" POST "$BASE/chart/divisional-svg" "$(mj "$BD" '"name":"navamsa"')" "200"
check "POST /chart/moon-svg" POST "$BASE/chart/moon-svg" "$BD" "200"
check "POST /chart/hora-svg" POST "$BASE/chart/hora-svg" "$BD" "200"
check "POST /chart/sudarshana-svg" POST "$BASE/chart/sudarshana-svg" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "14. CALENDAR / PANCHAANG API"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /api/calendar/panchang" POST "$BASE/api/calendar/panchang" \
  '{"year":2026,"month":1,"latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"
check "POST /api/calendar/hindu" POST "$BASE/api/calendar/hindu" \
  '{"year":2026,"month":1,"latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"
check "POST /api/calendar/festival" POST "$BASE/api/calendar/festival" \
  '{"year":2026,"latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"
check "POST /api/calendar/muhurat" POST "$BASE/api/calendar/muhurat" \
  '{"year":2026,"month":1,"latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"
check "POST /api/calendar/year" POST "$BASE/api/calendar/year" \
  '{"year":2026,"latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"
check "POST /api/calendar/year/auspicious-dates" POST "$BASE/api/calendar/year/auspicious-dates" \
  '{"year":2026,"latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata","purpose":"marriage"}' "200"
check "POST /api/calendar/year/monthly-summary" POST "$BASE/api/calendar/year/monthly-summary" \
  '{"year":2026,"month":10,"latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"
check "POST /calendar-api/panchang" POST "$BASE/calendar-api/panchang" \
  '{"year":2026,"month":1,"latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"
check "POST /calendar-api/hindu" POST "$BASE/calendar-api/hindu" \
  '{"year":2026,"month":1,"latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"
check "POST /calendar-api/festival" POST "$BASE/calendar-api/festival" \
  '{"year":2026,"latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"
check "POST /calendar-api/muhurat" POST "$BASE/calendar-api/muhurat" \
  '{"year":2026,"month":1,"latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"

# ════════════════════════════════════════════════════════════════════════════════
header "15. REPORTS"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /reports/birth-chart" POST "$BASE/reports/birth-chart" "$BD" "200"
check "POST /reports/career" POST "$BASE/reports/career" "$BD" "200"
check "POST /reports/predictions" POST "$BASE/reports/predictions" "$BD" "200"
check "POST /reports/pdf-info" POST "$BASE/reports/pdf-info" "$BD" "200"
check "POST /reports/full-pdf" POST "$BASE/reports/full-pdf" "$BD" "200"
check "POST /reports/comprehensive" POST "$BASE/reports/comprehensive" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "16. AI ASTRO"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /ai/career-analysis" POST "$BASE/ai/career-analysis" "$BD" "200"
check "POST /ai/kundli-interpretation" POST "$BASE/ai/kundli-interpretation" "$BD" "200"
check "POST /ai/chat" POST "$BASE/ai/chat" "$(mj "$BD" '"question":"What does my chart say?"')" "200"
check "POST /ai/prediction" POST "$BASE/ai/prediction" "$BD" "200"
check "POST /ai/horoscope-generation" POST "$BASE/ai/horoscope-generation" "$BD" "200"
check "POST /ai/gemstone-advisor" POST "$BASE/ai/gemstone-advisor" "$BD" "200"
check "POST /ai/remedies" POST "$BASE/ai/remedies" "$BD" "200"
check "POST /ai/marriage-analysis" POST "$BASE/ai/marriage-analysis" \
  "$(mj "$BD" '"partnerDateOfBirth":"1992-08-20","partnerTimeOfBirth":"10:00","partnerLatitude":28.6139,"partnerLongitude":77.2090,"partnerTimezone":"Asia/Kolkata"')" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "17. LUCKY"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /lucky/color" POST "$BASE/lucky/color" '{"dateOfBirth":"1990-05-15"}' "200"
check "POST /lucky/number" POST "$BASE/lucky/number" '{"dateOfBirth":"1990-05-15"}' "200"
check "POST /lucky/day" POST "$BASE/lucky/day" '{"dateOfBirth":"1990-05-15"}' "200"
check "POST /lucky/metal" POST "$BASE/lucky/metal" '{"dateOfBirth":"1990-05-15"}' "200"

# ════════════════════════════════════════════════════════════════════════════════
header "18. GEMSTONE"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /api/gemstone/recommendation" POST "$BASE/api/gemstone/recommendation" "$BD" "200"
check "POST /api/gemstone/by-planet" POST "$BASE/api/gemstone/by-planet" '{"planet":"Jupiter"}' "200"
check "POST /api/gemstone/by-lagna" POST "$BASE/api/gemstone/by-lagna" "$BD" "200"
check "POST /api/gemstone/by-dasha" POST "$BASE/api/gemstone/by-dasha" "$BD" "200"
check "POST /api/gemstone/wearing" POST "$BASE/api/gemstone/wearing" "$BD" "200"
check "POST /api/gemstone/finger" POST "$BASE/api/gemstone/finger" '{"planet":"Jupiter"}' "200"
check "POST /api/gemstone/weight" POST "$BASE/api/gemstone/weight" "$BD" "200"
check "POST /api/gemstone/metal" POST "$BASE/api/gemstone/metal" '{"planet":"Jupiter"}' "200"

# ════════════════════════════════════════════════════════════════════════════════
header "19. CALCULATOR"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /api/calculator/lagna" POST "$BASE/api/calculator/lagna" "$BD" "200"
check "POST /api/calculator/moon-sign" POST "$BASE/api/calculator/moon-sign" "$BD" "200"
check "POST /api/calculator/sun-sign" POST "$BASE/api/calculator/sun-sign" "$BD" "200"
check "POST /api/calculator/shadbala" POST "$BASE/api/calculator/shadbala" "$BD" "200"
check "POST /api/calculator/ashtakavarga" POST "$BASE/api/calculator/ashtakavarga" "$BD" "200"
check "POST /api/calculator/planet-strength" POST "$BASE/api/calculator/planet-strength" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "20. PRASHNA"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /api/prashna/chart" POST "$BASE/api/prashna/chart" \
  '{"question":"Will I get the job?","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"
check "POST /api/prashna/judgement" POST "$BASE/api/prashna/judgement" \
  '{"question":"Should I relocate abroad?","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"

# ════════════════════════════════════════════════════════════════════════════════
header "21. POOJA"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /pooja/recommendation" POST "$BASE/pooja/recommendation" "$BD" "200"
check "POST /pooja/availability" POST "$BASE/pooja/availability" '{"date":"2026-08-15","location":"Varanasi"}' "200"
check "POST /pooja/booking" POST "$BASE/pooja/booking" \
  "$(mj "$BD" '"poojaName":"Mangal Dosh Nivaran Puja","preferredDate":"2026-08-15","name":"Rahul Sharma","phone":"+919876543210"')" "200"
check "POST /pooja/sankalp" POST "$BASE/pooja/sankalp" "$BD" "200"
check "POST /pooja/temple" POST "$BASE/pooja/temple" "$BD" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "22. FESTIVAL"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /api/festival/hindu-festival" POST "$BASE/api/festival/hindu-festival" '{"year":2026}' "200"
check "POST /api/festival/diwali" POST "$BASE/api/festival/diwali" '{"year":2026}' "200"
check "POST /api/festival/holi" POST "$BASE/api/festival/holi" '{"year":2026}' "200"
check "POST /api/festival/navratri" POST "$BASE/api/festival/navratri" '{"year":2026}' "200"
check "POST /api/festival/purnima" POST "$BASE/api/festival/purnima" '{"year":2026}' "200"
check "POST /api/festival/ekadashi" POST "$BASE/api/festival/ekadashi" '{"year":2026}' "200"
check "POST /api/festival/sankranti" POST "$BASE/api/festival/sankranti" '{"year":2026}' "200"
check "POST /api/festival/amavasya" POST "$BASE/api/festival/amavasya" '{"year":2026}' "200"
check "POST /api/festival/chaturthi" POST "$BASE/api/festival/chaturthi" '{"year":2026}' "200"

# ════════════════════════════════════════════════════════════════════════════════
header "23. RUDRAKSHA"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /api/rudraksha/recommendation" POST "$BASE/api/rudraksha/recommendation" "$BD" "200"
check "POST /api/rudraksha/benefits" POST "$BASE/api/rudraksha/benefits" '{"mukhiCount":5}' "200"
check "POST /api/rudraksha/mantra" POST "$BASE/api/rudraksha/mantra" '{"mukhiCount":5}' "200"
check "POST /api/rudraksha/mukhi-identification" POST "$BASE/api/rudraksha/mukhi-identification" '{"description":"Round with 5 lines"}' "200"
check "POST /api/rudraksha/wearing-method" POST "$BASE/api/rudraksha/wearing-method" '{"mukhiCount":5,"gender":"male"}' "200"

# ════════════════════════════════════════════════════════════════════════════════
header "24. NUMEROLOGY"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /api/numerology/life-path" POST "$BASE/api/numerology/life-path" '{"dateOfBirth":"1990-05-15"}' "200"
check "POST /api/numerology/expression" POST "$BASE/api/numerology/expression" '{"fullName":"Rahul Sharma"}' "200"
check "POST /api/numerology/soul" POST "$BASE/api/numerology/soul" '{"fullName":"Rahul Sharma"}' "200"
check "POST /api/numerology/destiny" POST "$BASE/api/numerology/destiny" '{"fullName":"Rahul Sharma"}' "200"
check "POST /api/numerology/name-number" POST "$BASE/api/numerology/name-number" '{"name":"Rahul"}' "200"
check "POST /api/numerology/name-compatibility" POST "$BASE/api/numerology/name-compatibility" '{"name1":"Rahul","name2":"Priya"}' "200"
check "POST /api/numerology/baby-name" POST "$BASE/api/numerology/baby-name" '{"dateOfBirth":"1990-05-15","gender":"male"}' "200"
check "POST /api/numerology/business-name" POST "$BASE/api/numerology/business-name" '{"businessName":"Rahul Traders"}' "200"
check "POST /api/numerology/mobile" POST "$BASE/api/numerology/mobile" '{"mobileNumber":"9876543210"}' "200"
check "POST /api/numerology/vehicle" POST "$BASE/api/numerology/vehicle" '{"vehicleNumber":"MH12AB1234"}' "200"

# ════════════════════════════════════════════════════════════════════════════════
header "25. LOCATION"
# ════════════════════════════════════════════════════════════════════════════════
check "GET /api/location/search?q=Delhi" GET "$BASE/api/location/search?q=Delhi" "" "200"
check "GET /api/location/popular" GET "$BASE/api/location/popular" "" "200"
check "GET /api/location/reverse?lat=28.6139&lon=77.2090" GET "$BASE/api/location/reverse?lat=28.6139&lon=77.2090" "" "200"
check "GET /api/location/timezone?lat=28.6139&lon=77.2090" GET "$BASE/api/location/timezone?lat=28.6139&lon=77.2090" "" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "26. UTILITY"
# ════════════════════════════════════════════════════════════════════════════════
check "POST /api/utility/julian-day" POST "$BASE/api/utility/julian-day" '{"date":"1990-05-15","time":"14:30","timezone":"Asia/Kolkata"}' "200"
check "POST /api/utility/lunar-phase" POST "$BASE/api/utility/lunar-phase" '{"date":"2026-08-15","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"
check "POST /api/utility/sunrise-sunset" POST "$BASE/api/utility/sunrise-sunset" '{"date":"2026-08-15","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"
check "POST /api/utility/eclipse" POST "$BASE/api/utility/eclipse" '{"date":"2026-08-15","latitude":28.6139,"longitude":77.2090,"timezone":"Asia/Kolkata"}' "200"
check "POST /api/utility/ayanamsa" POST "$BASE/api/utility/ayanamsa" '{"date":"1990-05-15","time":"14:30","timezone":"Asia/Kolkata"}' "200"
check "POST /api/utility/ephemeris" POST "$BASE/api/utility/ephemeris" '{"date":"1990-05-15","time":"14:30","timezone":"Asia/Kolkata"}' "200"
check "POST /api/utility/planet-speed" POST "$BASE/api/utility/planet-speed" '{"date":"1990-05-15","time":"14:30","timezone":"Asia/Kolkata"}' "200"
check "POST /api/utility/ascendant-scan" POST "$BASE/api/utility/ascendant-scan" "$BD" "200"
check "POST /api/utility/rectify" POST "$BASE/api/utility/rectify" "$BD" "200"
check "POST /api/utility/transit-verify" POST "$BASE/api/utility/transit-verify" "$(mj "$BD" '"eventDate":"2026-08-15","eventType":"career_change"')" "200"

# ════════════════════════════════════════════════════════════════════════════════
header "27. JOBS API (JWT auth)"
# ════════════════════════════════════════════════════════════════════════════════
if [[ -n "$JWT_TOKEN" ]]; then
  check_jwt "POST /jobs/submit-pdf" POST "$BASE/jobs/submit-pdf" "$BD" "200"
  check_jwt "POST /jobs/submit-ai" POST "$BASE/jobs/submit-ai" "$(mj "$BD" '"question":"What does my chart say?"')" "200"
  check_jwt "GET /jobs" GET "$BASE/jobs" "" "200"
fi

# ════════════════════════════════════════════════════════════════════════════════
header "28. ADMIN (JWT auth)"
# ════════════════════════════════════════════════════════════════════════════════
if [[ -z "$JWT_TOKEN" ]]; then
  echo -e "  ${RED}⚠ Could not get JWT token — skipping admin tests${NC}"
else
  check_jwt "GET /admin/stats" GET "$BASE/admin/stats" "" "200"
  check_jwt "GET /admin/users" GET "$BASE/admin/users" "" "200"
  check_jwt "GET /admin/keys" GET "$BASE/admin/keys" "" "200"
  check_jwt "GET /admin/jobs" GET "$BASE/admin/jobs" "" "200"
  check_jwt "GET /admin/usage/daily" GET "$BASE/admin/usage/daily" "" "200"
  check_jwt "GET /admin/usage/endpoints" GET "$BASE/admin/usage/endpoints" "" "200"
  check_jwt "GET /admin/usage/by-user" GET "$BASE/admin/usage/by-user" "" "200"
fi

# ════════════════════════════════════════════════════════════════════════════════
header "29. AI PROVIDERS (JWT auth)"
# ════════════════════════════════════════════════════════════════════════════════
if [[ -n "$JWT_TOKEN" ]]; then
  check_jwt "GET /ai-providers" GET "$BASE/ai-providers" "" "200"
  check_jwt "GET /ai-providers/supported" GET "$BASE/ai-providers/supported" "" "200"
  check_jwt "POST /ai-providers/test" POST "$BASE/ai-providers/test" '{"provider":"openai","api_key":"test-key"}' "200"
fi

# ════════════════════════════════════════════════════════════════════════════════
header "30. PROTECTION (negative test)"
# ════════════════════════════════════════════════════════════════════════════════
NOAUTH=$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/api/kundli" \
  -H 'Content-Type: application/json' -d "$BD" 2>/dev/null || echo "000")
if [[ "$NOAUTH" == "401" || "$NOAUTH" == "403" ]]; then
  ok "No API key → $NOAUTH (blocked)"
else
  fail "No API key → should block" "got $NOAUTH"
fi

# ════════════════════════════════════════════════════════════════════════════════
# RESULTS
# ════════════════════════════════════════════════════════════════════════════════
TOTAL=$((PASS + FAIL + SKIP))
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  ${GREEN}✓ PASSED: $PASS${NC}  ${RED}✗ FAILED: $FAIL${NC}  Total: $TOTAL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ ${#ERRORS[@]} -gt 0 ]]; then
  echo ""
  echo "Failed endpoints:"
  for e in "${ERRORS[@]}"; do
    echo -e "  ${RED}•${NC} $e"
  done
  echo ""
fi

exit $FAIL
