# Semantic Kernel with FastAPI

## Requirements

- Azure AI Foundry


## Update .evn

```.evn
AZURE_AI_AGENT_PROJECT_CONNECTION_STRING="<example-connection-string>"
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME="<example-model-deployment-name>"
AZURE_AI_AGENT_ENDPOINT="<example-endpoint>"
AZURE_AI_AGENT_SUBSCRIPTION_ID="<example-subscription-id>"
AZURE_AI_AGENT_RESOURCE_GROUP_NAME="<example-resource-group-name>"
AZURE_AI_AGENT_PROJECT_NAME="<example-project-name>"
# Optional
AZURE_SEARCH_ENDPOINT="<example-search-endpoint>"
AZURE_SEARCH_API_KEY="<example-search-api-key>"
AZURE_SEARCH_INDEX="<example-search-index>"
ADX_CLUSTER_URL="<example-adx-cluster-url>"
ADX_DATABASE="<example-adx-database>"
```

## Start MCP Server

Example command
```bash
python -m sample-server.azureaisearch
```

## Post samples

1. Initial call 

```text
{
  "user_input":"List controls of PCI DSS"
}
```

Response will be like
```json
{
  "response": "The Payment Card Industry Data Security Standard (PCI DSS) version 4.0 is organized into 12 main requirements, often referred to as \"controls.\" Each requirement contains multiple sub-requirements and testing procedures. Here is a high-level list of the 12 core PCI DSS controls:\n\n1. Install and maintain network security controls.\n2. Apply secure configurations to all system components.\n3. Protect stored account data.\n4. Protect cardholder data with strong cryptography during transmission over open, public networks.\n5. Protect all systems and networks from malicious software.\n6. Develop and maintain secure systems and software.\n7. Restrict access to system components and cardholder data by business need to know.\n8. Identify users and authenticate access to system components.\n9. Restrict physical access to cardholder data.\n10. Log and monitor all access to system components and cardholder data.\n11. Test security of systems and networks regularly.\n12. Support information security with organizational policies and programs.\n\nEach of these requirements includes detailed controls and testing procedures to ensure the security of cardholder data and the cardholder data environment (CDE). If you need a breakdown of the sub-requirements or details for a specific control, let me know!",
  "thread_id": "thread_Jeg8fCvvNlfk9CTUQQohZvuY",
  "agent_id": "asst_LuzQe28Sa9yNh2J9zRpA6HN8"
}
```


2. And once you see thread_id and agent_id use them for the next call

```text
{
  "user_input":"Use Markdown format",
  "thread_id": "thread_Jeg8fCvvNlfk9CTUQQohZvuY",
  "agent_id": "asst_LuzQe28Sa9yNh2J9zRpA6HN8"
}
```
