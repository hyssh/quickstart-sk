import sys
import os
import logging
import asyncio
from fastapi import FastAPI, HTTPException
from azure.identity.aio import DefaultAzureCredential
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from azure.ai.agents.models import AzureAISearchTool, CodeInterpreterTool
from azure.ai.projects.models import ConnectionType
from semantic_kernel.agents import AgentGroupChat, AzureAIAgent, AzureAIAgentThread, AzureAIAgentSettings
from semantic_kernel.agents.strategies import TerminationStrategy
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.connectors.mcp import MCPStreamableHttpPlugin
from pydantic import BaseModel
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from memory.faq_memory import FAQMemory
from semantic_kernel.functions import kernel_function

logging.basicConfig(level=logging.INFO)

load_dotenv()

app = FastAPI()

class ChatRequest(BaseModel):
    user_input: str
    thread_id: Optional[str] = None
    chat_history: Optional[ChatHistory] = None

# Agent names
RAG_AGENT_NAME = "Coffee-Knowledge-Expert"
MCP_AGENT_NAME = "Systemadmin-Expert"

# Azure AI Search index name
AZURE_AI_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX")

# FAQ memory instance
faq_memory = FAQMemory()

@kernel_function(
    description="Get the best answer for a specific question from the FAQ database",
    name="get_faq_memory"
)
async def get_faq_memory(query: str = None, category: str = None, limit: int = 1, score: float = 0.21):
    """Get the FAQ memory instance."""
    if query is not None:
        results = await faq_memory.search_faq(query, category, limit, score)
        if results is None or len(results) == 0:
            return None
    else:
        results = None
    return results

class ConsensusTerminationStrategy(TerminationStrategy):
    """Terminates when all agents agree on an answer or reach max iterations."""
    
    def __init__(self, agents, maximum_iterations=5):
        super().__init__(agents=agents, maximum_iterations=maximum_iterations)
        
    async def should_agent_terminate(self, agent, history):
        """Check if the conversation should terminate."""
        # If we only have one message in history (the user query), continue
        if len(history) <= 1:
            return False
            
        # If we've reached max iterations, terminate
        if len(history) >= self.maximum_iterations * len(self.agents) + 1:
            return True
            
        # If both agents have answered and the last agent indicated completion
        if len(history) >= 3 and "FINAL ANSWER:" in history[-1].content:
            return True
            
        return False

class AgentFactory:
    """Factory for creating different types of agents."""
    
    def __init__(self, client):
        self.client = client
        
    async def create_rag_agent(self) -> AzureAIAgent:
        """Create a RAG agent with Azure AI Search capabilities."""
        ai_search_conn_id = ""
        async for connection in self.client.connections.list():
            if connection.type == ConnectionType.AZURE_AI_SEARCH:
                ai_search_conn_id = connection.id
                logging.info(f"Found Azure AI Search connection: {connection.id}")
                break
        
        if not ai_search_conn_id:
            raise HTTPException(status_code=500, detail="Azure AI Search connection not found")
        
        ai_search = AzureAISearchTool(index_connection_id=ai_search_conn_id, index_name=AZURE_AI_SEARCH_INDEX_NAME)
        
        agent_def = await self.client.agents.create_agent(
            model=os.environ.get("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"),
            name=RAG_AGENT_NAME,
            description="A knowledge expert, and Starbucks coffee enthusiast, that can search through documents to find information.",
            instructions="""You are a knowledge expert who can search through memories, documents and knowledge bases to find information.
            
            When asked a question:
            1. Starbucks related questions should be answered using the FAQ memory
            2. Else, use the Azure AI Search tool to find relevant documents
            3. If you don't find relevant information, state what you tried and that you couldn't find an answer
            4. When you're confident in your final answer, begin your response with "FINAL ANSWER:" 
            5. Collaborate with the System Expert to provide the most comprehensive answer
            """,
            temperature=0.1,
            top_p=0.1,                            
        )
        
        return AzureAIAgent(
            client=self.client,
            definition=agent_def,
            tools=ai_search.definitions,
            tool_resources=ai_search.resources,
            headers={"x-ms-enable-preview": "true"},
        )
        
    async def create_mcp_agent(self, plugins: List[MCPStreamableHttpPlugin]) -> AzureAIAgent:
        """Create an MCP Plugin agent with system capabilities."""
        code_interpreter = CodeInterpreterTool()
        
        agent_def = await self.client.agents.create_agent(
            model=os.environ.get("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME"),
            name=MCP_AGENT_NAME,
            description="A system expert who can access system information and perform system operations.",
            instructions="""You are a system expert who can retrieve weather information, system time, and monitor system operations.
            
            When asked a question:
            1. If it relates to weather, use the Weather plugin to get current weather information
            2. If it relates to time, use the GetSystemLocalTime plugin to get the current time
            3. If it relates to system monitoring, use the SystemLogRepository plugin
            4. Use the code interpreter when calculations or data processing is needed
            5. When you're confident in your final answer, begin your response with "FINAL ANSWER:"
            6. Collaborate with the Knowledge Expert to provide the most comprehensive answer
            """,
            temperature=0.1,
            top_p=0.1,                            
        )
        
        return AzureAIAgent(
            client=self.client,
            definition=agent_def,
            plugins=plugins,
            tools=code_interpreter.definitions,
            tool_resources=code_interpreter.resources
        )

@app.post("/reset_threads")
async def reset_threads(thread_id: Optional[str] = None):
    """Reset agent threads."""
    async with DefaultAzureCredential() as creds, AzureAIAgent.create_client(credential=creds) as client:
        if thread_id:
            try:
                await client.agents.threads.delete(thread_id=thread_id)
                logging.info(f"Deleted thread {thread_id}")
            except Exception as e:
                logging.error(f"Error deleting thread {thread_id}: {str(e)}")
    
    return {
        "message": "Reset completed successfully",
        "thread_id": thread_id
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat requests using a collaborative agent approach."""
    user_input = request.user_input
    thread_id = request.thread_id
    
    logging.info(f"User input: {user_input}")
    logging.info(f"Thread ID: {thread_id}")
    
    # First check FAQ memory for a cached answer
    cache_search_result = await get_faq_memory(query=user_input, category=None, limit=1, score=0.25)
    if cache_search_result is not None:
        logging.info(f"Found answer in FAQ memory: {cache_search_result[0].answer}")
        return {    
            "response": cache_search_result[0].answer,
            "thread_id": thread_id
        }
    
    async with (
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
        MCPStreamableHttpPlugin(
            name="Weather",
            description="Get current weather information",
            url="http://localhost:8086/mcp"
        ) as weather_plugin,
        MCPStreamableHttpPlugin(
            name="GetSystemLocalTime",
            description="System local time plugin for retrieving current system time",
            url="http://localhost:8087/mcp"
        ) as time_plugin,
        MCPStreamableHttpPlugin(
            name="SystemLogRepository",
            description="System log repository for monitoring and debugging",
            url="http://localhost:8089/mcp"
        ) as syslog_plugin,
    ):
        try:
            # Create agents
            agent_factory = AgentFactory(client)
            rag_agent = await agent_factory.create_rag_agent()
            mcp_agent = await agent_factory.create_mcp_agent([weather_plugin, time_plugin, syslog_plugin])
            
            # Set up the group chat
            group_chat = AgentGroupChat(
                agents=[rag_agent, mcp_agent],
                termination_strategy=ConsensusTerminationStrategy(agents=[rag_agent, mcp_agent], maximum_iterations=5)
            )
            
            # Start the conversation
            await group_chat.add_chat_message(message=user_input)
            
            # Collect all messages from the group chat
            responses = []
            async for content in group_chat.invoke():
                responses.append({
                    "role": content.role,
                    "name": content.name,
                    "content": content.content
                })
                logging.info(f"Agent response - {content.name}: {content.content}")
            
            # Extract the final answer
            final_answer = None
            for response in reversed(responses):
                if "FINAL ANSWER:" in response["content"]:
                    final_answer = response["content"].replace("FINAL ANSWER:", "").strip()
                    break
            
            if not final_answer and responses:
                # If no final answer was explicitly marked, use the last response
                final_answer = responses[-1]["content"]
            
            # Cleanup resources
            await group_chat.reset()
            
            # Return the thread_id from the group chat for future reference
            chat_thread_id = thread_id  # In this implementation we don't use thread_id
            
            return {
                "response": final_answer,
                "thread_id": chat_thread_id,
                "full_conversation": responses
            }
            
        except Exception as e:
            logging.error(f"Error in group chat: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("*" * 50)
    print("Starting Collaborative Multiagent Semantic Kernel server")
    print("This server implements a collaborative approach where multiple agents work together")
    print("*" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8091, log_level="info")