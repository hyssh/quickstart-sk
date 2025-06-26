import os
import logging
from fastapi import FastAPI, HTTPException
from azure.identity.aio import DefaultAzureCredential
from typing import Optional
from dotenv import load_dotenv
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentThread, AzureAIAgentSettings
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


agent_settings = AzureAIAgentSettings(
    endpoint=os.environ.get("PROJECT_ENDPOINT"),
    model_deployment_name=os.environ.get("MODEL_DEPLOYMENT_NAME") or "gpt-4.1"
)

@app.post("/chat")
async def chat(request: ChatRequest):
    user_input = request.user_input
    agent_id = request.agent_id
    thread_id = request.thread_id

    logging.info("User input: %s", user_input)
    logging.info("Agent ID: %s", agent_id)
    logging.info("Thread ID: %s", thread_id)
    AGENT_NAME = "PCIDSSAgent"   

    async with (
        # 1. Login to Azure and create a Azure AI Project Client
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
        # 2. Create the MCP plugin
        MCPSsePlugin(
            name="PCIDSSKnowledgeBase",
            description="PCI DSS version 4 knowledge in Azure AI Search",
            url="http://localhost:8088/sse"
        ) as pic_dss_knowledge_base_plugin,
    ): 
        if agent_id is None:
            # Initial call
            logging.info("Created new plugin: %s", pic_dss_knowledge_base_plugin.name)
            agent = AzureAIAgent(
                client=client,
                definition = await client.agents.create_agent(
                    model=agent_settings.model_deployment_name,
                    name=AGENT_NAME,
                    description="PCI DSS version 4.0 knowledge agent",
                    instructions="You are an assistant Agent. Answer questions. Use PCIDSSKnwowledgeBase to answer questions. Knowledgable PCI DSS version 4.0. You will answer general questions and also PCI DSS version 4.0, which is the latest version of the Payment Card Industry Data Security Standard (PCI DSS). You will use the Azure AI Search MCP to find relevant documents and provide accurate answers to user queries.",
                    temperature=0.1,
                    top_p=0.1,                            
                ),
                plugins=[pic_dss_knowledge_base_plugin],
            )
            logging.info("Created new agent: %s", agent.id)
        else:
            # Second call with existing agent and thread
            agent_def = await client.agents.get_agent(agent_id=agent_id)
            agent = AzureAIAgent(
                client=client,
                definition=agent_def,
                plugins=[pic_dss_knowledge_base_plugin], # Important, it need to be added again
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
    import asyncio
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8091, log_level="info")