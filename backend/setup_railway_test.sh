#!/bin/bash

# Minimal requirements file for Railway test app
echo -e "fastapi==0.110.0\nuvicorn==0.27.1" > requirements.txt.minimal

# Create a backup of the original requirements file
cp requirements.txt requirements.txt.backup

# Replace with minimal requirements
mv requirements.txt.minimal requirements.txt

echo "✅ Created minimal requirements.txt for Railway test app"
echo "The original file has been backed up as requirements.txt.backup"
echo ""
echo "To deploy the test app to Railway:"
echo "1. Use the start command: uvicorn railway_test_app:app --host 0.0.0.0 --port \$PORT"
echo "2. Deploy to Railway"
echo ""
echo "To restore the original requirements:"
echo "mv requirements.txt.backup requirements.txt"
