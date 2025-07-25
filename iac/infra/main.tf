terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
    azurecaf = {
      source  = "aztfmod/azurecaf"
      version = "~>1.2"
    }
  }
}

provider "azurerm" {
  features {}
}


# Generate a random string of 4 characters
resource "random_string" "random_suffix" {
  length  = 4
  special = false
  upper   = false
  numeric = false
}

# Define a local variable for the hashed timestamp (first 8 characters) and project name
locals {
  hashed_time_subset = substr(sha256(timestamp()), 0, 8)
  project_name       = "${var.project_name}${random_string.random_suffix.result}${local.hashed_time_subset}"
}

# Data source for current client configuration
data "azurerm_client_config" "current" {}

# Resource naming using azurecaf
resource "azurecaf_name" "resource_group" {
  name          = local.project_name
  resource_type = "azurerm_resource_group"
  suffixes      = [var.environment]
}

resource "azurecaf_name" "ai_services" {
  name          = local.project_name
  resource_type = "azurerm_cognitive_account"
  suffixes      = [var.environment]
}

resource "azurecaf_name" "search_service" {
  name          = local.project_name
  resource_type = "azurerm_search_service"
  suffixes      = [var.environment]
}

resource "azurecaf_name" "cosmos_db" {
  name          = local.project_name
  resource_type = "azurerm_cosmosdb_account"
  suffixes      = [var.environment]
}

resource "azurecaf_name" "kusto_cluster" {
  name          = local.project_name
  resource_type = "azurerm_kusto_cluster"
  suffixes      = [var.environment]
}

resource "azurecaf_name" "ai_project" {
  name          = local.project_name
  resource_type = "azurerm_machine_learning_workspace"
  suffixes      = ["aiproject", var.environment]
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = azurecaf_name.resource_group.result
  location = var.location

  tags = {
    Environment    = var.environment
    Project        = local.project_name
    "azd-env-name" = var.environment
  }
}

# AI Services (Cognitive Services) - Multi-service account
resource "azurerm_cognitive_account" "ai_services" {
  name                = azurecaf_name.ai_services.result
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "CognitiveServices"
  sku_name            = var.ai_services_sku

  tags = {
    Environment = var.environment
    Project     = local.project_name
  }
}

# Azure OpenAI Service (separate from multi-service for model deployments)
resource "azurerm_cognitive_account" "openai" {
  name                = "${local.project_name}-openai-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "OpenAI"
  sku_name            = var.openai_sku

  tags = {
    Environment = var.environment
    Project     = local.project_name
  }
}

# Azure AI Search Service
resource "azurerm_search_service" "search" {
  name                = azurecaf_name.search_service.result
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.search_sku
  replica_count       = 1
  partition_count     = 1

  tags = {
    Environment = var.environment
    Project     = local.project_name
  }
}

# Cosmos DB Account
resource "azurerm_cosmosdb_account" "cosmos" {
  name                = azurecaf_name.cosmos_db.result
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level       = "BoundedStaleness"
    max_interval_in_seconds = 300
    max_staleness_prefix    = 100000
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }

  capabilities {
    name = "EnableServerless"
  }

  tags = {
    Environment = var.environment
    Project     = local.project_name
  }
}

# Cosmos DB SQL Database
resource "azurerm_cosmosdb_sql_database" "database" {
  name                = var.cosmosdb_database
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.cosmos.name
}

# Cosmos DB SQL Container - Fixed partition key configuration
resource "azurerm_cosmosdb_sql_container" "container" {
  name                = var.cosmosdb_container
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.cosmos.name
  database_name       = azurerm_cosmosdb_sql_database.database.name
  
  # Updated to use partition_key_paths instead of deprecated partition_key_path
  partition_key_paths = ["/id"]

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }

    excluded_path {
      path = "/\"_etag\"/?"
    }
  }
}

# Data Explorer (Kusto) Cluster
resource "azurerm_kusto_cluster" "adx" {
  name                = azurecaf_name.kusto_cluster.result
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  sku {
    name     = var.kusto_sku_name
    capacity = var.kusto_sku_capacity
  }

  tags = {
    Environment = var.environment
    Project     = local.project_name
  }
}

# Data Explorer Database
resource "azurerm_kusto_database" "adx_database" {
  name                = var.adx_database
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  cluster_name        = azurerm_kusto_cluster.adx.name

  hot_cache_period   = "P7D"
  soft_delete_period = "P31D"
}

# Application Insights
resource "azurerm_application_insights" "ai_insights" {
  name                = "${local.project_name}-insights-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"

  tags = {
    Environment = var.environment
    Project     = local.project_name
  }
}

# Storage Account for AI Project
resource "azurerm_storage_account" "ai_storage" {
  name                     = lower(replace("${local.project_name}st${var.environment}", "-", ""))
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  allow_nested_items_to_be_public = false

  tags = {
    Environment = var.environment
    Project     = local.project_name
  }
}

# Key Vault
resource "azurerm_key_vault" "kv" {
  name                = "${local.project_name}kv${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Get", "List", "Create", "Delete", "Update"
    ]

    secret_permissions = [
      "Get", "List", "Set", "Delete"
    ]
  }

  tags = {
    Environment = var.environment
    Project     = local.project_name
  }
}

# Container Registry for AI Projects
resource "azurerm_container_registry" "acr" {
  name                = lower(replace("${local.project_name}acr${var.environment}", "-", ""))
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true

  tags = {
    Environment = var.environment
    Project     = local.project_name
  }
}

# Azure AI Foundry Project (Machine Learning Workspace)
resource "azurerm_machine_learning_workspace" "ai_project" {
  name                    = azurecaf_name.ai_project.result
  location                = azurerm_resource_group.main.location
  resource_group_name     = azurerm_resource_group.main.name
  application_insights_id = azurerm_application_insights.ai_insights.id
  key_vault_id            = azurerm_key_vault.kv.id
  storage_account_id      = azurerm_storage_account.ai_storage.id
  container_registry_id   = azurerm_container_registry.acr.id

  description = "Azure AI Foundry Project for ${local.project_name}"

  identity {
    type = "SystemAssigned"
  }

  tags = {
    Environment = var.environment
    Project     = local.project_name
    Type        = "AIProject"
  }
}