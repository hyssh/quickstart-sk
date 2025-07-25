# Chainlit Application Launcher

This directory contains multiple ways to efficiently run the Chainlit application with its MCP servers.

## Quick Start

### Option 1: Enhanced Batch Script (Windows)
```cmd
run_chainlit.cmd
```

### Option 2: Python Launcher (Cross-platform)
```bash
python launcher.py
```

## Environment Setup

### Creating and Activating a Python venv

Create a Python venv at the project root and install dependencies:

```bash
# Create venv at the project root
python -m venv ../.venv

# Activate venv (Windows)
../.venv\Scripts\activate
# Activate venv (Unix/Linux/Mac)
source ../.venv/bin/activate

# Install requirements
pip install -r ../requirements.txt
```

## Services Started

The launcher starts the following services:

1. **Weather MCP Server** (`mcpservers/weather.py`)
2. **LocalTime MCP Server** (`mcpservers/localtime.py`)
3. **Azure Data Explorer MCP Server** (`mcpservers/azuredataexproler.py`)
4. **Backend Server** (`backend/server.py`)
5. **Chainlit Frontend** (`frontend/app.py`)

## Features

- ✅ Proper service startup order
- ✅ Individual terminal windows for each service (Windows)
- ✅ Graceful shutdown with Ctrl+C
- ✅ Cross-platform compatibility
- ✅ Error handling and status reporting

## Troubleshooting

### Common Issues

1. **venv not found**: Make sure you created the venv at the project root and activated it
2. **Port conflicts**: Make sure ports used by the services aren't already in use, if they are the script will ask you if you want to have them automatically closed
3. **Dependencies missing**: Run `pip install -r ../requirements.txt` in your venv

### Logs and Debugging

Each service runs in its own terminal window (Windows) or background process (Unix), so you can monitor their individual outputs for debugging.

## Recommendations

- **For Development**: Use the Python launcher (`launcher.py`) for better process management
- **For Quick Testing**: Use the enhanced batch script (`run_chainlit.cmd`)
