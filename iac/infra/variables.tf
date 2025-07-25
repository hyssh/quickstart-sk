variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "mhack1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US 2"
}

variable "ai_services_sku" {
  description = "SKU for AI Services"
  type        = string
  default     = "S0"
}

variable "openai_sku" {
  description = "SKU for Azure OpenAI"
  type        = string
  default     = "S0"
}

variable "search_sku" {
  description = "SKU for Azure Search"
  type        = string
  default     = "standard"
}

variable "kusto_sku_name" {
  description = "SKU name for Kusto cluster"
  type        = string
  default     = "Dev(No SLA)_Standard_D11_v2"
}

variable "kusto_sku_capacity" {
  description = "SKU capacity for Kusto cluster"
  type        = number
  default     = 1
}

variable "cosmosdb_database" {
  description = "Cosmos DB database name"
  type        = string
  default     = "cachcontainer"
}

variable "cosmosdb_container" {
  description = "Cosmos DB container name"
  type        = string
  default     = "qnapair"
}

variable "adx_database" {
  description = "Azure Data Explorer database name"
  type        = string
  default     = "adxdb"
}