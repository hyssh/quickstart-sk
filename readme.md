# Semantic Kernel with FastAPI

This project demonstrates a Semantic Kernel implementation with FastAPI backend, Chainlit frontend, and multiple MCP (Model Context Protocol) servers for enhanced AI capabilities.

## Requirements

- Python 3.10+
- Azure AI Foundry project

## Quick Start

### 1. Azure CLI Login

Before setting up your environment, make sure you are logged in to Azure CLI:

```bash
az login
```

If you haven't installed Azure CLI, follow the [official guide](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest).

### 2. Environment Setup


**Environment**

Create a Python venv at the root of the project and install dependencies:

```bash
# Create venv at project root
python -m venv .venv

# Activate venv (Windows)
.venv\Scripts\activate
# Activate venv (Unix/Linux/Mac)
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and update with your values:

```bash
cp .env.example .env
```

Update the `.env` file with your Azure credentials:

```env
# Azure AI Agent Configuration
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME="gpt-4o"
AZURE_AI_AGENT_ENDPOINT="https://######.services.ai.azure.com/api/projects/#####"

# MCP Server Configuration (Optional)
AZURE_SEARCH_ENDPOINT="https://#####.search.windows.net"
AZURE_SEARCH_API_KEY="######"
AZURE_SEARCH_INDEX="#####"
ADX_CLUSTER_URL="https://#####.#####.kusto.windows.net"
ADX_DATABASE="######"
```

### 4. Running the Application

#### Option A: Enhanced Launcher (Recommended)

Navigate to the `src` directory and use the Python launcher:

```bash
cd src
python launcher.py
```

#### Option B: Enhanced Batch Script (Windows)

```bash
cd src
run_chainlit.cmd
```

#### Option C: Manual Start (Individual Components)

Start each component manually:

```bash
# Start MCP Servers
python src/mcpservers/weather.py
python src/mcpservers/localtime.py
python src/mcpservers/azuredataexproler.py

# Start Backend Server
python src/backend/server.py

# Start Chainlit Frontend
chainlit run src/frontend/app.py
```

## Services Overview

The application consists of multiple services:

1. **Weather MCP Server** - Provides weather information
2. **LocalTime MCP Server** - Provides local time information  
3. **Azure Data Explorer MCP Server** - Connects to Azure Data Explorer
4. **Backend Server** - FastAPI server for API endpoints
5. **Chainlit Frontend** - Interactive chat interface


## API Usage

### Testing the API

1. **Initial API Call**

   Make a POST request to the API endpoint with a user query:

   ```json
   {
     "user_input": "List controls for PCI DSS"
   }
   ```

   **Response:**
   ```json
   {
     "response": "The Payment Card Industry Data Security Standard (PCI DSS) version 4.0 is ...... kdown of the sub-requirements or details for a specific control, let me know!",
     "thread_id": "thread_Jeg8fCvvNlfk9CTUQQohZvuY",
     "agent_id": "asst_LuzQe28Sa9yNh2J9zRpA6HN8"
   }
   ```

2. **Follow-up API Call**

   Use the `thread_id` and `agent_id` from the previous response for conversation continuity:

   ```json
   {
     "user_input": "Use Markdown format",
     "thread_id": "thread_Jeg8fCvvNlfk9CTUQQohZvuY",
     "agent_id": "asst_LuzQe28Sa9yNh2J9zRpA6HN8"
   }
   ```

## Project Structure

```
quickstart-sk/
├── src/
│   ├── launcher.py              # Enhanced Python launcher
│   ├── run_chainlit.cmd         # Enhanced batch script
│   ├── README.md               # Launcher documentation
│   ├── backend/
│   │   └── server.py           # FastAPI backend
│   ├── frontend/
│   │   ├── app.py              # Chainlit frontend
│   │   ├── chainlit.md
│   │   └── chainlit.yaml
│   └── mcpservers/
│       ├── weather.py          # Weather MCP server
│       ├── localtime.py        # LocalTime MCP server
│       └── azuredataexproler.py # Azure Data Explorer MCP
├── sample-server/
│   ├── azureaisearch.py        # Azure AI Search MCP
│   └── azuresqldb.py           # Azure SQL DB MCP
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
└── readme.md                  # This file
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME` | Azure OpenAI model deployment name | Yes |
| `AZURE_AI_AGENT_ENDPOINT` | Azure AI Foundry endpoint URL | Yes |
| `AZURE_SEARCH_ENDPOINT` | Azure AI Search service endpoint | Optional |
| `AZURE_SEARCH_API_KEY` | Azure AI Search API key | Optional |
| `AZURE_SEARCH_INDEX` | Azure AI Search index name | Optional |
| `ADX_CLUSTER_URL` | Azure Data Explorer cluster URL | Optional |
| `ADX_DATABASE` | Azure Data Explorer database name | Optional |
| `CONDA_ENV` | Conda environment name for launchers | Optional (default: sk) |

## Troubleshooting

### Common Issues

1. **Conda environment not found**
   ```bash
   conda env list  # Check available environments
   conda create -n sk python=3.10  # Create if missing
   ```

2. **Port conflicts**
   - Backend typically runs on port 8091
   - Chainlit typically runs on port 8000
   - Make sure these ports are available

3. **Missing dependencies**
   ```bash
   conda activate sk
   pip install -r requirements.txt
   ```

4. **Azure authentication issues**
   - Verify your `.env` file has correct Azure credentials
   - Check Azure AI Foundry project permissions

### Logs and Debugging

- Each service runs in its own terminal window for easy monitoring
- Check individual service logs for specific error messages
- Use `python launcher.py --help` for launcher options

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
