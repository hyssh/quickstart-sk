#!/usr/bin/env python3
"""
Efficient launcher for the Chainlit application with MCP servers.
This script manages all the services in a single process with proper cleanup.
"""
import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

class ServiceManager:
    def __init__(self, conda_env=None):
        self.conda_env = conda_env or os.environ.get('CONDA_ENV', 'sk')
        self.processes = []
        self.base_dir = Path(__file__).parent
        
    def get_conda_python(self):
        """Get the python executable from the conda environment."""
        if os.name == 'nt':  # Windows
            return f"conda run -n {self.conda_env} python"
        else:  # Unix-like
            return f"conda run -n {self.conda_env} python"
    
    def start_service(self, name, script_path, delay=0):
        """Start a service with optional delay."""
        if delay > 0:
            time.sleep(delay)
        
        full_path = self.base_dir / script_path
        cmd = f"{self.get_conda_python()} {full_path}"
        
        print(f"Starting {name}...")
        try:
            if os.name == 'nt':  # Windows
                process = subprocess.Popen(
                    cmd, 
                    shell=True, 
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:  # Unix-like
                process = subprocess.Popen(cmd, shell=True)
            
            self.processes.append((name, process))
            print(f"✓ {name} started (PID: {process.pid})")
            
        except Exception as e:
            print(f"✗ Failed to start {name}: {e}")
    
    def start_chainlit(self, app_path, delay=0):
        """Start the Chainlit application."""
        if delay > 0:
            time.sleep(delay)
        
        full_path = self.base_dir / app_path
        cmd = f"conda run -n {self.conda_env} chainlit run {full_path}"
        
        print(f"Starting Chainlit App...")
        try:
            if os.name == 'nt':  # Windows
                process = subprocess.Popen(
                    cmd, 
                    shell=True, 
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:  # Unix-like
                process = subprocess.Popen(cmd, shell=True)
            
            self.processes.append(("Chainlit App", process))
            print(f"✓ Chainlit App started (PID: {process.pid})")
            
        except Exception as e:
            print(f"✗ Failed to start Chainlit App: {e}")
    
    def start_all_services(self):
        """Start all services in the correct order."""
        print(f"Using conda environment: {self.conda_env}")
        print("=" * 50)
        
        # Start MCP servers first
        services = [
            ("Weather MCP Server", "mcpservers/weather.py"),
            ("LocalTime MCP Server", "mcpservers/localtime.py"),
            ("Azure Data Explorer MCP Server", "mcpservers/azuredataexproler.py"),
            ("Backend Server", "backend/server.py"),
        ]
        
        # Start services in parallel using threads
        threads = []
        for name, script_path in services:
            thread = threading.Thread(target=self.start_service, args=(name, script_path))
            thread.start()
            threads.append(thread)
        
        # Wait for all services to start
        for thread in threads:
            thread.join()
        
        # Give services time to initialize
        print("\nWaiting for services to initialize...")
        time.sleep(3)
        
        # Start Chainlit app last
        self.start_chainlit("frontend/app.py")
        
        print("\n" + "=" * 50)
        print("All services started!")
        print("Check the individual console windows for service status.")
        print("Press Ctrl+C to stop all services.")
    
    def cleanup(self):
        """Clean up all processes."""
        print("\nStopping all services...")
        for name, process in self.processes:
            try:
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    print(f"✓ Stopped {name}")
            except Exception as e:
                print(f"✗ Error stopping {name}: {e}")
    
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C signal."""
        self.cleanup()
        sys.exit(0)

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Launch Chainlit app with MCP servers')
    parser.add_argument('--env', '-e', default='sk', 
                       help='Conda environment name (default: sk or CONDA_ENV env var)')
    
    args = parser.parse_args()
    
    manager = ServiceManager(conda_env=args.env)
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, manager.signal_handler)
    
    try:
        manager.start_all_services()
        
        # Keep the main process alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        manager.cleanup()
    except Exception as e:
        print(f"Error: {e}")
        manager.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()
