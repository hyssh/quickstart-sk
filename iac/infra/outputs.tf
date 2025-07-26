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

output "openai_endpoint" {
  description = "Azure OpenAI endpoint"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "openai_key" {
  description = "Azure OpenAI primary key"
  value       = azurerm_cognitive_account.openai.primary_access_key
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