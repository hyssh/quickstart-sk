Deployment Instructions

Open Azure Cloud Shell with Powershell from Azure Portal and execute the following scripts in sequence

# Clean any previous state
.\clean-terraform.ps1

# Deploy fresh
.\deploy-terraform.ps1

After successful deployment, you can view your resources in the Azure Portal at: https://portal.azure.com/#@/resource/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/

The Terraform script will create:

Resource Group

Azure AI Services (Cognitive Services)

Azure AI Search Service

Cosmos DB with database and container

Azure Data Explorer (Kusto) cluster and database

Application Insights

Storage Account

Key Vault

Azure AI services multi-service account

Azure AI Foundry

All resources will be properly named using the azurecaf provider and tagged for easy management.

# Example - Connect AI Services to ML Workspace (run after deployment)
az ml connection create --file connection-config.yml --workspace-name <workspace-name> --resource-group <rg-name>