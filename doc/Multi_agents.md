# Multi-Agent Group Chat Sample Guide

This guide will help you set up, run, and test the multi-agent group chat sample application in this repository. The sample demonstrates how multiple Azure AI Agents can collaborate to answer user queries using both Retrieval Augmented Generation (RAG) and system plugins.

---

## 1. Prerequisites

- **Python 3.10+** installed
- **Azure resources**:
  - Azure OpenAI or OpenAI API access
  - Azure AI Search index (for RAG)
- **.env file**: Copy `.env.example` to `.env` and fill in your Azure credentials and resource info
- **Virtual environment**: Recommended for dependency isolation

---

## 2. Environment Setup

1. **Create and activate a virtual environment**

```bash
python -m venv ../.venv
../.venv\Scripts\activate  # On Windows
# or
source ../.venv/bin/activate  # On Unix/Mac
```

2. **Install dependencies**

```bash
pip install -r ../requirements.txt
```

3. **Configure environment variables**

Edit the `.env` file at the project root. Example:

```
AZURE_SEARCH_ENDPOINT=...
AZURE_SEARCH_API_KEY=...
AZURE_SEARCH_INDEX=...
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME=...
AZURE_AI_AGENT_ENDPOINT=...
```

---

## 3. Starting the Multi-Agent App

### Option 1: Use the Batch Script (Recommended for Windows)

From the `src` directory, run:

```cmd
run_multiagent.cmd
```

This script will:
- Check and optionally free up required ports
- Start all MCP servers (Weather, LocalTime, Azure Data Explorer)
- Start the multi-agent backend server (`multiagent_group.py`)
- Start the Chainlit frontend

Each service will open in its own terminal window.

### Option 2: Manual Startup

Open multiple terminals and start each service in order:

1. **Weather MCP Server**
    ```bash
    python mcpservers/weather.py
    ```
2. **LocalTime MCP Server**
    ```bash
    python mcpservers/localtime.py
    ```
3. **Azure Data Explorer MCP Server**
    ```bash
    python mcpservers/azuredataexproler.py
    ```
4. **Multi-Agent Backend**
    ```bash
    python multiagent/multiagent_group.py
    ```
5. **Chainlit Frontend**
    ```bash
    chainlit run frontend/app.py
    ```

---

## 4. Using the Application

1. Open your browser and go to: [http://localhost:8081](http://localhost:8081)
2. You will see the Chainlit chat interface.
3. Type a question 
  - Get me total number of events from the system log and average number of event per an hour  - What is the weather in Seattle?
  - What non-coffee options does Starbucks offer?
4. The system will:
   - Use FAQ memory for known questions
   - Use RAG for knowledge-based queries
   - Use system plugins for weather, time, or data explorer queries
   - Let multiple agents collaborate and present a consensus answer

---

## 5. Troubleshooting

- **Port conflicts**: The batch script can help you identify and kill processes using required ports.
- **Missing dependencies**: Run `pip install -r ../requirements.txt` in your venv.
- **Azure errors**: Double-check your `.env` values and Azure resource status.
- **Service not starting**: Check each terminal for error messages and resolve as needed.

---

## 6. Customization & Next Steps

- Add more agents or plugins for new capabilities
- Adjust agent instructions in `multiagent_group.py` for different behaviors
- Explore the code to understand how group chat orchestration works

---

## References

- [Semantic Kernel Documentation](https://learn.microsoft.com/semantic-kernel/)
- [Azure AI Agent Documentation](https://learn.microsoft.com/azure/ai-services/openai/how-to/agent-service)
- [Chainlit Documentation](https://docs.chainlit.io)

---

This guide should help you get started with the multi-agent group chat sample. For further questions or issues, check the logs in each service window or consult the documentation above.
