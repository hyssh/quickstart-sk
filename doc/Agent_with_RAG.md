# Azure AI Agent with RAG Capability Guide

## Background

This guide explains how to run and test the Azure AI Agent with Retrieval Augmented Generation (RAG) capabilities. This solution combines the power of Azure AI Agent with Azure AI Search to create an intelligent agent that can answer questions based on your custom knowledge base.

### What is RAG?

Retrieval Augmented Generation (RAG) is an AI architecture that enhances large language models by:

1. Retrieving relevant information from a knowledge base
2. Augmenting the model's prompt with this retrieved information
3. Generating responses grounded in accurate, up-to-date information

This approach helps prevent hallucinations and provides more accurate answers based on your specific data.

### Architecture Overview

The solution consists of these components:

- **Azure AI Agent**: Orchestrates the conversation and reasoning
- **Azure AI Search**: Provides the vector search capabilities for retrieving relevant information
- **FAQ Memory**: Caches common questions for faster responses
- **FastAPI Backend**: Handles requests and communicates with Azure services
- **Chainlit Frontend**: Provides a user-friendly chat interface

## Prerequisites

Before starting, ensure you have:

1. **Python Environment**: Python 3.8+ with virtual environment
2. **Azure Resources**:
   - Azure OpenAI or OpenAI API access
   - Azure AI Search index with your knowledge base data
3. **Environment Variables**: Properly configured in a [`.env`](.env ) file

## Setup Instructions

### 1. Environment Configuration

Create a [`.env`](.env ) file in the project root with the following variables:

```
AZURE_OPENAI_ENDPOINT=https://your-azure-openai.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME=your-model-name
AZURE_SEARCH_INDEX=your-search-index-name
```

### 2. Install Dependencies

Create and activate a virtual environment, then install the required packages:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Application

You can start the application using the provided batch script or manually.

### Option 1: Using the Batch Script

The repository includes a convenient batch script to start all required services:

```bash
# Navigate to the src directory
cd src

# Run the startup script
run_agentrag.cmd
```

The script will:
1. Check and optionally kill processes using required ports
2. Start the backend server (agent_rag.py)
3. Start the Chainlit frontend

### Option 2: Manual Startup

If you prefer to start services manually:

1. **Start the Backend Server**:

```bash
# Activate virtual environment
.venv\Scripts\activate

# Start the backend
python src/backend/agent_rag.py
```

2. **Start the Chainlit Frontend** (in a separate terminal):

```bash
# Activate virtual environment
.venv\Scripts\activate

# Start Chainlit
chainlit run src/frontend/app.py
```

## Testing the Agent

Once both services are running:

1. Open a web browser and navigate to: `http://localhost:8081`
2. The Chainlit interface will appear with a welcome message
3. Type a question in the chat input and press Enter
4. The agent will:
   - Check if the question exists in FAQ memory
   - If not found, search the knowledge base using Azure AI Search
   - Generate a response based on the retrieved information

### Example Questions

Try asking questions relevant to your knowledge base, such as:

- "What are the key features of [your product]?"
- "How do I troubleshoot [common problem]?"
- "What is the process for [specific task]?"

## Understanding the Implementation

### Backend (agent_rag.py)

The backend implements:

1. **FAQ Memory**: A cache for frequent questions
2. **Azure AI Search Integration**: Connects to your search index
3. **Agent Management**: Creates and manages Azure AI Agent instances
4. **Thread Management**: Maintains conversation context across interactions

### Frontend (app.py)

The Chainlit frontend provides:

1. **User Interface**: A clean chat interface
2. **Session Management**: Tracks user sessions and agent/thread IDs
3. **Error Handling**: Graceful error reporting for users

## Advanced Features

### 1. Session Management

The system maintains session continuity by:
- Tracking agent and thread IDs
- Preserving conversation context across messages
- Allowing proper session reset when needed

### 2. FAQ Memory Optimization

Before querying the Azure AI Search index, the system checks an FAQ memory cache to:
- Provide faster responses for common questions
- Reduce API calls to Azure services
- Maintain consistent answers for frequent queries

## Troubleshooting

If you encounter issues:

1. **Port Conflicts**: Use the batch script's port checking feature to identify and resolve port conflicts
2. **Connection Errors**: Verify your Azure credentials in the [`.env`](.env ) file
3. **Search Index Issues**: Confirm your Azure AI Search index exists and is properly configured
4. **Agent Creation Failures**: Check Azure permissions and quotas

## Next Steps

Consider these enhancements:

1. **Multi-Agent Setup**: Implement specialized agents for different knowledge domains
2. **Plugin Integration**: Add MCP plugins for additional capabilities
3. **Web Browsing**: Enable web browsing capabilities for up-to-date information
4. **UI Customization**: Customize the Chainlit interface for your brand

## Resources

- [Semantic Kernel Documentation](https://learn.microsoft.com/semantic-kernel/)
- [Azure AI Agent Documentation](https://learn.microsoft.com/azure/ai-services/openai/how-to/agent-service)
- [Azure AI Search Documentation](https://learn.microsoft.com/azure/search/)
- [Chainlit Documentation](https://docs.chainlit.io)

---

This guide provides a starting point for working with your Azure AI Agent with RAG capabilities. As you become more familiar with the system, you can explore advanced features and customizations to better suit your specific use case.
