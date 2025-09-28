#!/bin/bash
# testing/diagnose-function-structure.sh
set -euo pipefail

echo "🔍 Diagnosing Function App Structure and Configuration"

# Source environment
if [ -f .env.testing ]; then
    source .env.testing
else
    echo "❌ No .env.testing found"
    exit 1
fi

echo "📁 Checking local function structure..."

# Check if api-spec-gen-func directory exists
if [ ! -d "api-spec-gen-func" ]; then
    echo "❌ api-spec-gen-func directory not found"
    echo "   Create this directory with your Azure Function code"
    exit 1
fi

cd api-spec-gen-func

echo "✅ Found api-spec-gen-func directory"

# Check required files
echo "📋 Checking required files..."
FILES=("host.json" "requirements.txt")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file exists"
    else
        echo "  ❌ $file missing"
    fi
done

# Check for function directories
echo "📂 Checking function directories..."
FUNCTION_DIRS=()
for dir in */; do
    if [ -d "$dir" ] && [ -f "${dir}function.json" ]; then
        FUNCTION_DIRS+=("${dir%/}")
        echo "  ✅ Function: ${dir%/}"
    elif [ -d "$dir" ]; then
        echo "  ⚠️  Directory ${dir%/} exists but missing function.json"
    fi
done

if [ ${#FUNCTION_DIRS[@]} -eq 0 ]; then
    echo "❌ No valid function directories found!"
    echo "   Each function needs its own directory with function.json"
    echo ""
    echo "Expected structure:"
    echo "api-spec-gen-func/"
    echo "├── host.json"
    echo "├── requirements.txt"
    echo "├── GenerateOpenApi/"
    echo "│   ├── function.json"
    echo "│   └── __init__.py"
    echo "└── GenerateDocsFromOpenApi/"
    echo "    ├── function.json"
    echo "    └── __init__.py"
    exit 1
fi

# Check function.json content
echo "📝 Checking function.json files..."
for func_dir in "${FUNCTION_DIRS[@]}"; do
    echo "  📄 Checking $func_dir/function.json"
    if ! python3 -c "import json; json.load(open('$func_dir/function.json'))" 2>/dev/null; then
        echo "    ❌ Invalid JSON in $func_dir/function.json"
    else
        echo "    ✅ Valid JSON"
        # Show bindings
        BINDINGS=$(python3 -c "import json; f=json.load(open('$func_dir/function.json')); print(len(f.get('bindings', [])))")
        echo "    📎 Bindings count: $BINDINGS"
    fi
done

# Check host.json
echo "📝 Checking host.json..."
if python3 -c "import json; json.load(open('host.json'))" 2>/dev/null; then
    echo "  ✅ Valid JSON"
    VERSION=$(python3 -c "import json; f=json.load(open('host.json')); print(f.get('version', 'unknown'))")
    echo "  📊 Functions version: $VERSION"
else
    echo "  ❌ Invalid JSON in host.json"
fi

# Check requirements.txt
echo "📦 Checking requirements.txt..."
if [ -s requirements.txt ]; then
    echo "  ✅ requirements.txt has content"
    echo "  📋 Dependencies:"
    head -5 requirements.txt | sed 's/^/    /'
    LINES=$(wc -l < requirements.txt)
    if [ $LINES -gt 5 ]; then
        echo "    ... and $((LINES - 5)) more"
    fi
else
    echo "  ⚠️  requirements.txt is empty"
fi

# Check Python files
echo "🐍 Checking Python files..."
PYTHON_FILES=$(find . -name "*.py" | wc -l)
echo "  📊 Python files found: $PYTHON_FILES"

if [ $PYTHON_FILES -eq 0 ]; then
    echo "  ❌ No Python files found!"
fi

cd ..

# Check Azure resources if available
echo "☁️  Checking Azure resources..."
if az account show >/dev/null 2>&1; then
    echo "  ✅ Logged into Azure"
    
    # Check if Function App exists
    if az functionapp show -g "$RG" -n "$FUNCAPP" >/dev/null 2>&1; then
        echo "  ✅ Function App exists: $FUNCAPP"
        
        # Get Function App details
        STATE=$(az functionapp show -g "$RG" -n "$FUNCAPP" --query state -o tsv)
        RUNTIME=$(az functionapp show -g "$RG" -n "$FUNCAPP" --query "siteConfig.linuxFxVersion" -o tsv)
        
        echo "    📊 State: $STATE"
        echo "    🐍 Runtime: $RUNTIME"
        
        # Check deployed functions
        DEPLOYED_FUNCTIONS=$(az functionapp function list -g "$RG" -n "$FUNCAPP" --query "[].name" -o tsv 2>/dev/null || echo "")
        if [ -n "$DEPLOYED_FUNCTIONS" ]; then
            echo "    ✅ Deployed functions:"
            echo "$DEPLOYED_FUNCTIONS" | sed 's/^/      /'
        else
            echo "    ⚠️  No functions deployed yet"
        fi
        
    else
        echo "  ❌ Function App not found: $FUNCAPP"
    fi
else
    echo "  ⚠️  Not logged into Azure"
fi

echo ""
echo "🎯 Summary:"
echo "  Local structure: $([ ${#FUNCTION_DIRS[@]} -gt 0 ] && echo "✅ OK" || echo "❌ Issues found")"
echo "  Required files: $([ -f api-spec-gen-func/host.json ] && [ -f api-spec-gen-func/requirements.txt ] && echo "✅ OK" || echo "❌ Missing files")"
echo ""
echo "💡 If you're missing the function structure, create it like this:"
echo "   mkdir -p api-spec-gen-func/{GenerateOpenApi,GenerateDocsFromOpenApi}"
echo "   # Add function.json and __init__.py to each function directory"