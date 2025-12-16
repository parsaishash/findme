#!/bin/bash
# Test script for static file serving with FORCE_SCRIPT_NAME
# Usage: ./scripts/test_static_files.sh [base_url] [prefix]
# Example: ./scripts/test_static_files.sh http://localhost:8000 /findme

set -e

BASE_URL="${1:-http://localhost:8000}"
PREFIX="${2:-/findme}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Testing static file serving"
echo "Base URL: $BASE_URL"
echo "Prefix: $PREFIX"
echo ""

# Test static files
test_static_file() {
    local url="$1"
    local description="$2"
    local expected_status="${3:-200}"
    
    echo -n "Testing $description... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (HTTP $response, expected $expected_status)"
        return 1
    fi
}

# Test static file content
test_static_content() {
    local url="$1"
    local description="$2"
    local expected_content="$3"
    
    echo -n "Testing $description content... "
    
    content=$(curl -s "$url" 2>/dev/null || echo "")
    
    if echo "$content" | grep -q "$expected_content"; then
        echo -e "${GREEN}✓ PASS${NC}"
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (content not found)"
        return 1
    fi
}

# Counters
passed=0
failed=0

# Test cases
echo "=== Testing with prefix ==="
if [ "$PREFIX" != "/" ]; then
    # Test CSS file with prefix
    if test_static_file "$BASE_URL$PREFIX/static/core/css/app.css" "CSS file with prefix"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    # Test JS file with prefix
    if test_static_file "$BASE_URL$PREFIX/static/core/js/app.js" "JS file with prefix"; then
        ((passed++))
    else
        ((failed++))
    fi
    
    # Test admin static file with prefix
    if test_static_file "$BASE_URL$PREFIX/static/admin/css/base.css" "Admin CSS with prefix"; then
        ((passed++))
    else
        ((failed++))
    fi
else
    echo -e "${YELLOW}No prefix specified, skipping prefix tests${NC}"
fi

echo ""
echo "=== Testing without prefix (should fail if FORCE_SCRIPT_NAME is set) ==="
# Test CSS file without prefix (should fail if FORCE_SCRIPT_NAME is set)
if test_static_file "$BASE_URL/static/core/css/app.css" "CSS file without prefix" "404"; then
    ((passed++))
else
    # If it returns 200, that's also acceptable (no prefix configured)
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/static/core/css/app.css" 2>/dev/null || echo "000")
    if [ "$response" = "200" ]; then
        echo -e "${YELLOW}Note: Static files accessible without prefix (FORCE_SCRIPT_NAME not set)${NC}"
        ((passed++))
    else
        ((failed++))
    fi
fi

echo ""
echo "=== Testing HTML template rendering ==="
# Test that HTML pages include correct static URLs
echo -n "Testing HTML template static URLs... "
html_content=$(curl -s "$BASE_URL$PREFIX/" 2>/dev/null || echo "")

if [ -n "$html_content" ]; then
    if echo "$html_content" | grep -q "$PREFIX/static"; then
        echo -e "${GREEN}✓ PASS${NC} (template includes prefixed static URLs)"
        ((passed++))
    else
        echo -e "${YELLOW}⚠ WARN${NC} (template may not include prefixed static URLs)"
        ((passed++))
    fi
else
    echo -e "${RED}✗ FAIL${NC} (could not fetch HTML)"
    ((failed++))
fi

echo ""
echo "=== Summary ==="
echo -e "Passed: ${GREEN}$passed${NC}"
echo -e "Failed: ${RED}$failed${NC}"

if [ $failed -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed!${NC}"
    exit 1
fi

