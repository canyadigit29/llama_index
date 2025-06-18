#!/bin/bash
# This script can be run to check the status of external service connections

# Check OpenAI connection
echo "Testing OpenAI connection..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️ OPENAI_API_KEY is not set"
else
    echo "✓ OPENAI_API_KEY is set"
    # Only perform a simple test - don't waste tokens
    echo "You can test OpenAI connection with: curl https://api.openai.com/v1/models -H \"Authorization: Bearer $OPENAI_API_KEY\""
fi

# Check Pinecone connection
echo -e "\nTesting Pinecone connection..."
if [ -z "$PINECONE_API_KEY" ]; then
    echo "⚠️ PINECONE_API_KEY is not set"
else
    echo "✓ PINECONE_API_KEY is set"
fi

if [ -z "$PINECONE_ENVIRONMENT" ]; then
    echo "⚠️ PINECONE_ENVIRONMENT is not set"
else
    echo "✓ PINECONE_ENVIRONMENT is set to: $PINECONE_ENVIRONMENT"
fi

if [ -z "$PINECONE_INDEX_NAME" ]; then
    echo "⚠️ PINECONE_INDEX_NAME is not set or using default"
else
    echo "✓ PINECONE_INDEX_NAME is set to: $PINECONE_INDEX_NAME"
fi

# Check Supabase connection
echo -e "\nTesting Supabase connection..."
if [ -z "$SUPABASE_URL" ]; then
    echo "⚠️ SUPABASE_URL is not set"
else
    echo "✓ SUPABASE_URL is set to: $SUPABASE_URL"
fi

if [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "⚠️ SUPABASE_ANON_KEY is not set"
else
    echo "✓ SUPABASE_ANON_KEY is set"
fi

if [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "⚠️ SUPABASE_SERVICE_ROLE_KEY is not set"
else
    echo "✓ SUPABASE_SERVICE_ROLE_KEY is set"
fi

# Check network connectivity
echo -e "\nTesting network connectivity..."
echo "Ping to api.openai.com:"
ping -c 1 api.openai.com || echo "Could not reach api.openai.com"

echo "Testing HTTP connectivity to Pinecone API:"
curl -s -o /dev/null -w "%{http_code}\n" https://controller.$PINECONE_ENVIRONMENT.pinecone.io/actions/whoami -H "Api-Key: $PINECONE_API_KEY" || echo "Could not connect to Pinecone API"

echo "Testing HTTP connectivity to Supabase:"
curl -s -o /dev/null -w "%{http_code}\n" $SUPABASE_URL/rest/v1/ -H "apikey: $SUPABASE_ANON_KEY" || echo "Could not connect to Supabase"

echo -e "\nCheck completed. Review any warnings above."
echo "You can also check the /health and / endpoints of your application for more details."
