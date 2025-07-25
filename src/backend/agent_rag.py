import sys
import os
import logging
from fastapi import FastAPI, HTTPException
from azure.identity.aio import DefaultAzureCredential
from typing import Optional
from dotenv import load_dotenv
from azure.ai.agents.models import AzureAISearchTool
from azure.ai.projects.models import ConnectionType
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentThread, AzureAIAgentSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from pydantic import BaseModel
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from memory.faq_memory import FAQMemory


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

AGENT_NAME = "AI-Agent-rag"   
AZURE_AI_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX")

ai_agent_settings = AzureAIAgentSettings()
faq_memory = FAQMemory()

async def get_faq_memory(query: str = None, category: str = None, limit: int = 1, score: float = 0.21):
    """Get the FAQ memory instance."""
    if query is not None:
        results = await faq_memory.search_faq(query, category, limit, score)
        if results is None or len(results) == 0:
            return None
    else:
        results = None
    return results

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

    cache_search_result = await get_faq_memory(query=user_input, category=None, limit=1, score=0.25)

    logging.info("Cache search result: %s", cache_search_result)
    if cache_search_result is not None:
        return {    
            "response": cache_search_result[0].answer
        }        
    
    print("No cache search result found, proceeding with agent response...")

    async with (
        # 1. Login to Azure and create a Azure AI Project Client
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ): 
        ai_search_conn_id = ""
        async for connection in client.connections.list():
            if connection.type == ConnectionType.AZURE_AI_SEARCH:
                ai_search_conn_id = connection.id
                print(f"Found Azure AI Search connection: {connection.id}")
                break

        ai_search = AzureAISearchTool(index_connection_id=ai_search_conn_id, index_name=AZURE_AI_SEARCH_INDEX_NAME)
        print(f"Using Azure AI Search index: {AZURE_AI_SEARCH_INDEX_NAME}")

        if agent_id is None:
            # Initial call
            agent = AzureAIAgent(
                client=client,
                definition = await client.agents.create_agent(
                    model=os.environ.get("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"),
                    name=AGENT_NAME,
                    description="An agent that can answer questions for user.",
                    instructions="You are an assistant Agent for answering questions. Your conversation is grounded in the context of the user query and data from search or knowledge base. outside of that. Do not make up answers. If you do not know the answer, say 'I don't know'.",
                    temperature=0.1,
                    top_p=0.1,                            
                ),
                tools=ai_search.definitions,
                tool_resources=ai_search.resources,
                headers={"x-ms-enable-preview": "true"},
            )
            logging.info("Created new agent: %s", agent.id)
        else:
            # Second call with existing agent and thread
            agent_def = await client.agents.get_agent(agent_id=agent_id)
            agent = AzureAIAgent(
                client=client,
                definition=agent_def,
                tools=ai_search.definitions,
                tool_resources=ai_search.resources,
                headers={"x-ms-enable-preview": "true"},
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
