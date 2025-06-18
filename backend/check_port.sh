# Port Check Script
# This script runs on startup to check port availability and binding
# in the Railway container environment.

PORT=${1:-8000}
echo "=========== PORT CHECK & DEBUG SCRIPT ==========="
echo "Checking for port availability and processes..."

# Display all ports being listened on
echo "Current listening ports:"
netstat -tulpn 2>/dev/null || echo "netstat command not available"

# Check if something is running on port 8000
echo "Checking port 8000 specifically:"
netstat -tulpn | grep -E ':8000\s' 2>/dev/null || echo "Port 8000 appears to be free"

# Check if something is running on port 8080
echo "Checking port 8080 specifically:"
netstat -tulpn | grep -E ':8080\s' 2>/dev/null || echo "Port 8080 appears to be free"

# Try a simple port check with Python
echo "Python port check:"
python -c "
import socket
def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    if result == 0:
        print(f'Port {port} is in use')
    else:
        print(f'Port {port} is free')
    sock.close()

check_port(8000)
check_port(8080)
"

# Report environment PORT value
echo "Environment PORT variable is: $PORT"
echo "Railway expects service to be running on port 8000"
echo "============== END PORT CHECK =================="
