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
    def __init__(self):
        self.processes = []
        self.base_dir = Path(__file__).parent
        
    def get_venv_python(self):
        """Get the python executable from the .venv environment."""
        venv_path = self.base_dir.parent / ".venv"
        if os.name == 'nt':  # Windows
            return str(venv_path / "Scripts" / "python.exe")
        else:
            return str(venv_path / "bin" / "python")

    def start_service(self, name, script_path, delay=0):
        """Start a service with optional delay."""
        if delay > 0:
            time.sleep(delay)
        full_path = self.base_dir / script_path
        cmd = f'"{self.get_venv_python()}" "{full_path}"'
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
        cmd = f'"{self.get_venv_python()}" -m chainlit run "{full_path}"'
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

    def check_ports(self, ports):
        """Check and optionally kill processes using the specified ports."""
        import psutil
        import socket
        active_ports = {}
        for port in ports:
            pids = set()
            for conn in psutil.net_connections():
                if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    if conn.pid:
                        pids.add(conn.pid)
            if pids:
                active_ports[port] = pids
        if active_ports:
            print("\nThe following ports are in use:")
            for port, pids in active_ports.items():
                print(f"  Port {port}: PIDs {', '.join(map(str, pids))}")
            resp = input("\nDo you want to kill these processes? (y/n): ").strip().lower()
            if resp == 'y':
                for port, pids in active_ports.items():
                    for pid in pids:
                        try:
                            p = psutil.Process(pid)
                            p.terminate()
                            print(f"✓ Killed PID {pid} on port {port}")
                        except Exception as e:
                            print(f"✗ Could not kill PID {pid} on port {port}: {e}")
            else:
                print("Skipping killing processes.")
        else:
            print("No active processes found on the specified ports.")

    def start_all_services(self):
        """Start all services in the correct order."""
        print(f"Using .venv environment at: {self.base_dir.parent / '.venv'}")
        print("=" * 50)
        # Port logic
        ports = [8089, 8087, 8091, 8086, 8000, 8501]
        try:
            import psutil
        except ImportError:
            print("psutil not found. Installing...")
            subprocess.check_call([self.get_venv_python(), "-m", "pip", "install", "psutil"])
            import psutil
        resp = input(f"Do you want to check which processes are using ports {ports}? (y/n): ").strip().lower()
        if resp == 'y':
            self.check_ports(ports)
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
    manager = ServiceManager()
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
