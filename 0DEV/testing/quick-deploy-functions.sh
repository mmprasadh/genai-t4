#!/bin/bash
# testing/quick-deploy-functions.sh
set -euo pipefail

echo "🚀 Quick Deploy Functions for Testing"

# Source environment if it exists
if [ -f .env.testing ]; then
    source .env.testing
    echo "✅ Loaded testing environment"
else
    echo "❌ No testing environment found. Run ./testing/setup-testing-environment.sh first"
    exit 1
fi

# Verify prerequisites
echo "🔍 Checking prerequisites..."
command -v az >/dev/null 2>&1 || { echo "❌ Azure CLI required"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.9+ required"; exit 1; }

# Ensure logged in to Azure
if ! az account show >/dev/null 2>&1; then
    echo "🔐 Azure login required"
    az login --use-device-code
    az account set --subscription "$SUB"
fi

# Create resource group
echo "🏗️ Ensuring resource group exists: $RG"
az group create -n "$RG" -l "$LOC" >/dev/null 2>&1 || true

# Create Key Vault
echo "🔐 Using existing Key Vault: $KV"
export KV="kv-weu-SBX-001"
export RG_KV="rg-functionapp-001"

# Create Azure OpenAI
echo "🤖 Creating Azure OpenAI: $AOAI_NAME"
az cognitiveservices account create -g "$RG" -n "$AOAI_NAME" -l "$LOC" \
  --kind OpenAI --sku S0 >/dev/null 2>&1 || true

# Wait for Azure OpenAI to be ready
echo "⏳ Waiting for Azure OpenAI to be ready..."
sleep 30

# Create Storage Account
echo "💾 Creating Storage Account: $ST"
az storage account create -g "$RG" -n "$ST" -l "$LOC" --sku Standard_LRS >/dev/null 2>&1 || true

# Wait for storage account to be ready
echo "⏳ Waiting for Storage Account to be ready..."
sleep 15

# Create Function App with explicit Python version
echo "⚡ Creating Function App: $FUNCAPP"
az functionapp create -g "$RG" -n "$FUNCAPP" --storage-account "$ST" \
  --consumption-plan-location "$LOC" --os-type Linux --runtime python \
  --runtime-version 3.11 --functions-version 4 >/dev/null 2>&1 || true

# Wait for Function App to be fully provisioned
echo "⏳ Waiting for Function App to be fully ready..."
sleep 60

# Deploy GPT-4o model - Change the model, if required **Guru
echo "🚀 Deploying GPT-4o model..."
az cognitiveservices account deployment create \
  -g "$RG" -n "$AOAI_NAME" --deployment-name "gpt4o-test" \
  --model-format OpenAI --model-name "gpt-4o" --model-version "2024-08-06" \
  --sku-name "Standard" --sku-capacity 10 >/dev/null 2>&1 || true

# Configure Key Vault secrets
echo "🔑 Setting up Key Vault secrets..."
AOAI_ENDPOINT="https://$AOAI_NAME.openai.azure.com/"
AOAI_KEY=$(az cognitiveservices account keys list -g "$RG" -n "$AOAI_NAME" --query key1 -o tsv)

az keyvault secret set --vault-name "$KV" --name AZURE-OPENAI-ENDPOINT \
  --value "$AOAI_ENDPOINT" >/dev/null
az keyvault secret set --vault-name "$KV" --name AZURE-OPENAI-DEPLOYMENT \
  --value "gpt4o-test" >/dev/null
az keyvault secret set --vault-name "$KV" --name AZURE-OPENAI-API-KEY \
  --value "$AOAI_KEY" >/dev/null

# Configure Function App identity and permissions
echo "🔐 Configuring Function App permissions..."
az functionapp identity assign -g "$RG" -n "$FUNCAPP" >/dev/null
sleep 10  # Wait for identity to be created

FUNC_PRINCIPAL_ID=$(az functionapp identity show -g "$RG" -n "$FUNCAPP" --query principalId -o tsv)
KV_ID=$(az keyvault show -g "$RG_KV" -n "$KV" --query id -o tsv)

az role assignment create --role "Key Vault Secrets User" \
  --assignee-object-id "$FUNC_PRINCIPAL_ID" --assignee-principal-type ServicePrincipal \
  --scope "$KV_ID" >/dev/null

# Configure Function App settings
echo "⚙️ Configuring Function App settings..."
CONN=$(az storage account show-connection-string -g "$RG" -n "$ST" --query connectionString -o tsv)
az functionapp config appsettings set -g "$RG" -n "$FUNCAPP" --settings \
  "AzureWebJobsStorage=$CONN" \
  "KV_NAME=$KV" \
  "FUNCTIONS_WORKER_RUNTIME=python" \
  "WEBSITE_RUN_FROM_PACKAGE=1" >/dev/null

# Verify function app is ready before deployment
echo "🔍 Verifying Function App status..."
FUNC_STATE=$(az functionapp show -g "$RG" -n "$FUNCAPP" --query state -o tsv)
if [ "$FUNC_STATE" != "Running" ]; then
    echo "⏳ Function App not running yet, waiting..."
    sleep 30
fi

# Verify the api-spec-gen-func directory exists and has required files
if [ ! -d "api-spec-gen-func" ]; then
    echo "❌ api-spec-gen-func directory not found. Please ensure it exists in the current directory."
    exit 1
fi

echo "📂 Checking function structure..."
if [ ! -f "api-spec-gen-func/requirements.txt" ]; then
    echo "❌ requirements.txt not found in api-spec-gen-func/"
    exit 1
fi

if [ ! -f "api-spec-gen-func/host.json" ]; then
    echo "❌ host.json not found in api-spec-gen-func/"
    exit 1
fi

# Deploy function code
echo "📦 Deploying function code..."
ZIP="/tmp/func-test-deploy.zip"
rm -f "$ZIP"

# Create archive with proper exclusions and verbose output for debugging
echo "📁 Creating deployment package..."
(
  cd api-spec-gen-func
  
  # List contents for debugging
  echo "Contents of api-spec-gen-func directory:"
  find . -type f | head -20
  
  # Create zip with explicit exclusions
  zip -r "$ZIP" . \
    -x "*/.venv/*" "*/__pycache__/*" "*.pyc" "local.settings.json" \
    -x "*/.git/*" "*/.pytest_cache/*" "*/test_*" "*/.env*"
)

# Verify ZIP was created and has content
if [ ! -f "$ZIP" ]; then
    echo "❌ Failed to create deployment package"
    exit 1
fi

echo "📊 Deployment package size: $(du -h "$ZIP" | cut -f1)"
echo "📋 Contents of deployment package:"
unzip -l "$ZIP" | head -20

# Deploy to Azure Function App with better error handling
echo "🚀 Deploying to Azure Function App..."
if ! az functionapp deployment source config-zip \
  -g "$RG" -n "$FUNCAPP" --src "$ZIP"; then
    echo "❌ Deployment failed. Checking Function App logs..."
    
    # Get deployment logs for debugging
    echo "📝 Recent deployment logs:"
    az functionapp log deployment show -g "$RG" -n "$FUNCAPP" || true
    
    # Check Function App status
    echo "📊 Function App status:"
    az functionapp show -g "$RG" -n "$FUNCAPP" --query "{name:name,state:state,hostNames:defaultHostName}" -o table
    
    exit 1
fi

echo "⏳ Waiting for deployment to complete..."
sleep 60

# Verify deployment was successful
echo "✅ Verifying deployment..."
DEPLOY_STATUS=$(az functionapp show -g "$RG" -n "$FUNCAPP" --query state -o tsv)
if [ "$DEPLOY_STATUS" != "Running" ]; then
    echo "⚠️ Function App state: $DEPLOY_STATUS"
fi

# Get function URLs and codes with better error handling
echo "🔗 Retrieving function endpoints..."

# Check if functions exist before getting URLs
FUNCTIONS=$(az functionapp function list -g "$RG" -n "$FUNCAPP" --query "[].name" -o tsv)
echo "📋 Available functions: $FUNCTIONS"

if echo "$FUNCTIONS" | grep -q "GenerateOpenApi"; then
    GEN_URL=$(az functionapp function show -g "$RG" -n "$FUNCAPP" \
      --function-name GenerateOpenApi --query "invoke_url_template" -o tsv 2>/dev/null || echo "")
    GEN_CODE=$(az functionapp function keys list -g "$RG" -n "$FUNCAPP" \
      --function-name GenerateOpenApi --query "default" -o tsv 2>/dev/null || echo "")
else
    echo "⚠️ GenerateOpenApi function not found"
    GEN_URL=""
    GEN_CODE=""
fi

if echo "$FUNCTIONS" | grep -q "GenerateDocsFromOpenApi"; then
    DOCS_URL=$(az functionapp function show -g "$RG" -n "$FUNCAPP" \
      --function-name GenerateDocsFromOpenApi --query "invoke_url_template" -o tsv 2>/dev/null || echo "")
    DOCS_CODE=$(az functionapp function keys list -g "$RG" -n "$FUNCAPP" \
      --function-name GenerateDocsFromOpenApi --query "default" -o tsv 2>/dev/null || echo "")
else
    echo "⚠️ GenerateDocsFromOpenApi function not found"
    DOCS_URL=""
    DOCS_CODE=""
fi

# Save endpoints
mkdir -p testing
cat > testing/.endpoints <<EOF
export GEN_FUNC_URL="$GEN_URL"
export GEN_FUNC_CODE="$GEN_CODE"
export DOCS_FUNC_URL="$DOCS_URL"
export DOCS_FUNC_CODE="$DOCS_CODE"
EOF

echo "✅ Quick deployment complete!"
echo "📋 Function endpoints saved to testing/.endpoints"
echo ""
echo "🔗 Function URLs:"
if [ -n "$GEN_URL" ]; then
    echo "   GenerateOpenApi: $GEN_URL"
fi
if [ -n "$DOCS_URL" ]; then
    echo "   GenerateDocsFromOpenApi: $DOCS_URL"
fi
echo ""
echo "Next steps:"
echo "   1. Install 42Crunch CLI: npm install -g @42crunch/api-security-audit"
echo "   2. Test functions: ./testing/test-functions.sh"
echo "   3. Run Use Case 1: ./scripts/use-case-1-complete.sh"

# Clean up temporary files
rm -f "$ZIP"