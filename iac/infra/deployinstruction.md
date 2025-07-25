Deployment Instructions

1.Install Terraform (if not already installed):
winget install HashiCorp.Terraform

2.Initialize Terraform:
terraform init

3.Validate the configuration:
terraform validate

4.Plan the deployment:
terraform plan

5.Apply the configuration:
terraform apply -auto-approve

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

Azure AI Project (Machine Learning Workspace)

All resources will be properly named using the azurecaf provider and tagged for easy management.

# Example - Connect AI Services to ML Workspace (run after deployment)
az ml connection create --file connection-config.yml --workspace-name <workspace-name> --resource-group <rg-name>