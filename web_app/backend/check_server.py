"""Check if the backend server is running and accessible."""
import requests
import sys

def check_server():
    base_url = "http://localhost:5000"
    
    print("=" * 80)
    print("Checking Backend Server Status")
    print("=" * 80)
    
    # Check health endpoint
    try:
        print(f"\n[1] Checking health endpoint: {base_url}/api/health")
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"    Status: {response.status_code}")
        print(f"    Response: {response.json()}")
        print("    [OK] Server is running and accessible!")
    except requests.exceptions.ConnectionError:
        print("    [ERROR] Connection refused - Server is not running or not accessible")
        print("    [INFO] Start the server with: python app.py")
        return False
    except requests.exceptions.Timeout:
        print("    [ERROR] Request timeout - Server may be slow or unresponsive")
        return False
    except Exception as e:
        print(f"    [ERROR] Error: {e}")
        return False
    
    # Check simulation status endpoint
    try:
        print(f"\n[2] Checking simulation status: {base_url}/api/simulation/status")
        response = requests.get(f"{base_url}/api/simulation/status", timeout=5)
        print(f"    Status: {response.status_code}")
        print(f"    Response: {response.json()}")
        print("    [OK] Simulation status endpoint is working!")
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("Server Status: [OK] RUNNING")
    print("=" * 80)
    return True

if __name__ == "__main__":
    if not check_server():
        print("\n" + "=" * 80)
        print("TROUBLESHOOTING:")
        print("=" * 80)
        print("1. Make sure the backend server is running:")
        print("   cd web_app/backend")
        print("   python app.py")
        print("\n2. Check if port 5000 is already in use:")
        print("   netstat -ano | findstr :5000")
        print("\n3. Try accessing the health endpoint in your browser:")
        print("   http://localhost:5000/api/health")
        print("\n4. Check firewall settings if connection is still refused")
        sys.exit(1)
