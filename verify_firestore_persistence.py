#!/usr/bin/env python3
"""
Firestore Persistence Verification Script
Audits actual Firestore connection and document counts.
"""

import os
import sys
from datetime import datetime


def verify_firestore_configuration():
    """Step 1: Verify Firestore configuration."""
    print("=" * 80)
    print("FIRESTORE CONFIGURATION AUDIT")
    print("=" * 80)

    results = {"config_valid": True, "issues": []}

    # Check environment variables
    fresh_use_firestore = os.getenv("FRESH_USE_FIRESTORE", "").lower()
    use_enhanced_memory = os.getenv("USE_ENHANCED_MEMORY", "").lower()
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")

    print("\n1. Environment Variables:")
    print(f"   FRESH_USE_FIRESTORE: {fresh_use_firestore}")
    print(f"   USE_ENHANCED_MEMORY: {use_enhanced_memory}")
    print(f"   GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}")
    print(f"   GOOGLE_CLOUD_PROJECT: {project_id}")

    # Validate configuration
    if fresh_use_firestore != "true":
        results["config_valid"] = False
        results["issues"].append("FRESH_USE_FIRESTORE is not set to 'true'")
        print("   ⚠️  WARNING: FRESH_USE_FIRESTORE is not 'true'")
    else:
        print("   ✓ FRESH_USE_FIRESTORE correctly set")

    if not credentials_path:
        results["config_valid"] = False
        results["issues"].append("GOOGLE_APPLICATION_CREDENTIALS not set")
        print("   ✗ GOOGLE_APPLICATION_CREDENTIALS not set")
    elif not os.path.exists(credentials_path):
        results["config_valid"] = False
        results["issues"].append(f"Credentials file not found: {credentials_path}")
        print(f"   ✗ Credentials file not found: {credentials_path}")
    else:
        print(f"   ✓ Credentials file exists: {credentials_path}")

    if not project_id:
        results["config_valid"] = False
        results["issues"].append("GOOGLE_CLOUD_PROJECT not set")
        print("   ✗ GOOGLE_CLOUD_PROJECT not set")
    else:
        print(f"   ✓ Project ID set: {project_id}")

    return results


def test_firestore_connection():
    """Step 2: Test actual Firestore connection."""
    print("\n" + "=" * 80)
    print("FIRESTORE CONNECTION TEST")
    print("=" * 80)

    results = {"connected": False, "client_type": None, "error": None}

    try:
        from google.cloud import firestore

        print("\n✓ google-cloud-firestore package imported successfully")

        # Attempt to create client
        print("\nAttempting to connect to Firestore...")
        client = firestore.Client()
        results["client_type"] = "firestore.Client"

        # Test connection with a simple query
        test_collection = client.collection("agency_memories")
        list(test_collection.limit(1).stream())

        results["connected"] = True
        print("✓ Successfully connected to Firestore")
        print(f"✓ Client type: {type(client)}")

        return results, client

    except ImportError as e:
        results["error"] = f"Import error: {e}"
        print(f"✗ Failed to import google-cloud-firestore: {e}")
        return results, None

    except Exception as e:
        results["error"] = f"Connection error: {e}"
        print(f"✗ Failed to connect to Firestore: {e}")
        return results, None


def audit_firestore_data(client):
    """Step 3: Audit actual Firestore data."""
    print("\n" + "=" * 80)
    print("FIRESTORE DATA AUDIT")
    print("=" * 80)

    results = {
        "collection_exists": False,
        "document_count": 0,
        "sample_documents": [],
        "error": None,
    }

    if not client:
        results["error"] = "No Firestore client available"
        print("\n✗ Cannot audit data - no client available")
        return results

    try:
        collection_name = "agency_memories"
        collection = client.collection(collection_name)

        print(f"\n1. Querying collection: {collection_name}")

        # Count all documents
        docs = list(collection.stream())
        results["document_count"] = len(docs)
        results["collection_exists"] = True

        print("   ✓ Collection exists")
        print(f"   ✓ Found {len(docs)} documents")

        # Get sample documents
        if docs:
            print("\n2. Sample Documents (showing up to 3):")
            for i, doc in enumerate(docs[:3]):
                doc_data = doc.to_dict()
                results["sample_documents"].append({"id": doc.id, "data": doc_data})

                print(f"\n   Document {i + 1} (ID: {doc.id}):")
                print(f"      Key: {doc_data.get('key', 'N/A')}")
                print(f"      Tags: {doc_data.get('tags', [])}")
                print(f"      Timestamp: {doc_data.get('timestamp', 'N/A')}")
                print(f"      Content preview: {str(doc_data.get('content', ''))[:100]}...")
        else:
            print("\n   ℹ️  No documents found in collection")

        return results

    except Exception as e:
        results["error"] = f"Audit error: {e}"
        print(f"\n✗ Failed to audit Firestore data: {e}")
        return results


def check_firestore_store_implementation():
    """Step 4: Verify FirestoreStore will use real Firestore (not fallback)."""
    print("\n" + "=" * 80)
    print("FIRESTORESTORE IMPLEMENTATION CHECK")
    print("=" * 80)

    results = {"will_use_firestore": False, "fallback_conditions": [], "error": None}

    try:
        from agency_memory.firestore_store import FirestoreStore

        print("\n1. Initializing FirestoreStore...")
        store = FirestoreStore("agency_memories")

        # Check if fallback store is used
        if store._fallback_store is not None:
            results["will_use_firestore"] = False
            results["fallback_conditions"].append("InMemoryStore fallback is active")
            print("   ✗ FirestoreStore is using InMemoryStore fallback")
            print(f"   ✗ Fallback store type: {type(store._fallback_store)}")
        else:
            results["will_use_firestore"] = True
            print("   ✓ FirestoreStore is using REAL Firestore")
            print(f"   ✓ Client: {store._client}")
            print(f"   ✓ Collection: {store._collection}")

        return results

    except Exception as e:
        results["error"] = f"Implementation check error: {e}"
        print(f"\n✗ Failed to check FirestoreStore implementation: {e}")
        return results


def generate_audit_report(config_results, connection_results, data_results, implementation_results):
    """Generate comprehensive audit report."""
    print("\n" + "=" * 80)
    print("FIRESTORE PERSISTENCE AUDIT REPORT")
    print("=" * 80)
    print(f"Generated: {datetime.now().isoformat()}")
    print("=" * 80)

    # Overall status
    all_checks_passed = (
        config_results["config_valid"]
        and connection_results["connected"]
        and implementation_results["will_use_firestore"]
    )

    print(f"\nOVERALL STATUS: {'✓ PASS' if all_checks_passed else '✗ FAIL'}")

    # Configuration
    print("\n1. CONFIGURATION:")
    if config_results["config_valid"]:
        print("   ✓ All required environment variables set correctly")
    else:
        print("   ✗ Configuration issues found:")
        for issue in config_results["issues"]:
            print(f"      - {issue}")

    # Connection
    print("\n2. CONNECTION:")
    if connection_results["connected"]:
        print("   ✓ Successfully connected to Firestore")
        print(f"   ✓ Client type: {connection_results['client_type']}")
    else:
        print("   ✗ Failed to connect to Firestore")
        if connection_results["error"]:
            print(f"      Error: {connection_results['error']}")

    # Data
    print("\n3. DATA PERSISTENCE:")
    if data_results.get("collection_exists"):
        print("   ✓ Collection 'agency_memories' exists")
        print(f"   ✓ Document count: {data_results['document_count']}")
        if data_results["document_count"] > 0:
            print(
                f"   ✓ REAL DATA CONFIRMED - {data_results['document_count']} documents in Firestore"
            )
        else:
            print("   ℹ️  Collection is empty (no documents yet)")
    else:
        print("   ✗ Unable to verify data persistence")
        if data_results.get("error"):
            print(f"      Error: {data_results['error']}")

    # Implementation
    print("\n4. IMPLEMENTATION:")
    if implementation_results["will_use_firestore"]:
        print("   ✓ FirestoreStore will use REAL Firestore (not InMemoryStore fallback)")
    else:
        print("   ✗ FirestoreStore is using InMemoryStore fallback")
        for condition in implementation_results["fallback_conditions"]:
            print(f"      - {condition}")
        if implementation_results.get("error"):
            print(f"      Error: {implementation_results['error']}")

    # Summary
    print("\n" + "=" * 80)
    print("VERDICT:")
    print("=" * 80)
    if all_checks_passed:
        print("✓ FIRESTORE PERSISTENCE IS WORKING")
        print("✓ All checks passed - real Firestore is being used")
        if data_results.get("document_count", 0) > 0:
            print(f"✓ Verified {data_results['document_count']} documents in production Firestore")
    else:
        print("✗ FIRESTORE PERSISTENCE VERIFICATION FAILED")
        print("✗ Issues detected - see details above")
    print("=" * 80)

    return all_checks_passed


def main():
    """Run complete Firestore persistence audit."""
    print("\nStarting Firestore Persistence Audit...\n")

    # Step 1: Configuration
    config_results = verify_firestore_configuration()

    # Step 2: Connection
    connection_results, client = test_firestore_connection()

    # Step 3: Data audit
    data_results = audit_firestore_data(client) if client else {"error": "No client"}

    # Step 4: Implementation check
    implementation_results = check_firestore_store_implementation()

    # Step 5: Generate report
    success = generate_audit_report(
        config_results, connection_results, data_results, implementation_results
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
