# Firestore Setup Guide - Production-Grade Persistent Memory

Enable production-grade persistent memory for Agency with Firestore and VectorStore integration.

---

## Overview

Agency's memory system supports three configurations:

1. **In-Memory Only** (Development): Fast, no persistence between sessions
2. **In-Memory + VectorStore** (Enhanced Development): Semantic search, no persistence
3. **Firestore + VectorStore** (Production): Full persistence + semantic search ✅

This guide covers setting up configuration #3 for production use.

---

## Prerequisites

- Google Cloud Project with Firestore enabled
- Service account credentials (JSON file)
- Python dependencies installed

---

## Quick Setup (5 Minutes)

### 1. Create Firebase/Firestore Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or use existing
3. Enable **Firestore Database**
   - Select "Start in production mode"
   - Choose a location (e.g., `us-central`)

### 2. Generate Service Account Credentials

1. Go to **Project Settings → Service Accounts**
2. Click **Generate new private key**
3. Save the JSON file (e.g., `firebase-credentials.json`)
4. **Important**: Keep this file secure, never commit to git

### 3. Install Dependencies

```bash
# Install required packages
uv pip install google-cloud-firestore sentence-transformers

# Or using pip (if in virtual environment)
pip install google-cloud-firestore sentence-transformers
```

### 4. Configure Environment Variables

Add to your `.env` file:

```bash
# Firebase Configuration
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-credentials.json
GOOGLE_CLOUD_PROJECT=your-project-id  # Optional, extracted from credentials

# Enable Production Memory
FRESH_USE_FIRESTORE=true
USE_ENHANCED_MEMORY=true
```

### 5. Verify Setup

Run the automated setup script:

```bash
./scripts/setup_firestore.sh
```

**Expected output:**
```
🔥 Firestore Setup for Agency
==============================

✅ GOOGLE_APPLICATION_CREDENTIALS is set
✅ Credentials file exists
✅ Firebase Project ID: your-project-id
✅ google-cloud-firestore is installed
✅ sentence-transformers is installed
✅ Firestore connection test passed
✅ VectorStore integration test passed
🎉 Firestore setup complete!
```

---

## Testing Persistence

### Test Cross-Session Memory Persistence

```bash
# Step 1: Store test memories
python test_memory_persistence.py

# Expected output:
# ✅ Successfully stored 3 memories
# Test Session ID: 20251001_024055

# Step 2: Retrieve in "new session" (use the session ID from Step 1)
python test_memory_persistence.py retrieve 20251001_024055

# Expected output:
# ✅ Retrieved 3 memories from session 20251001_024055
# 🎉 Cross-session persistence verified!
```

---

## Architecture

### Memory System Components

```
┌─────────────────────────────────────────────┐
│           Agency Memory System              │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │  Firestore   │◄─────┤  Memory API     │ │
│  │  (Persist)   │      │  (store/search) │ │
│  └──────────────┘      └─────────────────┘ │
│                                             │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │ VectorStore  │◄─────┤ Semantic Search │ │
│  │ (Embeddings) │      │ (similarity)    │ │
│  └──────────────┘      └─────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

### Configuration Flow

```python
# agency.py initialization (lines 126-164)
if use_enhanced_memory and use_firestore:
    # Production: Firestore for persistence
    firestore_store = create_firestore_store()
    shared_memory = Memory(store=firestore_store)

    # VectorStore for semantic search (in-memory for performance)
    enhanced_store = create_enhanced_memory_store(
        embedding_provider="sentence-transformers"
    )
```

---

## Usage Examples

### Storing Memories

```python
from agency_memory import create_firestore_store

# Create Firestore-backed memory store
store = create_firestore_store(collection_name="agency_memories")

# Store a pattern
store.store(
    key="pattern_tdd_success_001",
    content={
        "type": "pattern",
        "description": "Successful TDD implementation",
        "context": "Test-first development approach",
        "success_rate": 0.95
    },
    tags=["pattern", "tdd", "success"]
)
```

### Searching Memories (Tag-Based)

```python
# Search by tags
results = store.search(["pattern", "tdd"])

print(f"Found {results.total_count} patterns:")
for record in results.records:
    print(f"  - {record.key}: {record.content['description']}")
```

### Semantic Search (VectorStore)

```python
from agency_memory import create_enhanced_memory_store

# Create enhanced memory store with VectorStore
enhanced_store = create_enhanced_memory_store(
    embedding_provider="sentence-transformers"
)

# Store memories
enhanced_store.store("ml_pattern", {"content": "Machine learning best practices"}, ["ml"])
enhanced_store.store("ai_pattern", {"content": "Neural network architectures"}, ["ai"])

# Semantic search
results = enhanced_store.semantic_search(
    query="deep learning techniques",
    top_k=5,
    min_similarity=0.5
)

for result in results:
    print(f"Similarity: {result['relevance_score']:.3f} - {result['content']['content']}")
```

---

## Firestore Collections

### Default Collections

- `agency_memories` - Main memory storage (configured in agency.py)
- `agency_persistence_test` - Test collection (used by test scripts)
- `patterns` - Pattern intelligence (future enhancement)

### Collection Structure

Each memory document contains:

```json
{
  "key": "unique_memory_key",
  "content": {
    "type": "pattern|learning|error_resolution",
    "description": "Memory description",
    "context": "Additional context",
    ...
  },
  "tags": ["tag1", "tag2", "tag3"],
  "timestamp": "2025-10-01T02:40:55.593212"
}
```

---

## Troubleshooting

### Error: `google-cloud-firestore not installed`

```bash
# Install in virtual environment
uv pip install google-cloud-firestore
```

### Error: `GOOGLE_APPLICATION_CREDENTIALS not set`

```bash
# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-credentials.json

# Add to .env file
echo "GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-credentials.json" >> .env
```

### Error: `Permission denied` when accessing Firestore

1. Check that service account has **Firestore Admin** role
2. Verify project ID matches credentials file
3. Ensure Firestore is enabled in Firebase Console

### Warnings: `ALTS creds ignored`

This is expected when running outside Google Cloud Platform. The warning is harmless and can be ignored.

### Slow Performance

Firestore queries can be slower than in-memory. Consider:

1. **Indexing**: Create Firestore indexes for frequently queried tags
2. **Caching**: Use in-memory cache for hot data
3. **Batching**: Batch writes for better performance

---

## Production Deployment

### Security Best Practices

1. **Never commit credentials** to version control
   - Add `*firebase-credentials*.json` to `.gitignore`
   - Use environment variables or secret managers

2. **Restrict service account permissions**
   - Grant only necessary Firestore permissions
   - Use separate credentials for dev/staging/prod

3. **Enable Firestore Security Rules**
   ```javascript
   rules_version = '2';
   service cloud.firestore {
     match /databases/{database}/documents {
       match /agency_memories/{document=**} {
         allow read, write: if request.auth != null;  // Authenticated only
       }
     }
   }
   ```

### Performance Optimization

1. **Connection Pooling**: Reuse Firestore client instances
2. **Batch Operations**: Use batch writes for multiple memories
3. **Query Optimization**: Use composite indexes for complex queries
4. **Monitoring**: Enable Firestore metrics in Google Cloud Console

### Cost Optimization

Firestore pricing is based on:
- Document reads/writes/deletes
- Storage (GB-month)
- Network egress

Tips to reduce costs:
1. Use **batched writes** to reduce write operations
2. Implement **TTL policies** to delete old memories
3. Use **query limits** to avoid large result sets
4. Consider **Firestore Lite** for read-heavy workloads

---

## Environment Variable Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | - | Path to Firebase service account JSON |
| `GOOGLE_CLOUD_PROJECT` | Auto-detected | Firebase project ID (optional) |
| `FRESH_USE_FIRESTORE` | `true` | Enable Firestore persistence |
| `USE_ENHANCED_MEMORY` | `true` | Enable VectorStore semantic search |
| `FIRESTORE_EMULATOR_HOST` | - | Use Firestore emulator (development) |

---

## Next Steps

1. **Enable in Production**: Set `FRESH_USE_FIRESTORE=true` in production `.env`
2. **Monitor Usage**: Check Firestore metrics in Google Cloud Console
3. **Optimize Queries**: Create indexes for frequently used tag combinations
4. **Backup Strategy**: Enable Firestore automated backups
5. **Learning Integration**: Enable pattern learning with `PERSIST_PATTERNS=true`

---

## Support

- **Setup Issues**: Run `./scripts/setup_firestore.sh` for diagnostics
- **Test Persistence**: Use `python test_memory_persistence.py`
- **Documentation**: See [Firebase Firestore Docs](https://firebase.google.com/docs/firestore)
- **Agency Docs**: See `constitution.md` Article IV (Continuous Learning)

---

**Version**: 1.0.0
**Last Updated**: 2025-10-01
**Status**: Production Ready ✅
