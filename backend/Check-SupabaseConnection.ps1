# Supabase Connection Check for Windows PowerShell
# This script tests connectivity to Supabase from your environment

Write-Host "=== Supabase Connection Diagnostic Tool ===" -ForegroundColor Cyan
Write-Host "This script will help diagnose connectivity issues with Supabase"

# Load environment variables from .env file if present
if (Test-Path .env) {
    Write-Host "Loading environment variables from .env file" -ForegroundColor Yellow
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            $name = $matches[1]
            $value = $matches[2]
            if ($name -and -not $name.StartsWith('#')) {
                [Environment]::SetEnvironmentVariable($name, $value)
            }
        }
    }
}

# Check if required environment variables are set
$SUPABASE_URL = [Environment]::GetEnvironmentVariable("SUPABASE_URL")
$SUPABASE_ANON_KEY = [Environment]::GetEnvironmentVariable("SUPABASE_ANON_KEY")

if (-not $SUPABASE_URL) {
    Write-Host "❌ SUPABASE_URL environment variable not set" -ForegroundColor Red
    exit 1
}

if (-not $SUPABASE_ANON_KEY) {
    Write-Host "❌ SUPABASE_ANON_KEY environment variable not set" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Basic connectivity tests ===" -ForegroundColor Cyan

# Extract domain from Supabase URL
$DOMAIN = $SUPABASE_URL -replace "https?://", ""

# Basic connectivity test
Write-Host "Testing basic connectivity to $DOMAIN... " -NoNewline
try {
    $ping = Test-Connection -ComputerName $DOMAIN -Count 1 -Quiet
    if ($ping) {
        Write-Host "✅ Success" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Failed" -ForegroundColor Red
        Write-Host "Cannot reach Supabase server. Check your network connection or firewall settings." -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ Failed" -ForegroundColor Red
    Write-Host "Error testing connectivity: $_" -ForegroundColor Red
}

# Test HTTPS connection
Write-Host "Testing HTTPS connection to $SUPABASE_URL... " -NoNewline
try {
    $response = Invoke-WebRequest -Uri $SUPABASE_URL -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "✅ Success" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed" -ForegroundColor Red
    Write-Host "Cannot establish HTTPS connection to Supabase URL." -ForegroundColor Red
    Write-Host "This may indicate network restrictions or incorrect URL." -ForegroundColor Red
}

# Test API endpoint with anon key
Write-Host "`n=== Testing API access ===" -ForegroundColor Cyan
Write-Host "Testing REST API access with anon key... " -NoNewline
try {
    $headers = @{
        "apikey" = $SUPABASE_ANON_KEY
    }
    $response = Invoke-WebRequest -Uri "$SUPABASE_URL/rest/v1/" -Headers $headers -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "✅ Success (HTTP $($response.StatusCode))" -ForegroundColor Green
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "❌ Failed (HTTP $statusCode)" -ForegroundColor Red
    Write-Host "API access failed. This may indicate an invalid anon key or API restriction." -ForegroundColor Red
}

# Test auth endpoint
Write-Host "Testing Auth API access... " -NoNewline
try {
    $headers = @{
        "apikey" = $SUPABASE_ANON_KEY
    }
    $response = Invoke-WebRequest -Uri "$SUPABASE_URL/auth/v1/" -Headers $headers -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "✅ Success (HTTP $($response.StatusCode))" -ForegroundColor Green
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "❌ Failed (HTTP $statusCode)" -ForegroundColor Red
    Write-Host "Auth API access failed. This might indicate auth service issues." -ForegroundColor Red
}

# Check JWT verification if secret is available
$SUPABASE_JWT_SECRET = [Environment]::GetEnvironmentVariable("SUPABASE_JWT_SECRET")
if ($SUPABASE_JWT_SECRET) {
    Write-Host "`n=== JWT Verification ===" -ForegroundColor Cyan
    Write-Host "JWT secret is set in environment. Use the Python script for detailed JWT tests." -ForegroundColor Yellow
    Write-Host "Run: python supabase_auth_diagnostic.py" -ForegroundColor Yellow
}
else {
    Write-Host "`n=== JWT Verification ===" -ForegroundColor Cyan
    Write-Host "⚠️ SUPABASE_JWT_SECRET not set. JWT verification tests skipped." -ForegroundColor Yellow
    Write-Host "For production, make sure to set this value from your Supabase dashboard." -ForegroundColor Yellow
}

# Function to check table existence using HEAD request
function Check-Table {
    param(
        [string]$tableName
    )
    Write-Host "Checking for '$tableName' table... " -NoNewline
    try {
        $headers = @{
            "apikey" = $SUPABASE_ANON_KEY
        }
        $response = Invoke-WebRequest -Uri "$SUPABASE_URL/rest/v1/$tableName" -Headers $headers -Method Head -UseBasicParsing -ErrorAction SilentlyContinue
        Write-Host "✅ Found (HTTP $($response.StatusCode))" -ForegroundColor Green
    }
    catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "❌ Not found (HTTP $statusCode)" -ForegroundColor Red
    }
}

# Check for specific tables
Write-Host "`n=== Testing table access ===" -ForegroundColor Cyan
Check-Table -tableName "llama_index_documents"
Check-Table -tableName "documents"

# Check storage buckets
Write-Host "`n=== Testing storage access ===" -ForegroundColor Cyan
Write-Host "Checking storage API... " -NoNewline
try {
    $headers = @{
        "apikey" = $SUPABASE_ANON_KEY
    }
    $response = Invoke-WebRequest -Uri "$SUPABASE_URL/storage/v1/bucket" -Headers $headers -UseBasicParsing -ErrorAction SilentlyContinue
    Write-Host "✅ Success (HTTP $($response.StatusCode))" -ForegroundColor Green
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "❌ Failed (HTTP $statusCode)" -ForegroundColor Red
    Write-Host "Storage API access failed. This might indicate storage service issues." -ForegroundColor Red
}

Write-Host "`n=== Diagnostic Summary ===" -ForegroundColor Cyan
Write-Host "For detailed authentication tests, run the Python diagnostic scripts:" -ForegroundColor Yellow
Write-Host "- python supabase_diagnostic.py       (general Supabase connectivity)" -ForegroundColor Yellow
Write-Host "- python supabase_auth_diagnostic.py  (authentication specific)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Common issues:" -ForegroundColor Yellow
Write-Host "1. Network/Firewall restrictions preventing access to Supabase" -ForegroundColor Yellow
Write-Host "2. Incorrect SUPABASE_URL or SUPABASE_ANON_KEY" -ForegroundColor Yellow
Write-Host "3. Missing tables or RLS policies" -ForegroundColor Yellow
Write-Host "4. JWT authentication configuration" -ForegroundColor Yellow
