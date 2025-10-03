# Firestore Production Memory - Quick Start

Enable cross-session memory persistence with Google Firestore.

## 🚀 Quick Setup (5 minutes)

### 1. Create Firestore Project
```bash
# Go to: https://console.firebase.google.com
# Create new project or use existing
# Enable Firestore Database (Native mode)
```

### 2. Get Credentials
```bash
# In Firebase Console:
# Project Settings → Service Accounts → Generate New Private Key
# Download JSON file as: firebase-credentials.json
```

### 3. Configure Agency
```bash
# Add to .env:
FRESH_USE_FIRESTORE=true
GOOGLE_APPLICATION_CREDENTIALS=./firebase-credentials.json

# Or set environment variable:
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/firebase-credentials.json"
```

### 4. Verify
```bash
python -c "from agency_memory.firestore_store import FirestoreStore; store = FirestoreStore(); print('✅ Firestore connected!')"
```

## 📊 Benefits

### Cross-Session Continuity
- Memories persist between runs
- Team knowledge sharing
- Accumulated learning over time

### Production Ready
- Google-scale infrastructure
- Automatic backups
- Real-time sync

### Current Setup
```python
# Local-only (default):
USE_ENHANCED_MEMORY=true  # VectorStore in memory

# Production (Firestore):
FRESH_USE_FIRESTORE=true  # Persistent storage
```

## 🔒 Security

### Credentials Management
```bash
# NEVER commit credentials to git
echo "firebase-credentials.json" >> .gitignore
echo ".env" >> .gitignore
```

### Access Control
```javascript
// Firestore rules (in Firebase Console):
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /memories/{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

## 📈 Usage

Once enabled, all memory operations automatically use Firestore:

```python
from shared.agent_context import create_agent_context

context = create_agent_context()

# Store memory (persists to Firestore)
context.store_memory("learning", "New pattern discovered", tags=["agent"])

# Search (queries Firestore)
results = context.search_memories(["pattern"])
```

## 🐛 Troubleshooting

### Connection Issues
```bash
# Test connection:
python -c "
from google.cloud import firestore
db = firestore.Client()
print('✅ Connected to Firestore')
"
```

### Credentials Not Found
```bash
# Verify path:
echo $GOOGLE_APPLICATION_CREDENTIALS
ls -la $GOOGLE_APPLICATION_CREDENTIALS

# Or set in .env:
GOOGLE_APPLICATION_CREDENTIALS=/full/path/to/credentials.json
```

### Permission Denied
```bash
# Check Firestore rules in Firebase Console
# Ensure service account has proper permissions
```

## 📚 More Info

See full documentation: `docs/FIRESTORE_SETUP.md`
