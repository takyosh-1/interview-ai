import signal
import sys
import subprocess
import os
from config.settings import running_servers

def cleanup_servers():
    for employee_id in list(running_servers.keys()):
        server_info = running_servers[employee_id]
        print(f"Shutting down server for employee {employee_id}")
        
        if 'server' in server_info:
            try:
                server_info['server'].shutdown()
            except Exception as e:
                print(f"Error shutting down server: {e}")
        
        if 'process' in server_info:
            try:
                server_info['process'].terminate()
                server_info['process'].wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_info['process'].kill()
            except Exception as e:
                print(f"Error terminating process: {e}")
        
        if 'server_file' in server_info:
            try:
                os.remove(server_info['server_file'])
            except Exception as e:
                print(f"Error removing server file: {e}")
        
        del running_servers[employee_id]

def signal_handler(sig, frame):
    print("\nShutting down all servers...")
    cleanup_servers()
    sys.exit(0)
