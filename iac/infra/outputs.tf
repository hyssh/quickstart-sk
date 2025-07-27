output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "ai_services_endpoint" {
  description = "AI Services endpoint"
  value       = azurerm_cognitive_account.ai_services.endpoint
}

output "ai_services_key" {
  description = "AI Services primary key"
  value       = azurerm_cognitive_account.ai_services.primary_access_key
  sensitive   = true
}

output "search_endpoint" {
  description = "Azure Search endpoint"
  value       = "https://${azurerm_search_service.search.name}.search.windows.net"
}

output "search_api_key" {
  description = "Azure Search admin key"
  value       = azurerm_search_service.search.primary_key
  sensitive   = true
}

output "cosmos_endpoint" {
  description = "Cosmos DB endpoint"
  value       = azurerm_cosmosdb_account.cosmos.endpoint
}

output "cosmos_primary_key" {
  description = "Cosmos DB primary key"
  value       = azurerm_cosmosdb_account.cosmos.primary_key
  sensitive   = true
}

output "adx_cluster_uri" {
  description = "Azure Data Explorer cluster URI"
  value       = azurerm_kusto_cluster.adx.uri
}

# AI Foundry outputs
output "ai_foundry_name" {
  description = "AI Foundry resource name"
  value       = azapi_resource.ai_foundry.name
}

output "ai_foundry_id" {
  description = "AI Foundry resource ID"
  value       = azapi_resource.ai_foundry.id
}

output "ai_foundry_endpoint" {
  description = "AI Foundry endpoint"
  value       = "https://${azapi_resource.ai_foundry.name}.cognitiveservices.azure.com/"
}

output "ai_foundry_project_name" {
  description = "AI Foundry project name"
  value       = azapi_resource.ai_foundry_project.name
}

output "ai_foundry_project_id" {
  description = "AI Foundry project ID"
  value       = azapi_resource.ai_foundry_project.id
}

output "gpt_4o_deployment_name" {
  description = "GPT-4o deployment name"
  value       = azurerm_cognitive_deployment.aifoundry_deployment_gpt_4o.name
}