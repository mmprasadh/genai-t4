#!/bin/bash
# testing/create-function-structure.sh
set -euo pipefail

echo "🏗️ Creating Azure Function structure"

# Create main directory
mkdir -p api-spec-gen-func

cd api-spec-gen-func

# Create host.json
cat > host.json <<EOF
{
    "version": "2.0",
    "extensionBundle": {
        "id": "Microsoft.Azure.Functions.ExtensionBundle",
        "version": "[4.*, 5.0.0)"
    },
    "functionTimeout": "00:10:00",
    "logging": {
        "logLevel": {
            "default": "Information"
        }
    }
}
EOF

# Create requirements.txt
cat > requirements.txt <<EOF
azure-functions
azure-identity
azure-keyvault-secrets
openai>=1.0.0
pydantic
requests
EOF

# Create GenerateOpenApi function
mkdir -p GenerateOpenApi

cat > GenerateOpenApi/function.json <<EOF
{
    "scriptFile": "__init__.py",
    "bindings": [
        {
            "authLevel": "function",
            "type": "httpTrigger",
            "direction": "in",
            "name": "req",
            "methods": ["get", "post"]
        },
        {
            "type": "http",
            "direction": "out",
            "name": "$return"
        }
    ]
}
EOF

cat > GenerateOpenApi/__init__.py <<'EOF'
import azure.functions as func
import json
import logging
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import openai

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('GenerateOpenApi function processed a request.')
    
    try:
        # Get request data
        try:
            req_body = req.get_json()
            prompt = req_body.get('prompt', '') if req_body else ''
        except ValueError:
            prompt = req.params.get('prompt', '')
            
        if not prompt:
            return func.HttpResponse(
                json.dumps({"error": "Please provide a prompt parameter"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Get Azure OpenAI credentials from Key Vault
        kv_name = os.environ.get('KV_NAME')
        if not kv_name:
            return func.HttpResponse(
                json.dumps({"error": "Key Vault not configured"}),
                status_code=500,
                mimetype="application/json"
            )
        
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=f"https://{kv_name}.vault.azure.net/", credential=credential)
        
        endpoint = client.get_secret("AZURE-OPENAI-ENDPOINT").value
        api_key = client.get_secret("AZURE-OPENAI-API-KEY").value
        deployment = client.get_secret("AZURE-OPENAI-DEPLOYMENT").value
        
        # Initialize OpenAI client
        client_openai = openai.AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-15-preview"
        )
        
        # Generate OpenAPI spec
        system_prompt = """You are an expert API designer. Generate a complete OpenAPI 3.0 specification based on the user's description. 
        Return only valid JSON for the OpenAPI specification without any markdown formatting."""
        
        response = client_openai.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Create an OpenAPI specification for: {prompt}"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Parse and return the generated spec
        generated_content = response.choices[0].message.content
        
        # Try to parse as JSON to validate
        try:
            openapi_spec = json.loads(generated_content)
            return func.HttpResponse(
                json.dumps(openapi_spec, indent=2),
                status_code=200,
                mimetype="application/json"
            )
        except json.JSONDecodeError:
            return func.HttpResponse(
                json.dumps({"error": "Generated content is not valid JSON", "content": generated_content}),
                status_code=500,
                mimetype="application/json"
            )
            
    except Exception as e:
        logging.error(f"Error in GenerateOpenApi: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
EOF

# Create GenerateDocsFromOpenApi function
mkdir -p GenerateDocsFromOpenApi

cat > GenerateDocsFromOpenApi/function.json <<EOF
{
    "scriptFile": "__init__.py",
    "bindings": [
        {
            "authLevel": "function",
            "type": "httpTrigger",
            "direction": "in",
            "name": "req",
            "methods": ["get", "post"]
        },
        {
            "type": "http",
            "direction": "out",
            "name": "$return"
        }
    ]
}
EOF

cat > GenerateDocsFromOpenApi/__init__.py <<'EOF'
import azure.functions as func
import json
import logging
import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import openai

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('GenerateDocsFromOpenApi function processed a request.')
    
    try:
        # Get request data
        try:
            req_body = req.get_json()
            openapi_spec = req_body.get('openapi_spec', {}) if req_body else {}
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Please provide openapi_spec in request body"}),
                status_code=400,
                mimetype="application/json"
            )
            
        if not openapi_spec:
            return func.HttpResponse(
                json.dumps({"error": "Please provide openapi_spec parameter"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Get Azure OpenAI credentials from Key Vault
        kv_name = os.environ.get('KV_NAME')
        if not kv_name:
            return func.HttpResponse(
                json.dumps({"error": "Key Vault not configured"}),
                status_code=500,
                mimetype="application/json"
            )
        
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=f"https://{kv_name}.vault.azure.net/", credential=credential)
        
        endpoint = client.get_secret("AZURE-OPENAI-ENDPOINT").value
        api_key = client.get_secret("AZURE-OPENAI-API-KEY").value
        deployment = client.get_secret("AZURE-OPENAI-DEPLOYMENT").value
        
        # Initialize OpenAI client
        client_openai = openai.AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-02-15-preview"
        )
        
        # Generate documentation
        system_prompt = """You are a technical documentation expert. Generate comprehensive API documentation 
        in Markdown format based on the provided OpenAPI specification. Include:
        1. Overview and description
        2. Authentication details
        3. Endpoint descriptions with examples
        4. Request/response schemas
        5. Error codes and handling
        Make it developer-friendly and easy to understand."""
        
        spec_text = json.dumps(openapi_spec, indent=2)
        
        response = client_openai.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate documentation for this OpenAPI spec:\n{spec_text}"}
            ],
            temperature=0.3,
            max_tokens=3000
        )
        
        documentation = response.choices[0].message.content
        
        return func.HttpResponse(
            json.dumps({"documentation": documentation}),
            status_code=200,
            mimetype="application/json"
        )
            
    except Exception as e:
        logging.error(f"Error in GenerateDocsFromOpenApi: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": f"Internal server error: {str(e)}"}),
            status_code=500,
            mimetype="application/json"
        )
EOF

cd ..

echo "✅ Azure Function structure created successfully!"
echo ""
echo "📁 Created structure:"
echo "api-spec-gen-func/"
echo "├── host.json"
echo "├── requirements.txt"
echo "├── GenerateOpenApi/"
echo "│   ├── function.json"
echo "│   └── __init__.py"
echo "└── GenerateDocsFromOpenApi/"
echo "    ├── function.json"
echo "    └── __init__.py"
echo ""
echo "🎯 Next steps:"
echo "   1. Review and customize the function code as needed"
echo "   2. Run the fixed deployment script: ./testing/quick-deploy-functions.sh"