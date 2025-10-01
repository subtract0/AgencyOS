#!/bin/bash
# Firestore Setup and Verification Script for Agency
# Enables production-grade persistent memory with Firestore and VectorStore

set -e  # Exit on error

# Determine the script directory and activate virtual environment if available
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Use virtual environment Python if available
if [ -f "$PROJECT_DIR/.venv/bin/python" ]; then
    PYTHON="$PROJECT_DIR/.venv/bin/python"
elif [ -f "$PROJECT_DIR/venv/bin/python" ]; then
    PYTHON="$PROJECT_DIR/venv/bin/python"
else
    PYTHON="python3"
fi

echo "🔥 Firestore Setup for Agency"
echo "=============================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ️  $1${NC}"; }

# Step 1: Check for GOOGLE_APPLICATION_CREDENTIALS
echo "Step 1: Checking Firebase credentials..."
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    print_error "GOOGLE_APPLICATION_CREDENTIALS not set"
    echo ""
    print_info "Steps to set up Firestore:"
    echo "  1. Go to Firebase Console: https://console.firebase.google.com/"
    echo "  2. Create project or use existing"
    echo "  3. Enable Firestore Database (select 'Start in production mode')"
    echo "  4. Go to Project Settings → Service Accounts"
    echo "  5. Generate new private key (JSON)"
    echo "  6. Save the file (e.g., firebase-credentials.json)"
    echo "  7. Set environment variable:"
    echo ""
    echo "     export GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-credentials.json"
    echo ""
    echo "  8. Add to .env file:"
    echo "     GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-credentials.json"
    echo "     FRESH_USE_FIRESTORE=true"
    echo "     USE_ENHANCED_MEMORY=true"
    echo ""
    exit 1
fi

print_success "GOOGLE_APPLICATION_CREDENTIALS is set: $GOOGLE_APPLICATION_CREDENTIALS"

# Step 2: Verify credentials file exists
echo ""
echo "Step 2: Verifying credentials file..."
if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    print_error "Credentials file not found: $GOOGLE_APPLICATION_CREDENTIALS"
    echo ""
    print_info "Please ensure the file exists and the path is correct"
    exit 1
fi

print_success "Credentials file exists: $GOOGLE_APPLICATION_CREDENTIALS"

# Step 3: Extract project ID from credentials
echo ""
echo "Step 3: Extracting project information..."
PROJECT_ID=$($PYTHON -c "import json; print(json.load(open('$GOOGLE_APPLICATION_CREDENTIALS'))['project_id'])" 2>/dev/null || echo "")

if [ -z "$PROJECT_ID" ]; then
    print_error "Could not extract project_id from credentials file"
    exit 1
fi

print_success "Firebase Project ID: $PROJECT_ID"

# Step 4: Check if dependencies are installed
echo ""
echo "Step 4: Checking dependencies..."

# Check google-cloud-firestore
if $PYTHON -c "from google.cloud import firestore" 2>/dev/null; then
    print_success "google-cloud-firestore is installed"
else
    print_error "google-cloud-firestore not installed"
    echo ""
    print_info "Install with: uv pip install google-cloud-firestore"
    exit 1
fi

# Check sentence-transformers
if $PYTHON -c "import sentence_transformers" 2>/dev/null; then
    print_success "sentence-transformers is installed"
else
    print_error "sentence-transformers not installed"
    echo ""
    print_info "Install with: uv pip install sentence-transformers"
    exit 1
fi

# Step 5: Test Firestore connection
echo ""
echo "Step 5: Testing Firestore connection..."

TEST_RESULT=$($PYTHON << 'EOF'
import sys
import os
from datetime import datetime

try:
    from agency_memory import create_firestore_store

    # Create Firestore store
    store = create_firestore_store(collection_name="agency_test_connection")

    # Test write
    test_key = f"connection_test_{datetime.now().isoformat()}"
    store.store(test_key, {"test": "data", "timestamp": datetime.now().isoformat()}, ["test", "connection"])

    # Test read
    result = store.search(["test"])

    if result.total_count > 0:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILED: No data retrieved")
        sys.exit(1)

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
EOF
)

if [ "$TEST_RESULT" = "SUCCESS" ]; then
    print_success "Firestore connection test passed"
else
    print_error "Firestore connection test failed: $TEST_RESULT"
    exit 1
fi

# Step 6: Verify VectorStore integration
echo ""
echo "Step 6: Testing VectorStore integration..."

VECTOR_TEST=$($PYTHON << 'EOF'
import sys

try:
    from agency_memory import create_enhanced_memory_store

    # Create enhanced memory store
    store = create_enhanced_memory_store(embedding_provider="sentence-transformers")

    # Test semantic search
    store.store("test_vector_1", {"content": "Machine learning is fascinating"}, ["test"])
    store.store("test_vector_2", {"content": "Python is a programming language"}, ["test"])

    # Semantic search
    results = store.semantic_search("artificial intelligence", top_k=1, min_similarity=0.0)

    if len(results) > 0:
        print("SUCCESS")
        sys.exit(0)
    else:
        print("FAILED: VectorStore search returned no results")
        sys.exit(1)

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
EOF
)

if [ "$VECTOR_TEST" = "SUCCESS" ]; then
    print_success "VectorStore integration test passed"
else
    print_error "VectorStore integration test failed: $VECTOR_TEST"
    exit 1
fi

# Step 7: Display environment configuration
echo ""
echo "Step 7: Environment configuration summary"
echo "=========================================="
echo ""
echo "Current .env settings should include:"
echo "  GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"
echo "  FRESH_USE_FIRESTORE=true"
echo "  USE_ENHANCED_MEMORY=true"
echo ""

# Check if .env file exists and has the right settings
if [ -f ".env" ]; then
    if grep -q "FRESH_USE_FIRESTORE=true" .env && grep -q "USE_ENHANCED_MEMORY=true" .env; then
        print_success ".env file is properly configured"
    else
        print_info ".env file exists but may need updating"
        echo ""
        echo "Ensure .env contains:"
        echo "  FRESH_USE_FIRESTORE=true"
        echo "  USE_ENHANCED_MEMORY=true"
    fi
else
    print_info ".env file not found. Create one from .env.example"
fi

# Final summary
echo ""
echo "=========================================="
print_success "Firestore setup complete!"
echo ""
echo "Your Agency instance is now configured with:"
echo "  • Firestore for persistent cross-session memory"
echo "  • VectorStore for semantic pattern matching"
echo "  • Production-grade learning infrastructure"
echo ""
echo "Next steps:"
echo "  1. Run: python agency.py run"
echo "  2. Test persistence by storing memories and restarting"
echo "  3. Monitor logs/telemetry/ for memory operations"
echo ""
echo "For troubleshooting, see docs/QUICKSTART.md"
echo "=========================================="
