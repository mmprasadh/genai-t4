# ****** Prasadh: CURRENT VERSION ******
#!/usr/bin/env python3
# docs-gen/generate_docs_comprehensive.py
# Comprehensive API documentation generator with abbreviations and citations

import os
import sys
import yaml
import json
import argparse
from openai import AzureOpenAI
import markdown
from datetime import datetime

# Import our data files
from abbreviations import ABBREVIATIONS
from citations import CITATIONS

class ComprehensiveDocsGenerator:
    def __init__(self):
        """Initialize with comprehensive abbreviations and citations"""
        self.client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version=os.environ.get("AZU=E_OPENAI_API_VERSION", "2024-10-21")
        )
        self.deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
        self.abbreviations = ABBREVIATIONS
        self.citations = CITATIONS
        
    def strip_redundant_heading(self, section_text: str) -> str:
        """
        Remove the first line if it is a Markdown heading 
        Keeps the rest of the content intact.
        """
        lines = section_text.strip().splitlines()
        if lines and lines[0].strip().startswith("#"):
            return "\n".join(lines[1:]).strip()
        return section_text.strip()
    
    
    def generate_complete_documentation(self, spec_path, output_md, output_html):
        """Generate complete documentation with all sections"""
        print("📚 Starting comprehensive documentation generation...")
        
        with open(spec_path, 'r') as f:
            spec_text = f.read()
            spec = yaml.safe_load(spec_text)
        
        sections = []
        
        # Section 1: Title and Table of Contents
        print("  1️⃣ Generating title and overview...")
        title_section = self.generate_title_and_toc(spec)
        sections.append(title_section)
        
        # Section 2: Overview with abbreviations
        print("  2️⃣ Generating overview with abbreviations...")
        overview = self.generate_overview_section(spec_text, spec)
        sections.append(overview)
        
        # Section 3: Authentication & Security
        print("  3️⃣ Generating authentication and security...")
        auth = self.generate_auth_section(spec)
        sections.append(auth)
        
        # Section 4: Endpoints
        print("  4️⃣ Generating endpoints documentation...")
        endpoints = self.generate_endpoints_section(spec_text[:6000])
        sections.append(endpoints)
        
        # Section 5: Schemas with IT Security details
        print("  5️⃣ Generating schemas with IT security...")
        schemas = self.generate_schemas_section(spec)
        sections.append(schemas)
        
        # Section 6: IT Security Guidelines
        print("  6️⃣ Generating IT security guidelines...")
        security = self.generate_security_section(spec)
        sections.append(security)
        
        # Section 7: Error Handling
        print("  7️⃣ Generating error handling...")
        errors = self.generate_error_handling_section(spec)
        sections.append(errors)
        
        # Section 8: Abbreviations Glossary
        print("  8️⃣ Generating abbreviations glossary...")
        glossary = self.generate_abbreviations_glossary()
        sections.append(glossary)
        
        # Section 9: References and Citations
        print("  9️⃣ Generating references and citations...")
        references = self.generate_references_section()
        sections.append(references)
        
        # Section 10: Code Examples
        print("  🔟 Generating code examples...")
        examples = self.generate_code_examples_section(spec)
        sections.append(examples)
        
        # Combine all sections
        complete_docs = "\n\n---\n\n".join(sections)
        
        # Save outputs
        with open(output_md, 'w') as f:
            f.write(complete_docs)
        
        html_content = self.convert_to_html(complete_docs)
        with open(output_html, 'w') as f:
            f.write(html_content)
        
        print("✅ Documentation generation complete!")
        return complete_docs
    
    def generate_title_and_toc(self, spec):
        """Generate title page and table of contents"""
        info = spec.get('info', {})
        title = info.get('title', 'API Documentation')
        version = info.get('version', '1.0.0')
        
        return f"""# {title}

**Version**: {version}  
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Table of Contents

1. [Overview](#overview)
2. [Authentication & Security](#authentication--security)
3. [API Endpoints](#api-endpoints)
4. [Data Schemas](#data-schemas)
5. [IT Security Guidelines](#it-security-guidelines)
6. [Error Handling](#error-handling)
7. [Abbreviations Glossary](#abbreviations-glossary)
8. [References and Citations](#references-and-citations)
9. [Code Examples](#code-examples)"""
    
    def generate_overview_section(self, spec_text, spec):
        """Generate overview with abbreviations included"""
        abbrev_list = json.dumps(dict(list(self.abbreviations.items())[:30]), indent=2)
        citations_list = json.dumps(dict(list(self.citations.items())[:5]), indent=2)
        
        prompt = f"""Create a comprehensive API overview section.

Include these abbreviations in context:
{abbrev_list}

Reference these standards:
{citations_list}

OpenAPI Info:
{json.dumps(spec.get('info', {}), indent=2)}

Include:
1. Executive Summary
2. Purpose and Business Context
3. Target Audience
4. Key Features
5. Compliance Standards (reference citations)

Use abbreviations naturally in text, e.g., "The API uses REST (Representational State Transfer) architecture..."

Format as professional Markdown documentation."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are a technical writer creating API documentation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        return f"## Overview\n\n{response.choices[0].message.content}"
    
    def generate_auth_section(self, spec):
        """Generate authentication section with security citations"""
        security_schemes = spec.get('components', {}).get('securitySchemes', {})
        
        prompt = f"""Create a comprehensive Authentication & Security section.

Security Schemes:
{json.dumps(security_schemes, indent=2)}

Include references to:
- OAuth 2.0 (RFC 6749)
- OpenID Connect (OIDC)
- JWT (RFC 7519)
- OWASP API Security Top 10 2023
- Zero Trust Architecture (NIST SP 800-207)

Cover:
1. Authentication methods
2. Authorization flows
3. Security best practices
4. Token management
5. Rate limiting

Use proper citations, e.g., "Following OAuth 2.0 specifications [RFC 6749]..."

Format as detailed Markdown."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are a security expert documenting API authentication."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3500
        )
        
        clean_content = self.strip_redundant_heading(response.choices[0].message.content)
        return f"## Authentication & Security\n\n{clean_content}"


        
    
    def generate_schemas_section(self, spec):
        """Generate schemas with IT Security field details"""
        schemas = spec.get('components', {}).get('schemas', {})
        
        # Focus on IT Security schemas
        security_schemas = {k: v for k, v in schemas.items() 
                           if 'security' in k.lower() or 'bgw' in str(v).lower()}
        
        prompt = f"""Create COMPREHENSIVE schema documentation focusing on IT Security fields.

Schemas to document (truncated for space):
{json.dumps(security_schemas, indent=2)[:3000]}

CRITICAL: For EACH security field, explain:

1. bgwCategorization - ALL values:
   - WhiteMC: Management Console accessible from public networks (cite: CIS Controls v8, Control 12)
   - BlackMC: Management Console restricted to internal networks (cite: NIST 800-53r5, AC-4)
   - GreyMC: Management Console with conditional access (cite: Zero Trust Architecture)
   - White: Standard public classification
   - Black: Highly restricted internal
   - Grey: Conditional access required

2. confidentiality/integrity/availability (CIA Triad - ISO 27001:2022):
   - Level 1: Low - No specific requirements
   - Level 2: Medium - Standard requirements (SOC 2 Type II baseline)
   - Level 3: High - Enhanced requirements (PCI-DSS compliance)
   - Level 4: Critical - Maximum requirements (HIPAA/GDPR critical data)

3. itSecurityClassification levels (based on ISO 27001:2022 Annex A):
   - Public: No restrictions
   - Internal: Company use only
   - Confidential: Restricted access
   - Secret: Highly restricted
   - Top Secret: Maximum security

Include abbreviations: IC (Information Classification), RBAC (Role-Based Access Control), etc.

Format as detailed technical documentation."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are an IT security expert documenting schemas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3500
        )
        
        return f"## Data Schemas\n\n{response.choices[0].message.content}"
    
    def generate_security_section(self, spec):
        """Generate comprehensive IT Security guidelines"""
        prompt = f"""Create comprehensive IT Security Guidelines section.

Reference these standards with proper citations:
{json.dumps(dict(list(self.citations.items())[:10]), indent=2)}

Include these abbreviations in context:
{json.dumps(dict(list(self.abbreviations.items())[:20]), indent=2)}

Cover:
1. Security Classification Framework
   - BGW Categorization (all 6 values with use cases)
   - CIA Triad implementation (ISO 27001:2022)
   - Data classification levels

2. Compliance Requirements
   - GDPR (EU 2016/679) - Data protection
   - PCI-DSS v4.0 - Payment security
   - HIPAA - Health information
   - SOC 2 Type II - Service organization controls
   - ISO 27001:2022 - Information security management

3. Security Controls (NIST 800-53r5)
   - Access Control (AC)
   - Audit and Accountability (AU)
   - Security Assessment (CA)
   - Incident Response (IR)

4. Implementation Guidelines
   - Zero Trust Architecture (NIST SP 800-207)
   - Defense in Depth
   - Least Privilege (CIS Control 6)

Format with proper citations [Standard-ID] and spell out abbreviations on first use."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are an IT security architect creating security guidelines."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=3000
        )
        
        clean_content = self.strip_redundant_heading(response.choices[0].message.content)
        return f"## IT Security Guidelines\n\n{clean_content}"


    
    def generate_error_handling_section(self, spec):
        """Generate error handling with security considerations"""
        prompt = f"""Create comprehensive Error Handling section.

Include security considerations from:
- OWASP API Security Top 10 2023
- CWE (Common Weakness Enumeration)

Cover:
1. HTTP Status Codes
2. Error Response Schemas
3. Security Error Handling (avoid information disclosure)
4. Rate Limiting Errors (429)
5. Authentication/Authorization Errors (401/403)
6. Validation Errors (400/422)

Reference: OWASP API4:2023 - Unrestricted Resource Consumption

Format as technical documentation with examples."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "Create error handling documentation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
       
        response_text = response.choices[0].message.content
        lines = response_text.split("\n")
        if lines and lines[0].strip().startswith("#"):
            response_text = "\n".join(lines[1:])
       
        cleaned_response = self.strip_redundant_heading(response_text)
        return f"## Error Handling\n\n{cleaned_response}"



    
    def generate_endpoints_section(self, spec_text):
        """Generate endpoints documentation"""
        prompt = f"""Create detailed endpoint documentation.

OpenAPI Spec (truncated):
{spec_text}

For each endpoint include:
1. Method and Path
2. Purpose
3. Authentication required
4. Parameters
5. Request/Response examples
6. Error scenarios
7. Security considerations

Use abbreviations: API, REST, CRUD, HTTP, JSON
Reference: OpenAPI Specification v3.0.3

Format as technical API documentation."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "Create endpoint documentation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3500
        )
        
        return f"## API Endpoints\n\n{response.choices[0].message.content}"
    
    def generate_abbreviations_glossary(self):
        """Generate complete abbreviations glossary"""
        # Split abbreviations into categories
        security_abbrev = {k: v for k, v in self.abbreviations.items() 
                          if any(term in v.lower() for term in ['security', 'auth', 'encryption'])}
        compliance_abbrev = {k: v for k, v in self.abbreviations.items()
                            if any(term in k for term in ['ISO', 'NIST', 'OWASP', 'GDPR', 'PCI'])}
        technical_abbrev = {k: v for k, v in self.abbreviations.items()
                           if k not in security_abbrev and k not in compliance_abbrev}
        
        glossary = "## Abbreviations Glossary\n\n"
        
        glossary += "### Security & Authentication\n\n"
        glossary += "| Abbreviation | Full Form |\n|---|---|\n"
        for abbrev, full in sorted(security_abbrev.items()):
            glossary += f"| **{abbrev}** | {full} |\n"
        
        glossary += "\n### Compliance & Standards\n\n"
        glossary += "| Abbreviation | Full Form |\n|---|---|\n"
        for abbrev, full in sorted(compliance_abbrev.items()):
            glossary += f"| **{abbrev}** | {full} |\n"
        
        glossary += "\n### Technical Terms\n\n"
        glossary += "| Abbreviation | Full Form |\n|---|---|\n"
        for abbrev, full in sorted(list(technical_abbrev.items())[:30]):
            glossary += f"| **{abbrev}** | {full} |\n"
        
        return glossary
    
    def generate_references_section(self):
        """Generate complete references and citations"""
        references = "## References and Citations\n\n"
        
        # Group citations by category
        standards = {k: v for k, v in self.citations.items() 
                    if 'ISO' in k or 'NIST' in k or 'CIS' in k}
        regulations = {k: v for k, v in self.citations.items()
                      if any(reg in k for reg in ['GDPR', 'HIPAA', 'PCI', 'SOX', 'CCPA'])}
        frameworks = {k: v for k, v in self.citations.items()
                     if any(fw in k for fw in ['OWASP', 'COBIT', 'CSA'])}
        technical = {k: v for k, v in self.citations.items()
                    if any(tech in k for tech in ['RFC', 'OpenAPI', 'OAuth', 'JWT'])}
        
        references += "### International Standards\n\n"
        for ref_id, ref_data in standards.items():
            references += f"**[{ref_id}]** {ref_data['title']}. "
            references += f"{ref_data['publisher']}, {ref_data['year']}. "
            references += f"Available at: {ref_data['url']}\n\n"
        
        references += "### Regulatory Compliance\n\n"
        for ref_id, ref_data in regulations.items():
            references += f"**[{ref_id}]** {ref_data['title']}. "
            references += f"{ref_data['publisher']}, {ref_data['year']}. "
            references += f"Available at: {ref_data['url']}\n\n"
        
        references += "### Security Frameworks\n\n"
        for ref_id, ref_data in frameworks.items():
            references += f"**[{ref_id}]** {ref_data['title']}. "
            references += f"{ref_data['publisher']}, {ref_data['year']}. "
            references += f"Available at: {ref_data['url']}\n\n"
        
        references += "### Technical Specifications\n\n"
        for ref_id, ref_data in technical.items():
            references += f"**[{ref_id}]** {ref_data['title']}. "
            references += f"{ref_data['publisher']}, {ref_data['year']}. "
            references += f"Available at: {ref_data['url']}\n\n"
        
        return references
    
    def generate_code_examples_section(self, spec):
        """Generate code examples"""
        servers = spec.get('servers', [{'url': 'https://api.example.com'}])
        base_url = servers[0]['url'] if servers else 'https://api.example.com'
        
        return f"""## Code Examples

### Authentication Example
```python
# Python example using requests
import requests

# API Key Authentication
headers = {{
    'X-API-Key': 'your-api-key',
    'Content-Type': 'application/json'
}}

response = requests.get(
    '{base_url}/endpoint',
    headers=headers
)

if response.status_code == 200:
    data = response.json()
    print(f"Success: {{data}}")
else:
    print(f"Error: {{response.status_code}} - {{response.text}}")
```

### cURL Example
```bash
curl -X GET "{base_url}/endpoint" \\
     -H "X-API-Key: your-api-key" \\
     -H "Content-Type: application/json"
```

### JavaScript Example
```javascript
const apiKey = 'your-api-key';
const baseUrl = '{base_url}';

const response = await fetch(`${{baseUrl}}/endpoint`, {{
    method: 'GET',
    headers: {{
        'X-API-Key': apiKey,
        'Content-Type': 'application/json'
    }}
}});

if (response.ok) {{
    const data = await response.json();
    console.log('Success:', data);
}} else {{
    console.error('Error:', response.status, await response.text());
}}
```

### PHP Example
```php
<?php
$apiKey = 'your-api-key';
$baseUrl = '{base_url}';

$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $baseUrl . '/endpoint');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'X-API-Key: ' . $apiKey,
    'Content-Type: application/json'
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode === 200) {{
    $data = json_decode($response, true);
    echo "Success: " . print_r($data, true);
}} else {{
    echo "Error: $httpCode - $response";
}}
?>
```"""
    
    def convert_to_html(self, markdown_content):
        """Convert markdown to HTML"""
        html_content = markdown.markdown(markdown_content, extensions=['tables', 'toc'])
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px; 
            line-height: 1.6;
            color: #333;
        }}
        h1, h2, h3 {{ 
            color: #2c3e50; 
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }}
        h1 {{ color: #1e3a8a; }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            margin: 15px 0; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th, td {{ 
            border: 1px solid #ddd; 
            padding: 12px; 
            text-align: left; 
        }}
        th {{ 
            background-color: #f8f9fa; 
            font-weight: 600;
            color: #2c3e50;
        }}
        tr:nth-child(even) {{ background-color: #f8f9fa; }}
        pre {{ 
            background-color: #f4f4f4; 
            padding: 15px; 
            border-radius: 8px; 
            overflow-x: auto; 
            border-left: 4px solid #007bff;
        }}
        code {{ 
            background-color: #f4f4f4; 
            padding: 3px 6px; 
            border-radius: 4px; 
            font-family: 'Courier New', Consolas, monospace;
        }}
        .toc {{ 
            background-color: #f8f9fa; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
            border-left: 4px solid #28a745;
        }}
        blockquote {{
            border-left: 4px solid #ffc107;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #fff9e6;
        }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""

def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive API documentation')
    parser.add_argument('spec_path', help='Path to OpenAPI specification file')
    parser.add_argument('--output-md', default='docs/comprehensive-docs.md', help='Output markdown file')
    parser.add_argument('--output-html', default='docs/comprehensive-docs.html', help='Output HTML file')
    
    args = parser.parse_args()
    
    generator = ComprehensiveDocsGenerator()
    generator.generate_complete_documentation(args.spec_path, args.output_md, args.output_html)

if __name__ == "__main__":
    main()  
