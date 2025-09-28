def generate_enhanced_docs(spec_text):
    """Generate enhanced documentation with detailed schema information"""
    import yaml
    import json
    
    try:
        spec = yaml.safe_load(spec_text)
        client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21")
        )
        
        # Step 1: Generate main documentation
        main_docs = generate_main_documentation(client, spec_text)
        
        # Step 2: Generate detailed schema documentation
        schema_docs = ""
        if 'components' in spec and 'schemas' in spec['components']:
            schema_docs = generate_schema_documentation(client, spec['components']['schemas'])
        
        # Step 3: Generate field reference
        field_reference = generate_field_reference(client, spec)
        
        # Combine all documentation
        complete_docs = f"""
{main_docs}

## Detailed Schema Documentation

{schema_docs}

## Field Reference Guide

{field_reference}
"""
        return complete_docs
        
    except Exception as e:
        print(f"❌ Enhanced generation failed: {e}")
        return generate_docs_with_llm(spec_text)  # Fallback to standard

def generate_schema_documentation(client, schemas):
    """Generate detailed documentation for each schema"""
    
    schema_prompt = """For the following OpenAPI schemas, create DETAILED documentation:
    
    For EACH field:
    - Explain its business purpose
    - List ALL possible values (for enums)
    - Describe validation rules
    - Provide usage examples
    - Explain relationships to other fields
    
    Pay special attention to business-critical fields like:
    - bgwCategorization (explain all categories: White, Black, Grey, MC variants)
    - itSecurityClassification (explain all levels and when to use each)
    - confidentiality/integrity/availability ratings
    
    Schemas:
    {schemas_json}
    """
    
    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {"role": "system", "content": "You are an API documentation expert. Create detailed field-by-field documentation."},
            {"role": "user", "content": schema_prompt.format(schemas_json=json.dumps(schemas, indent=2))}
        ],
        temperature=0.2,
        max_tokens=6000  # Dedicated tokens for schema docs
    )
    
    return response.choices[0].message.content

def generate_field_reference(client, spec):
    """Generate a comprehensive field reference guide"""
    
    # Extract all unique fields and their properties
    fields_to_document = extract_important_fields(spec)
    
    reference_prompt = f"""Create a detailed field reference guide for these API fields:

{json.dumps(fields_to_document, indent=2)}

For each field, provide:
1. Field name and type
2. Business meaning and context
3. ALL possible values with explanations
4. Validation rules and constraints
5. Example values in different scenarios
6. Related fields and dependencies

Focus especially on enum fields and business-critical fields like:
- bgwCategorization: Explain White/Black/Grey categories, MC variants, security implications
- securityClassification: Detail each level and when it applies
- Any other security or compliance fields
"""
    
    response = client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
        messages=[
            {"role": "system", "content": "Create a comprehensive field reference guide."},
            {"role": "user", "content": reference_prompt}
        ],
        temperature=0.3,
        max_tokens=4000
    )
    
    return response.choices[0].message.content

def extract_important_fields(spec):
    """Extract important fields that need detailed documentation"""
    important_fields = {}
    
    if 'components' in spec and 'schemas' in spec['components']:
        for schema_name, schema_def in spec['components']['schemas'].items():
            if 'properties' in schema_def:
                for field_name, field_def in schema_def['properties'].items():
                    # Focus on enums and complex business fields
                    if 'enum' in field_def or field_name in [
                        'bgwCategorization', 'itSecurityClassification',
                        'confidentiality', 'integrity', 'availability'
                    ]:
                        important_fields[f"{schema_name}.{field_name}"] = field_def
    
    return important_fields
    