# mcp_doc_generator_server.py for the APIM Use Case 2
# **** NEED TO DO A SELF-REVIEW ****

import asyncio
import json
from mcp import Server, types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import aiohttp

app = Server("api-doc-generator")

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="generate_api_documentation",
            description="Generate comprehensive API documentation from OpenAPI specs",
            inputSchema={
                "type": "object",
                "properties": {
                    "api_spec_source": {
                        "type": "string",
                        "enum": ["auto-detect", "url", "repo-path"],
                        "description": "Where to find the API specification"
                    },
                    "spec_location": {
                        "type": "string",
                        "description": "URL or path to the API specification"
                    },
                    "output_name": {
                        "type": "string",
                        "description": "Base name for output files"
                    },
                    "include_security": {
                        "type": "boolean",
                        "default": True,
                        "description": "Include IT security guidelines"
                    }
                },
                "required": ["api_spec_source"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "generate_api_documentation":
        return await generate_documentation(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

async def generate_documentation(args: dict) -> list[types.TextContent]:
    """Trigger Azure DevOps pipeline and return status"""
    
    # Map MCP parameters to pipeline parameters
    pipeline_params = {
        "INPUT_SPEC_SOURCE": map_spec_source(args.get("api_spec_source")),
        "INPUT_SPEC_PATH": args.get("spec_location", ""),
        "OUTPUT_MD_NAME": f"{args.get('output_name', 'api-docs')}.md",
        "OUTPUT_HTML_NAME": f"{args.get('output_name', 'api-docs')}.html",
        "INCLUDE_SECURITY_GUIDELINES": args.get("include_security", True)
    }
    
    # Trigger Azure DevOps pipeline
    pipeline_url = "https://dev.azure.com/{org}/{project}/_apis/pipelines/{pipeline_id}/runs"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            pipeline_url,
            headers={
                "Authorization": f"Bearer {AZURE_DEVOPS_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "resources": {
                    "repositories": {
                        "self": {
                            "refName": "refs/heads/main"
                        }
                    }
                },
                "templateParameters": pipeline_params
            }
        ) as response:
            result = await response.json()
            
            if response.status == 200:
                run_id = result["id"]
                run_url = result["url"]
                
                return [
                    types.TextContent(
                        type="text",
                        text=f"""Documentation generation started successfully!

📄 Pipeline Run ID: {run_id}
🔗 Monitor progress: {run_url}
📥 Artifacts will be available after completion

The pipeline will generate:
- {pipeline_params['OUTPUT_MD_NAME']} (Markdown)
- {pipeline_params['OUTPUT_HTML_NAME']} (HTML)

Features included:
- Comprehensive abbreviations glossary
- Professional citations and references
- IT security guidelines: {'Yes' if pipeline_params['INCLUDE_SECURITY_GUIDELINES'] else 'No'}
- Multi-language code examples
"""
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error starting documentation generation: {result.get('message', 'Unknown error')}"
                    )
                ]

def map_spec_source(source: str) -> str:
    """Map MCP source types to pipeline parameter values"""
    mapping = {
        "auto-detect": "current-repo-auto",
        "url": "external-url", 
        "repo-path": "current-repo-custom"
    }
    return mapping.get(source, "current-repo-auto")

if __name__ == "__main__":
    import mcp.server.stdio
    mcp.server.stdio.run_server(app)