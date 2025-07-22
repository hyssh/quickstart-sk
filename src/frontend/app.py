import chainlit as cl
import requests
import uuid
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Dictionary to store session IDs and user data
sessions = {}

@cl.on_chat_start
async def on_chat_start():
    """Initialize the chat session when a new chat is started"""
    # Clear any stored messages
    cl.user_session.set("messages", [])
    
    # Get session ID if it exists
    session_id = cl.user_session.get("session_id")
    
    # If this is a brand new session (first time user loads the app)
    if not session_id:
        # Create a new session ID
        session_id = str(uuid.uuid4())
        cl.user_session.set("session_id", session_id)
        sessions[session_id] = {
            "agent_id": None,
            "thread_id": None
        }
        await cl.Message(content="Welcome! I am an intelligent AI Assistant running Semantic Kernel with MCPPlugins. How can I help you?", author="System").send()
        return
        
    # If it's an existing session
    if session_id and session_id in sessions:
        # Check if there are existing agent_id and thread_id
        agent_id = sessions[session_id].get("agent_id")
        thread_id = sessions[session_id].get("thread_id")
        
        logging.info(f"Resetting session: {session_id}, agent_id: {agent_id}, thread_id: {thread_id}")
        
        # If both agent_id and thread_id exist, call the reset endpoint
        if agent_id and thread_id:
            try:
                # Call the backend API to delete the agent and thread resources
                reset_url = f"http://localhost:8091/reset_agent_thread_id?agent_id={agent_id}&thread_id={thread_id}"
                logging.info(f"Calling reset endpoint: {reset_url}")
                
                reset_response = requests.post(reset_url)
                reset_response.raise_for_status()
                
                logging.info(f"Reset response: {reset_response.json()}")
                await cl.Message(content="Previous agent and thread resources have been deleted.", author="System").send()
            except requests.exceptions.RequestException as e:
                logging.error(f"Error resetting agent/thread: {str(e)}")
                # Continue anyway, as we'll set the IDs to None and create new ones
                await cl.Message(content=f"Note: Could not delete previous session resources: {str(e)}", author="System").send()
        
        # Clear the IDs to force creation of new ones on next message
        sessions[session_id]["agent_id"] = None
        sessions[session_id]["thread_id"] = None
        
        # Send a welcome message
        await cl.Message(content="Started a new conversation. Previous session has been reset.", author="System").send()

@cl.on_message
async def handle_message(message: cl.Message):
    """Handle incoming messages from Chainlit."""
    # Get the message content as a string
    user_message = message.content
    
    # Generate a unique session ID for the user if not already created
    session_id = cl.user_session.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        cl.user_session.set("session_id", session_id)  # Use set() method
        sessions[session_id] = {"agent_id": None, "thread_id": None}

    # Send the message to the backend server
    url = "http://localhost:8091/chat"  # Use localhost instead of 0.0.0.0
    payload = {
        "user_input": user_message,  # Use the extracted message content
        "agent_id": sessions[session_id].get("agent_id"),
        "thread_id": sessions[session_id].get("thread_id"),
    }

    # Create an empty message to show loading state initially
    msg = cl.Message(content="", author="Assistant")
    await msg.send()
    
    try:
        # Send request to backend
        logging.info(f"Sending request to backend with payload: {payload}")
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        # Update session data with agent and thread IDs
        sessions[session_id]["agent_id"] = data.get("agent_id")
        sessions[session_id]["thread_id"] = data.get("thread_id")
        
        # Debug log to verify stored IDs
        logging.info(f"Stored IDs: agent_id={data.get('agent_id')}, thread_id={data.get('thread_id')}")

        # Show the full response at once
        response_text = data.get("response", "No response received.")
        msg.content = response_text
        await msg.update()
            
    except requests.exceptions.RequestException as e:
        error_message = f"Error communicating with backend: {str(e)}"
        logging.error(error_message)
        
        # Check if the error is a connection issue
        if isinstance(e, requests.exceptions.ConnectionError):
            error_message = "Could not connect to the backend server. Please ensure the server is running."
        # Check if the error is an HTTP error
        elif isinstance(e, requests.exceptions.HTTPError) and hasattr(e, 'response'):
            status_code = e.response.status_code
            error_data = None
            try:
                error_data = e.response.json()
            except ValueError:
                pass
                
            if error_data and 'detail' in error_data:
                error_message = f"Backend error ({status_code}): {error_data['detail']}"
            else:
                error_message = f"Backend error ({status_code}): {e.response.text or str(e)}"
        
        # Show the full error at once
        msg.content = error_message
        await msg.update()

if __name__ == "__main__":
    print("*"*50)
    print("Starting Chainlit server")
    print("This server is responsible for handling requests to the Chainlit frontend.")
    print("*"*50)
    cl.run(host="0.0.0.0", port=8081)
