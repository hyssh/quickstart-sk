#!/usr/bin/env pwsh

<#
.SYNOPSIS
    Clean Terraform state and reinitialize

.DESCRIPTION
    This script cleans any existing Terraform state and cache, then reinitializes
#>

$ErrorActionPreference = "Stop"

Write-Host "🧹 Cleaning Terraform state and cache..." -ForegroundColor Yellow

# Remove Terraform state and cache files
if (Test-Path ".terraform") {
    Remove-Item -Recurse -Force ".terraform"
    Write-Host "✅ Removed .terraform directory" -ForegroundColor Green
}

if (Test-Path "terraform.tfstate") {
    Remove-Item -Force "terraform.tfstate"
    Write-Host "✅ Removed terraform.tfstate" -ForegroundColor Green
}

if (Test-Path "terraform.tfstate.backup") {
    Remove-Item -Force "terraform.tfstate.backup"
    Write-Host "✅ Removed terraform.tfstate.backup" -ForegroundColor Green
}

if (Test-Path ".terraform.lock.hcl") {
    Remove-Item -Force ".terraform.lock.hcl"
    Write-Host "✅ Removed .terraform.lock.hcl" -ForegroundColor Green
}

if (Test-Path "tfplan") {
    Remove-Item -Force "tfplan"
    Write-Host "✅ Removed tfplan" -ForegroundColor Green
}

Write-Host "✅ Terraform cleanup completed!" -ForegroundColor Green
Write-Host "💡 You can now run .\deploy-terraform.ps1 to deploy fresh" -ForegroundColor Cyan
