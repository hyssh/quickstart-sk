#!/usr/bin/env python

import os
import json
from typing import Any, Dict
from dataclasses import dataclass

import dotenv
import requests
from mcp.server.fastmcp import FastMCP

dotenv.load_dotenv()
mcp = FastMCP("Azure AI Search MCP")

@dataclass
class AzureSearchConfig:
    endpoint: str
    api_key: str
    index: str

search_config = AzureSearchConfig(
    endpoint=os.environ.get("AZURE_SEARCH_ENDPOINT", ""),
    api_key=os.environ.get("AZURE_SEARCH_API_KEY", ""),
    index=os.environ.get("AZURE_SEARCH_INDEX", ""),
)


@mcp.tool(description="Executes a search query against the Azure AI Search, it has PCI-DSS realted Controls and guides can be found.Payment Card Industry Data Security Standard  Requirements and Testing Procedures Version 4.0 March 2022 The Payment Card Industry Data Security Standard (PCI DSS) was developed to encourage and enhance payment card account data security and facilitate the broad adoption of consistent data security measures globally. PCI DSS provides a baseline of technical and operational requirements designed to protect account data. While specifically designed to focus on environments with payment card account data, PCI DSS can also be used to protect against threats and secure other elements in the payment ecosystem.")
async def search_documents(query: str) -> Dict[str, Any]:
    """
    Executes a search query against the configured AI Search index.
    
    Raises:
        ValueError: If required Azure Search environment variables are missing.
    
    Returns:
        Dict[str, Any]: The JSON response from the Azure Cognitive Search service.
    """
    if not search_config.endpoint or not search_config.api_key or not search_config.index:
        raise ValueError("Azure Search configuration is missing. Please set AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_API_KEY, and AZURE_SEARCH_INDEX environment variables.")
    
    search_url = f"{search_config.endpoint}/indexes/{search_config.index}/docs/search?api-version=2021-04-30-Preview"
    headers = {
        "Content-Type": "application/json",
        "api-key": search_config.api_key,
    }
    payload = {"search": query, "select":"content", "top": 5}
    response = requests.post(search_url, headers=headers, json=payload)
    response.raise_for_status()
    print(f"Search query: {query}")
    print(f"Response status code: {response.status_code}")
    return response.json()

@mcp.prompt()
async def search_prompt() -> str:
    return """
    This Azure AI Search service contains comprehensive PCI DSS v4.0 (Payment Card Industry Data Security Standard) documentation and compliance guides.
    
    You can search for information about:
    
    **Core PCI DSS Requirements:**
    - Network security requirements
    - Cardholder data protection
    - Vulnerability management programs
    - Access control measures
    - Network monitoring and testing
    - Information security policies
    
    **Example Queries:**
    - "What are the network security requirements for PCI DSS?"
    - "How to implement strong access control measures?"
    - "What are the cardholder data protection requirements?"
    - "PCI DSS vulnerability scanning requirements"
    - "Multi-factor authentication requirements"
    - "Network segmentation best practices"
    - "Encryption requirements for cardholder data"
    - "Security testing procedures"
    - "Incident response requirements"
    - "Compliance validation and reporting"
    
    **Specific Controls and Requirements:**
    - Requirements 1-12 detailed explanations
    - Testing procedures for each requirement
    - Guidance for implementation
    - Customized approaches and compensating controls
    
    **Use Cases:**
    - Compliance assessment preparation
    - Implementation guidance
    - Security control validation
    - Risk assessment support
    - Audit preparation
    
    Simply provide your search query about PCI DSS compliance, security controls, or implementation guidance.
    """

if __name__ == "__main__":
    print("Starting Azure AI Search MCP Server...")
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = 8088
    mcp.run("sse")