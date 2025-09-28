#!/usr/bin/env bash
set -euo pipefail

# Set your environment variables (adjust these to match your deployment)
RG="rg-uk-sbx-wipro"                   # Replace with actual name
KV="genai-test-kv-56209"               # Replace with actual name
AOAI_NAME="your-openai-resource-name"  # Replace with actual name
ST="your-storage-account-name"         # Replace with actual name
FUNCAPP="your-function-app-name"       # Replace with actual name
APIM="your-apim-name"                  # Replace with actual name

echo "🧹 Starting cleanup of GenAI resources..."

# Function to safely delete resource
delete_resource() {
    local service="$1"
    local resource_name="$2"
    local command="$3"
    
    echo "Checking $service: $resource_name"
    if eval "$command" >/dev/null 2>&1; then
        echo "❌ Deleting $service: $resource_name"
        eval "${command/show/delete} --yes" >/dev/null 2>&1 || echo "⚠️  Failed to delete $resource_name"
    else
        echo "✅ $service not found: $resource_name"
    fi
}

# Delete API Management (takes longest, so start first)
echo "🔄 Deleting API Management (this can take 30+ minutes)..."
delete_resource "APIM" "$APIM" "az apim show -g $RG -n $APIM"

# Delete Function App
delete_resource "Function App" "$FUNCAPP" "az functionapp show -g $RG -n $FUNCAPP"

# Delete Azure OpenAI (might be in soft-delete state)
echo "🔄 Deleting Azure OpenAI resource..."
if az cognitiveservices account show -g "$RG" -n "$AOAI_NAME" >/dev/null 2>&1; then
    echo "❌ Deleting OpenAI resource: $AOAI_NAME"
    az cognitiveservices account delete -g "$RG" -n "$AOAI_NAME" --yes >/dev/null 2>&1 || echo "⚠️  Failed to delete OpenAI resource"
    
    # Also purge to avoid conflicts in future deployments
    echo "🗑️  Purging OpenAI resource from soft-delete..."
    sleep 10  # Wait a bit before purging
    az cognitiveservices account purge --location "westeurope" --name "$AOAI_NAME" >/dev/null 2>&1 || echo "⚠️  Failed to purge OpenAI resource"
else
    echo "✅ OpenAI resource not found: $AOAI_NAME"
fi

# Delete Storage Account
delete_resource "Storage Account" "$ST" "az storage account show -g $RG -n $ST"

# Delete Key Vault (will go into soft-delete state)
echo "🔄 Deleting Key Vault..."
if az keyvault show -g "$RG" -n "$KV" >/dev/null 2>&1; then
    echo "❌ Deleting Key Vault: $KV"
    az keyvault delete -g "$RG" -n "$KV" >/dev/null 2>&1 || echo "⚠️  Failed to delete Key Vault"
    
    # Also purge to avoid conflicts in future deployments
    echo "🗑️  Purging Key Vault from soft-delete..."
    sleep 10  # Wait a bit before purging
    az keyvault purge -n "$KV" >/dev/null 2>&1 || echo "⚠️  Failed to purge Key Vault (may require admin permissions)"
else
    echo "✅ Key Vault not found: $KV"
fi

echo ""
echo "🎉 Cleanup completed!"
echo ""
echo "📝 Notes:"
echo "   • API Management deletion can take 30-45 minutes"
echo "   • Key Vault and OpenAI resources may remain in soft-delete state"
echo "   • You may need admin permissions to purge Key Vault"
echo ""
echo "🔍 To verify cleanup, run:"
echo "   az resource list -g $RG --query '[].{Name:name,Type:type,Status:provisioningState}' -o table"