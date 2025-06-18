#!/bin/bash
# Supabase Authentication and Connection Troubleshooting Script
# This script checks connectivity to Supabase services from your environment

echo "=== Supabase Connection Diagnostic Tool ==="
echo "This script will help diagnose connectivity issues with Supabase"

# Load environment variables from .env file if present
if [ -f .env ]; then
    echo "Loading environment variables from .env file"
    export $(grep -v '^#' .env | xargs)
fi

# Check if required environment variables are set
if [ -z "$SUPABASE_URL" ]; then
    echo "❌ SUPABASE_URL environment variable not set"
    exit 1
fi

if [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "❌ SUPABASE_ANON_KEY environment variable not set"
    exit 1
fi

echo -e "\n=== Basic connectivity tests ==="

# Extract domain from Supabase URL
DOMAIN=$(echo $SUPABASE_URL | sed 's/https:\/\///' | sed 's/http:\/\///')

# Basic connectivity test
echo -n "Testing basic connectivity to $DOMAIN... "
if ping -c 1 $DOMAIN > /dev/null 2>&1; then
    echo "✅ Success"
else
    echo "❌ Failed"
    echo "Cannot reach Supabase server. Check your network connection or firewall settings."
fi

# Test HTTPS connection
echo -n "Testing HTTPS connection to $SUPABASE_URL... "
if curl -s -o /dev/null -w "%{http_code}" $SUPABASE_URL > /dev/null 2>&1; then
    echo "✅ Success"
else
    echo "❌ Failed"
    echo "Cannot establish HTTPS connection to Supabase URL."
    echo "This may indicate network restrictions or incorrect URL."
fi

# Test API endpoint with anon key
echo -e "\n=== Testing API access ==="
echo -n "Testing REST API access with anon key... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "apikey: $SUPABASE_ANON_KEY" "$SUPABASE_URL/rest/v1/")

if [ "$STATUS" -lt "400" ]; then
    echo "✅ Success (HTTP $STATUS)"
else
    echo "❌ Failed (HTTP $STATUS)"
    echo "API access failed. This may indicate an invalid anon key or API restriction."
fi

# Test auth endpoint
echo -n "Testing Auth API access... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "apikey: $SUPABASE_ANON_KEY" "$SUPABASE_URL/auth/v1/")

if [ "$STATUS" -lt "400" ]; then
    echo "✅ Success (HTTP $STATUS)"
else
    echo "❌ Failed (HTTP $STATUS)"
    echo "Auth API access failed. This might indicate auth service issues."
fi

# Test JWT verification if secret is available
if [ ! -z "$SUPABASE_JWT_SECRET" ]; then
    echo -e "\n=== JWT Verification ==="
    echo "JWT secret is set in environment. Use the Python script for detailed JWT tests."
    echo "Run: python supabase_auth_diagnostic.py"
else
    echo -e "\n=== JWT Verification ==="
    echo "⚠️ SUPABASE_JWT_SECRET not set. JWT verification tests skipped."
    echo "For production, make sure to set this value from your Supabase dashboard."
fi

# Check for specific tables
echo -e "\n=== Testing table access ==="

# Function to check table existence using HEAD request
check_table() {
    local table=$1
    echo -n "Checking for '$table' table... "
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X HEAD -H "apikey: $SUPABASE_ANON_KEY" "$SUPABASE_URL/rest/v1/$table")
    
    if [ "$STATUS" -lt "400" ]; then
        echo "✅ Found (HTTP $STATUS)"
    else
        echo "❌ Not found (HTTP $STATUS)"
    fi
}

# Check important tables
check_table "llama_index_documents"
check_table "documents"

# Check storage buckets
echo -e "\n=== Testing storage access ==="
echo -n "Checking storage API... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "apikey: $SUPABASE_ANON_KEY" "$SUPABASE_URL/storage/v1/bucket")

if [ "$STATUS" -lt "400" ]; then
    echo "✅ Success (HTTP $STATUS)"
else
    echo "❌ Failed (HTTP $STATUS)"
    echo "Storage API access failed. This might indicate storage service issues."
fi

echo -e "\n=== Diagnostic Summary ==="
echo "For detailed authentication tests, run the Python diagnostic scripts:"
echo "- python supabase_diagnostic.py       (general Supabase connectivity)"
echo "- python supabase_auth_diagnostic.py  (authentication specific)"
echo ""
echo "Common issues:"
echo "1. Network/Firewall restrictions preventing access to Supabase"
echo "2. Incorrect SUPABASE_URL or SUPABASE_ANON_KEY"
echo "3. Missing tables or RLS policies"
echo "4. JWT authentication configuration"
