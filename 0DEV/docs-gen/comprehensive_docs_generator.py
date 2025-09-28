# generate_docs_enhanced.py
import os
import yaml
import json
from openai import AzureOpenAI
import markdown

class comprehensive_docs_generator:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21")
        )
        self.deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]
        
        # IT Security abbreviations and citations
        self.it_security_context = {
            "abbreviations": {
                "BGW": "Border Gateway",
                "MC": "Management Console",
                "IC": "Information Classification",
                "GDPR": "General Data Protection Regulation",
                "SOC": "Security Operations Center",
                "SIEM": "Security Information and Event Management",
                "CIA": "Confidentiality, Integrity, Availability",
                "PII": "Personally Identifiable Information",
                "RBAC": "Role-Based Access Control",
                "MFA": "Multi-Factor Authentication",
                "SSO": "Single Sign-On",
                "ISMS": "Information Security Management System",
                "ISO": "International Organization for Standardization",
                "NIST": "National Institute of Standards and Technology",
                "OWASP": "Open Web Application Security Project"
            },
            "citations": {
                "ISO27001": "ISO/IEC 27001:2022 - Information security management systems",
                "NIST-CSF": "NIST Cybersecurity Framework Version 2.0 (2024)",
                "GDPR": "Regulation (EU) 2016/679 - General Data Protection Regulation",
                "SOC2": "SOC 2® - Service Organization Control 2 (AICPA)",
                "OWASP-Top10": "OWASP Top 10 API Security Risks – 2023",
                "CIS": "CIS Critical Security Controls v8.0",
                "COBIT": "COBIT 2019 Framework: Governance and Management Objectives"
            }
        }
    
    def generate_complete_documentation(self, spec_path, output_md, output_html):
        """Generate complete documentation with all sections"""
        with open(spec_path, 'r') as f:
            spec_text = f.read()
            spec = yaml.safe_load(spec_text)
        
        print("📚 Generating comprehensive API documentation...")
        
        # Generate each section separately to manage token limits
        sections = []
        
        # Section 1: Overview and Authentication
        print("  1️⃣ Generating overview and authentication...")
        overview = self.generate_overview_section(spec_text)
        sections.append(overview)
        
        # Section 2: Detailed Endpoints Documentation
        print("  2️⃣ Generating endpoints documentation...")
        endpoints = self.generate_endpoints_section(spec_text)
        sections.append(endpoints)
        
        # Section 3: Comprehensive Schema Documentation
        print("  3️⃣ Generating schema documentation...")
        schemas = self.generate_schemas_section(spec)
        sections.append(schemas)
        
        # Section 4: IT Security Documentation
        print("  4️⃣ Generating IT security documentation...")
        security = self.generate_security_section(spec)
        sections.append(security)
        
        # Section 5: Abbreviations Glossary
        print("  5️⃣ Generating abbreviations glossary...")
        abbreviations = self.generate_abbreviations_section(spec)
        sections.append(abbreviations)
        
        # Section 6: References and Citations
        print("  6️⃣ Generating references and citations...")
        references = self.generate_references_section(spec)
        sections.append(references)
        
        # Section 7: Code Examples
        print("  7️⃣ Generating code examples...")
        examples = self.generate_examples_section(spec)
        sections.append(examples)
        
        # Combine all sections
        complete_docs = "\n\n---\n\n".join(sections)
        
        # Add table of contents
        toc = self.generate_table_of_contents(complete_docs)
        final_docs = f"{toc}\n\n---\n\n{complete_docs}"
        
        # Save markdown
        with open(output_md, 'w') as f:
            f.write(final_docs)
        
        # Convert to HTML with styling
        html_content = self.convert_to_html(final_docs)
        with open(output_html, 'w') as f:
            f.write(html_content)
        
        print("✅ Documentation generation complete!")
        return final_docs
    
    def generate_overview_section(self, spec_text):
        """Generate overview and authentication section"""
        prompt = f"""Create a comprehensive API overview section with:

1. Executive Summary
2. API Purpose and Business Context
3. Target Audience
4. Key Features and Capabilities
5. Authentication and Authorization
6. Rate Limiting and Quotas
7. Versioning Strategy
8. Support and Contact Information

Include relevant abbreviations in parentheses on first use.

OpenAPI Spec:
{spec_text[:3000]}  # First part of spec for context

Format in Markdown with clear sections."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are a technical writer creating professional API documentation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return f"# API Documentation\n\n{response.choices[0].message.content}"
    
    def generate_schemas_section(self, spec):
        """Generate detailed schema documentation with IT security focus"""
        schemas = spec.get('components', {}).get('schemas', {})
        
        prompt = f"""Create COMPREHENSIVE schema documentation for these API schemas:

{json.dumps(schemas, indent=2)[:4000]}

For EACH schema and field:

1. **Field Details:**
   - Field name, type, and constraints
   - Business purpose and context
   - Required/optional status
   - Default values

2. **For Enum Fields (CRITICAL - LIST ALL VALUES):**
   - ALL possible values with detailed explanations
   - When to use each value
   - Business implications

3. **For IT Security Fields (bgwCategorization, securityClassification, etc.):**
   - Detailed explanation of each security level
   - Compliance requirements (cite: {', '.join(self.it_security_context['citations'].keys())})
   - Implementation guidelines
   
   For bgwCategorization specifically:
   - WhiteMC: Management Console accessible from public networks (low security)
   - BlackMC: Management Console restricted to internal networks only (high security)
   - GreyMC: Management Console with conditional access (medium security)
   - White: Standard public-facing classification
   - Black: Highly restricted, internal only
   - Grey: Restricted with specific access controls
   
   For confidentiality/integrity/availability:
   - Level 1: Low - No specific security requirements
   - Level 2: Medium - Standard security requirements
   - Level 3: High - Enhanced security requirements
   - Level 4: Critical - Maximum security requirements

4. **Abbreviations:** Use these IT security abbreviations:
{json.dumps(self.it_security_context['abbreviations'], indent=2)}

5. **Citations:** Reference these standards where relevant:
{json.dumps(self.it_security_context['citations'], indent=2)}

Format as detailed Markdown with examples."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are an expert in API documentation and IT security standards."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return f"## Data Schemas\n\n{response.choices[0].message.content}"
    
    def generate_security_section(self, spec):
        """Generate comprehensive IT Security documentation"""
        prompt = f"""Create a comprehensive IT Security section for this API documentation:

## IT Security Documentation

### 1. Security Classification Framework
Explain the security classification system used in this API:
- BGW (Border Gateway) Categorization levels and their meanings
- IT Security Classification levels
- CIA (Confidentiality, Integrity, Availability) triad ratings

### 2. Compliance and Standards
Reference these standards with proper citations:
{json.dumps(self.it_security_context['citations'], indent=2)}

### 3. Security Implementation Guidelines
For each security field in the API:
- bgwCategorization: Explain ALL values (WhiteMC, BlackMC, GreyMC, White, Black, Grey)
- itSecurityClassification: Detail each classification level
- confidentiality/integrity/availability: Explain rating scale (1-4)
- icRelevancy: Information Classification relevancy
- securityConceptDocument: Requirements and format

### 4. Security Best Practices
- Authentication requirements
- Data encryption standards
- Audit logging requirements
- Access control implementation

### 5. Abbreviations Used
{json.dumps(self.it_security_context['abbreviations'], indent=2)}

### 6. Regulatory Compliance
- GDPR requirements and implementation
- SOC 2 compliance considerations
- ISO 27001 alignment

Include practical examples and implementation notes.
Format as professional security documentation."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "You are an IT security expert creating security documentation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=3000
        )
        
        return f"## IT Security Guidelines\n\n{response.choices[0].message.content}"
    
    def generate_abbreviations_section(self, spec):
        """Generate comprehensive abbreviations glossary"""
        all_abbreviations = {
            **self.it_security_context['abbreviations'],
            "API": "Application Programming Interface",
            "REST": "Representational State Transfer",
            "JSON": "JavaScript Object Notation",
            "HTTP": "Hypertext Transfer Protocol",
            "HTTPS": "Hypertext Transfer Protocol Secure",
            "URL": "Uniform Resource Locator",
            "URI": "Uniform Resource Identifier",
            "UUID": "Universally Unique Identifier",
            "CRUD": "Create, Read, Update, Delete",
            "TLS": "Transport Layer Security",
            "JWT": "JSON Web Token",
            "OAuth": "Open Authorization",
            "SAML": "Security Assertion Markup Language",
            "LDAP": "Lightweight Directory Access Protocol",
            "DNS": "Domain Name System",
            "CDN": "Content Delivery Network",
            "DDoS": "Distributed Denial of Service",
            "WAF": "Web Application Firewall",
            "XSS": "Cross-Site Scripting",
            "CSRF": "Cross-Site Request Forgery",
            "SQL": "Structured Query Language"
        }
        
        prompt = f"""Create a comprehensive abbreviations glossary for API documentation:

Include these abbreviations and any others found in the API specification:
{json.dumps(all_abbreviations, indent=2)}

Format as a professional glossary with:
1. Alphabetical ordering
2. Clear definitions
3. Context of use in this API
4. Related terms where applicable

Format in Markdown as a table or definition list."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "Create a professional abbreviations glossary."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=2000
        )
        
        return f"## Abbreviations and Acronyms\n\n{response.choices[0].message.content}"
    
    def generate_references_section(self, spec):
        """Generate references and citations section"""
        prompt = f"""Create a comprehensive References and Citations section:

## References and Citations

### Standards and Frameworks
{json.dumps(self.it_security_context['citations'], indent=2)}

### Additional References
1. OpenAPI Specification 3.0.3
2. RFC 7231 - HTTP/1.1 Semantics and Content
3. RFC 6749 - OAuth 2.0 Authorization Framework
4. RFC 7519 - JSON Web Token (JWT)

### Recommended Reading
- API Security Best Practices
- RESTful API Design Guidelines
- Security Headers Documentation

### External Resources
- Link to official documentation
- Developer portal references
- Support resources

Format as a professional bibliography with:
- Proper citations (Author, Year, Title, Publisher)
- Hyperlinks where available
- Brief descriptions of relevance
- Categorization by type (Standards, Guidelines, Tools, etc.)"""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "Create professional references and citations section."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=1500
        )
        
        return f"## References and Citations\n\n{response.choices[0].message.content}"
    
    def generate_endpoints_section(self, spec_text):
        """Generate detailed endpoints documentation"""
        prompt = f"""Create detailed endpoint documentation from this OpenAPI spec:

{spec_text[:4000]}

For each endpoint include:
1. HTTP method and path
2. Purpose and business logic
3. Authentication requirements
4. Request parameters (query, path, headers, body)
5. Response codes and schemas
6. Error scenarios
7. Example requests and responses
8. Rate limiting information
9. Related endpoints

Use proper technical abbreviations and cite security standards where relevant."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "Create comprehensive endpoint documentation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return f"## API Endpoints\n\n{response.choices[0].message.content}"
    
    def generate_examples_section(self, spec):
        """Generate code examples section"""
        prompt = """Create comprehensive code examples section:

## Code Examples

### Authentication Examples
- API Key authentication
- OAuth 2.0 flow
- JWT token usage

### Common Operations
- CRUD operations
- Pagination
- Filtering and sorting
- Error handling

### Language-Specific Examples
1. Python (using requests)
2. JavaScript (fetch/axios)
3. cURL commands
4. Postman collections

### Integration Patterns
- Retry logic
- Rate limiting handling
- Webhook implementation
- Batch processing

Include working code with comments and best practices."""

        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": "Create practical code examples for API usage."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        return f"## Code Examples\n\n{response.choices[0].message.content}"
    
    def generate_table_of_contents(self, content):
        """Generate table of contents from markdown content"""
        lines = content.split('\n')
        toc = ["# Table of Contents\n"]
        
        for line in lines:
            if line.startswith('##'):
                level = line.count('#')
                title = line.replace('#', '').strip()
                indent = '  ' * (level - 2)
                anchor = title.lower().replace(' ', '-').replace('/', '-')
                toc.append(f"{indent}- [{title}](#{anchor})")
        
        return '\n'.join(toc)
    
    def convert_to_html(self, markdown_content):
        """Convert markdown to styled HTML"""
        html_body = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'toc', 'attr_list']
        )
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 40px 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3, h4 {{
            color: #2c3e50;
            margin-top: 30px;
        }}
        h1 {{ border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; }}
        code {{
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Consolas', monospace;
        }}
        pre {{
            background: #282c34;
            color: #abb2bf;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
        }}
        pre code {{
            background: none;
            color: inherit;
            padding: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding-left: 20px;
            color: #555;
            background: #ecf0f1;
            padding: 15px 20px;
        }}
        .security-note {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .abbreviation {{
            color: #3498db;
            cursor: help;
            border-bottom: 1px dotted #3498db;
        }}
        .citation {{
            color: #7f8c8d;
            font-size: 0.9em;
            vertical-align: super;
        }}
        .toc {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .toc ul {{
            list-style-type: none;
            padding-left: 20px;
        }}
        .toc a {{
            color: #3498db;
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_body}
    </div>
</body>
</html>"""
        
        return html