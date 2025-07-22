# Chainlit Application Launcher

This directory contains multiple ways to efficiently run the Chainlit application with its MCP servers.

## Quick Start

### Option 1: Enhanced Batch Script (Windows)
```cmd
# Use default environment (sk)
run_chainlit.cmd

# Use custom environment
set CONDA_ENV=your_env_name && run_chainlit.cmd
```


### Option 2: Python Launcher (Cross-platform)
```bash
# Use default environment
python launcher.py

# Use custom environment
python launcher.py --env your_env_name
```

## Environment Setup

### Setting Custom Environment
You can set the conda environment in several ways:

1. **Environment Variable (All methods)**:
   ```cmd
   set CONDA_ENV=your_env_name  # Windows
   export CONDA_ENV=your_env_name  # Unix
   ```

2. **Command Line Argument (Python launcher)**:
   ```bash
   python launcher.py --env your_env_name
   ```

### Creating New Environment
If you need to create a new conda environment:

```bash
# Create environment with Python 3.10
conda create -n your_env_name python=3.10

# Activate environment
conda activate your_env_name

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

- ✅ Flexible conda environment selection
- ✅ Proper service startup order
- ✅ Individual terminal windows for each service (Windows)
- ✅ Graceful shutdown with Ctrl+C
- ✅ Cross-platform compatibility
- ✅ Auto-detection of environments
- ✅ Error handling and status reporting

## Troubleshooting

### Common Issues

1. **Conda not found**: Make sure Anaconda/Miniconda is installed and in your PATH
2. **Environment doesn't exist**: Use `conda env list` to see available environments
3. **Port conflicts**: Make sure ports used by the services aren't already in use
4. **Dependencies missing**: Run `pip install -r ../requirements.txt` in your conda environment

### Logs and Debugging

Each service runs in its own terminal window (Windows) or background process (Unix), so you can monitor their individual outputs for debugging.

## Recommendations

- **For Development**: Use the Python launcher (`launcher.py`) for better process management
- **For Quick Testing**: Use the enhanced batch script (`run_chainlit.cmd`)
