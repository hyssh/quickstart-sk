#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Deploy Terraform configuration with AI Foundry resources

.DESCRIPTION
    This script initializes and deploys the Terraform configuration that includes AI Foundry resources

.PARAMETER Environment
    The environment name (default: "dev")

.PARAMETER AutoApprove
    Skip interactive approval of plan

.EXAMPLE
    .\deploy-terraform.ps1
    .\deploy-terraform.ps1 -Environment "prod" -AutoApprove
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory = $false)]
    [switch]$AutoApprove
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Deploying Terraform configuration with AI Foundry..." -ForegroundColor Green

# Check if we're in the correct directory
if (-not (Test-Path "main.tf")) {
    Write-Host "❌ main.tf not found. Please run this script from the infra directory." -ForegroundColor Red
    exit 1
}

# Check Azure CLI login
try {
    $account = az account show --output json | ConvertFrom-Json
    Write-Host "✅ Logged in as: $($account.user.name)" -ForegroundColor Green
    Write-Host "✅ Using subscription: $($account.name)" -ForegroundColor Green
} catch {
    Write-Host "❌ Please run 'az login' first" -ForegroundColor Red
    exit 1
}

# Initialize Terraform
Write-Host "🔧 Initializing Terraform..." -ForegroundColor Yellow
terraform init
if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Terraform init failed"
    exit 1
}

# Validate configuration
Write-Host "🔍 Validating Terraform configuration..." -ForegroundColor Yellow
terraform validate
if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Terraform validation failed"
    exit 1
}

# Plan deployment
Write-Host "📋 Planning Terraform deployment..." -ForegroundColor Yellow
terraform plan -var-file="terraform.tfvars" -out=tfplan

if ($LASTEXITCODE -ne 0) {
    Write-Error "❌ Terraform plan failed"
    exit 1
}

# Apply deployment
if ($AutoApprove) {
    Write-Host "🎯 Applying Terraform configuration (auto-approved)..." -ForegroundColor Yellow
    terraform apply tfplan
} else {
    Write-Host "🎯 Applying Terraform configuration..." -ForegroundColor Yellow
    Write-Host "💡 Plan has been saved to 'tfplan'. Applying the exact planned changes..." -ForegroundColor Cyan
    terraform apply tfplan
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Terraform deployment completed successfully!" -ForegroundColor Green
    
    # Show outputs
    Write-Host "`n📋 Deployment Outputs:" -ForegroundColor Cyan
    terraform output
    
} else {
    Write-Error "❌ Terraform apply failed"
    exit 1
}

Write-Host "`n🎉 AI Foundry infrastructure deployed successfully!" -ForegroundColor Green
Write-Host "🌐 You can view your resources in the Azure portal" -ForegroundColor Yellow
