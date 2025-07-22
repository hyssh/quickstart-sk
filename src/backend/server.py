import os
import logging
from fastapi import FastAPI, HTTPException
from azure.identity.aio import DefaultAzureCredential
from typing import Optional
from dotenv import load_dotenv
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentThread, AzureAIAgentSettings
from azure.ai.agents.models import CodeInterpreterTool
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.connectors.mcp import MCPSsePlugin
from pydantic import BaseModel

logging.basicConfig(level=logging.ERROR)

load_dotenv()

app = FastAPI()
"""
Create dependency injection for the agent
This is a simple chat application using FastAPI and Semantic Kernel.
"""

class ChatRequest(BaseModel):
    user_input: str
    agent_id: Optional[str] = None
    thread_id: Optional[str] = None    
    chat_history: Optional[ChatHistory] = None

AGENT_NAME = "AI-Agent-with-MCP"   

@app.post("/reset_agent_thread_id")
async def delete_agent_thread(agent_id:Optional[str] = None, thread_id:Optional[str] = None):
    """
    Reset the agent thread ID.
    This is useful for starting a new conversation with the agent.
    """
    logging.info("Resetting agent thread ID")
    
    async with (
        # 1. Login to Azure and create a Azure AI Project Client
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        logging.info("Deleting thread with ID: %s for agent ID: %s", thread_id, agent_id)
        if (agent_id is None) or (thread_id is None):
            raise HTTPException(status_code=400, detail="Agent ID is required to reset thread.")
        else:
            # Second call with existing agent and thread
            agent_def = await client.agents.get_agent(agent_id=agent_id)
            agent = AzureAIAgent(
                client=client,
                definition=agent_def
            )
            logging.info("Using existing agent: %s", agent.id)

            await client.agents.threads.delete(thread_id=thread_id)
            await client.agents.delete_agent(agent_id=agent_id)
    return {
        "message": "Agent thread reset successfully.",
        "agent_id": agent_id,
        "thread_id": thread_id
    }
    

@app.post("/chat")
async def chat(request: ChatRequest):
    user_input = request.user_input
    agent_id = request.agent_id
    thread_id = request.thread_id

    logging.info("User input: %s", user_input)
    logging.info("Agent ID: %s", agent_id)
    logging.info("Thread ID: %s", thread_id)
    AGENT_NAME = "MCP-Demo-Agent"   

    async with (
        # 1. Login to Azure and create a Azure AI Project Client
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
        # 2. Create the MCP plugins
        MCPSsePlugin(
            name="Weather",
            description="Get current weather information",
            url="http://localhost:8086/sse"
        ) as current_weather_plugin,
        MCPSsePlugin(
            name="GetSystemLocalTime",
            description="System local time plugin for retrieving current system time",
            url="http://localhost:8087/sse"
        ) as current_time_plugin,
        MCPSsePlugin(
            name="SystemLogRepository",
            description="System log repository for monitoring and debugging",
            url="http://localhost:8089/sse"
        ) as sys_log_ads_plugin,
    ): 
        code_interpreter = CodeInterpreterTool()
        
        if agent_id is None:
            # Initial call
            logging.info("Created new plugin: %s", sys_log_ads_plugin.name)
            agent = AzureAIAgent(
                client=client,
                definition = await client.agents.create_agent(
                    model=os.environ.get("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"),
                    name=AGENT_NAME,
                    description="An agent that can answer questions about system monitoring, weather, and current time.",
                    instructions="You are an assistant Agent for answering questions about system monitoring, weather, and current time. You can use the SystemLogRepository plugin to log system events and retrieve logs. Use the Weather plugin to get current weather information and the GetSystemLocalTime plugin to retrieve the current system time.",
                    temperature=0.1,
                    top_p=0.1,                            
                ),
                plugins=[sys_log_ads_plugin, current_weather_plugin, current_time_plugin],
                tools=code_interpreter.definitions,
                tool_resources=code_interpreter.resources
            )
            logging.info("Created new agent: %s", agent.id)
        else:
            # Second call with existing agent and thread
            agent_def = await client.agents.get_agent(agent_id=agent_id)
            agent = AzureAIAgent(
                client=client,
                definition=agent_def,
                plugins=[sys_log_ads_plugin, current_weather_plugin, current_time_plugin], # Important, it need to be added again
                tools=code_interpreter.definitions,
                tool_resources=code_interpreter.resources
            )
            logging.info("Using existing agent: %s", agent.id)

        # Create user message
        user_message = ChatMessageContent(
            role=AuthorRole.USER,
            items=[
                TextContent(text=user_input),
            ]
        )
        
        # Get response from agent, passing the user message
        logging.info("Getting response from agent...")
        thread = None
        # If thread_id is not provided in the request, try to get it from the singleton manager
        if thread_id is not None:            
            logging.info("Using thread ID from request: %s", thread_id)
            thread = AzureAIAgentThread(client=client, thread_id=thread_id)
            logging.info("Retrieved existing thread: %s", thread.id if thread else "None")
        
        # Let agent handle thread creation if needed
        if thread_id:
            try:
                logging.info("Attempting to use thread ID: %s", thread_id)
                response = await agent.get_response(messages=user_message, thread=thread)
            except Exception as e:
                logging.error("Error with existing thread ID %s: %s", thread_id, str(e))
                raise HTTPException(status_code=500, detail=f"Error with existing thread ID {thread_id}: {str(e)}")
        else:
            logging.info("No thread ID available, creating new thread")
            response = await agent.get_response(messages=user_message)
                
        logging.info("Response received from agent.")
        logging.info("Agent response: %s", response.content.content if hasattr(response.content, 'content') else response.content)
        
        return {    
            "response": response.content.content if hasattr(response.content, 'content') else response.content,
            "thread_id": response.thread.id,
            "agent_id": str(agent.id) if agent else None,
        }

if __name__ == "__main__":
    import uvicorn
    print("*"*50)
    print("Starting Semantic Kernel server")
    print("This server is responsible for handling requests to the Semantic Kernel.")
    print("*"*50)
    uvicorn.run(app, host="0.0.0.0", port=8091, log_level="info")