import signal
import sys
import subprocess
import os
import logging
from config.settings import running_servers

logger = logging.getLogger(__name__)

def cleanup_servers():
    logger.info(f"Starting cleanup of {len(running_servers)} running servers")
    for employee_id in list(running_servers.keys()):
        server_info = running_servers[employee_id]
        logger.info(f"Shutting down server for employee {employee_id}")
        
        if 'server' in server_info:
            try:
                server_info['server'].shutdown()
                logger.info(f"Successfully shut down server for employee {employee_id}")
            except Exception as e:
                logger.error(f"Error shutting down server for employee {employee_id}: {e}")
        
        if 'process' in server_info:
            try:
                server_info['process'].terminate()
                server_info['process'].wait(timeout=5)
                logger.info(f"Successfully terminated process for employee {employee_id}")
            except subprocess.TimeoutExpired:
                server_info['process'].kill()
                logger.warning(f"Force killed process for employee {employee_id}")
            except Exception as e:
                logger.error(f"Error terminating process for employee {employee_id}: {e}")
        
        if 'server_file' in server_info:
            try:
                os.remove(server_info['server_file'])
                logger.info(f"Successfully removed server file for employee {employee_id}")
            except Exception as e:
                logger.error(f"Error removing server file for employee {employee_id}: {e}")
        
        del running_servers[employee_id]
    
    logger.info("Server cleanup completed")

def signal_handler(sig, frame):
    logger.info(f"Received signal {sig}, shutting down all servers...")
    cleanup_servers()
    logger.info("Application shutdown complete")
    sys.exit(0)
