@echo off
echo Backing up original vector_store_config.py...
copy vector_store_config.py vector_store_config.py.bak
echo Replacing with fixed version...
copy vector_store_config.py.new vector_store_config.py
echo Done!

echo Creating a copy in the backend folder...
copy vector_store_config.py backend/vector_store_config.py
echo Complete!
