# Specification: Model Storage and Versioning

**Spec ID**: `spec-006-model-storage`
**Status**: `Draft`
**Author**: PlannerAgent
**Created**: 2025-10-10
**Last Updated**: 2025-10-10
**Parent Spec**: `spec-005-advanced-pattern-recognition.md` (Leap 5)
**Related Plan**: `plan-005-advanced-pattern-recognition.md` (Phase 2, Task 2.2)

---

## Executive Summary

The ModelStorage class provides semantic versioning, serialization, and persistence for ML models in the Leap 5 Advanced Pattern Recognition system. It implements production-grade model lifecycle management with automated versioning, metadata tracking, and secure file permissions.

**Key Innovation**: Symlink-based "latest" routing enables zero-downtime model updates and instant rollback capability, critical for production ML systems.

---

## Goals

### Primary Goals

- **Goal 1**: Implement semantic versioning for ML models (major.minor format: v1.0, v1.1, v2.0)
- **Goal 2**: Serialize models with <2s save time and <1s load time (fast production deployment)
- **Goal 3**: Track model metadata (training date, accuracy, feature schema) for traceability
- **Goal 4**: Enable instant rollback via symlink routing (zero-downtime updates)

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| **Model Save Time** | <2s | Measure joblib.dump() with 30MB model |
| **Model Load Time** | <1s | Measure joblib.load() from disk |
| **Model Size** | <50MB | Check file size after serialization |
| **Metadata Accuracy** | 100% | Validate JSON metadata matches model attributes |
| **File Permissions** | 0600 | Verify owner-only read/write via os.stat() |

---

## Non-Goals

### Explicit Exclusions

- **Non-Goal 1**: Cloud storage integration (S3, GCS) - local disk only for Leap 5
- **Non-Goal 2**: Model compression beyond joblib (no ONNX, TensorRT optimization)
- **Non-Goal 3**: Multi-model serving (load one model at a time, not A/B simultaneously)
- **Non-Goal 4**: Model monitoring/observability (handled by separate dashboard tools)

### Future Considerations

- **Future Enhancement 1**: Cloud backup for model versioning (S3 sync after save)
- **Future Enhancement 2**: Model registry integration (MLflow, Weights & Biases)
- **Future Enhancement 3**: Delta compression for efficient version storage (only changed weights)
- **Future Enhancement 4**: Model signing and checksum validation (security hardening)

---

## User Personas & Journeys

### Primary Personas

#### Persona 1: ML Model Trainer (Training Pipeline)

- **Description**: Automated training pipeline that saves newly trained models
- **Goals**: Fast serialization (<2s), automated versioning, metadata tracking
- **Pain Points**: Manual version numbering, metadata drift, slow saves blocking pipeline
- **Technical Proficiency**: Python training scripts, scikit-learn, joblib

#### Persona 2: ML Inference Engine (Production Classifier)

- **Description**: Real-time classification service that loads models at startup
- **Goals**: Fast loading (<1s), always load latest production model, rollback capability
- **Pain Points**: Stale model references, slow cold starts, no rollback mechanism
- **Technical Proficiency**: Production Python services, lazy loading, caching

#### Persona 3: DevOps Engineer (Model Deployment)

- **Description**: Human operator deploying new models and managing rollbacks
- **Goals**: List available versions, deploy specific version, instant rollback
- **Pain Points**: No version history, manual symlink management, unclear metadata
- **Technical Proficiency**: Bash scripts, file system operations, semantic versioning

### User Journeys

#### Journey 1: Save Trained Model (Primary Use Case)

```
1. Trainer starts with: EnsembleModel trained (RandomForest + GradientBoosting)
2. System needs to: Save model with auto-versioning and metadata
3. System performs:
   - Check existing versions in ~/.agency/models/ (e.g., v1.2 is latest)
   - Auto-increment to v1.3 (minor version, retraining)
   - Serialize model to routing_classifier_v1.3.pkl via joblib.dump()
   - Save metadata to routing_classifier_v1.3.json (accuracy, FN_rate, feature_names)
   - Update routing_classifier_latest.pkl symlink → v1.3
   - Set file permissions to 0600 (owner-only)
4. System achieves:
   - Save time: 1.4s (30MB model)
   - Model size: 32MB (within 50MB target)
   - Version: v1.3 (auto-incremented)
   - Metadata: 100% accurate (training_date, validation_accuracy=0.984, FN_rate=0.018)
```

#### Journey 2: Load Latest Model (Production Use Case)

```
1. Inference engine starts with: Cold start (no model loaded)
2. System needs to: Load latest production model (<1s)
3. System performs:
   - Resolve "latest" → follow routing_classifier_latest.pkl symlink → v1.3
   - Load metadata JSON first (validate feature_names length = 1644)
   - Deserialize model via joblib.load()
   - Validate model schema (check feature count, sklearn version)
   - Cache model in memory (singleton pattern)
4. System achieves:
   - Load time: 0.8s (32MB model)
   - Schema valid: feature_count=1644 ✓
   - Model cached: subsequent loads <10ms (memory lookup)
```

#### Journey 3: Rollback to Previous Version (Debugging Use Case)

```
1. DevOps starts with: Production accuracy dropped (v1.3 has bug)
2. System needs to: Instantly rollback to v1.2 (previous stable version)
3. System performs:
   - List available versions: v1.0, v1.1, v1.2, v1.3
   - View metadata for v1.2 (accuracy=0.982, training_date=2025-10-05)
   - Update routing_classifier_latest.pkl symlink → v1.2
   - No service restart needed (lazy loading re-checks symlink)
4. System achieves:
   - Rollback time: <1s (symlink update)
   - Zero downtime: inference engine auto-reloads on next request
   - Metadata preserved: all versions still available for debugging
```

---

## Acceptance Criteria

### Functional Requirements

#### Component 1: Model Serialization

- **AC-1.1**: Serialize EnsembleModel to .pkl via `joblib.dump(compress=3, protocol=4)`
- **AC-1.2**: Save time <2s for models <50MB (measured with time.perf_counter())
- **AC-1.3**: Model size <50MB after compression (target for fast loading)
- **AC-1.4**: No data loss (load/save roundtrip produces identical model predictions)

#### Component 2: Semantic Versioning

- **AC-2.1**: Version format: `v{major}.{minor}` (e.g., v1.0, v1.1, v2.0)
- **AC-2.2**: First save: v1.0 (initial model)
- **AC-2.3**: Retraining (same feature schema): increment minor (v1.0 → v1.1, v1.5 → v1.6)
- **AC-2.4**: Breaking change (feature schema change): increment major (v1.5 → v2.0, v1.0 → v2.0)
- **AC-2.5**: Auto-increment if version=None (detect latest version, increment minor)

#### Component 3: Metadata Tracking

- **AC-3.1**: Metadata JSON includes:
  - `version`: str (e.g., "v1.0")
  - `training_date`: str (ISO 8601 timestamp)
  - `validation_accuracy`: float (0.0-1.0)
  - `false_negative_rate`: float (0.0-1.0)
  - `feature_count`: int (1644 for Leap 5)
  - `model_size_mb`: float (file size in MB)
  - `sklearn_version`: str (e.g., "1.3.0")
  - `file_path`: str (absolute path to .pkl file)
- **AC-3.2**: Metadata saved alongside model (routing_classifier_v1.0.json)
- **AC-3.3**: Metadata validated on load (feature_count must match current extractor)

#### Component 4: Symlink Routing

- **AC-4.1**: Create `routing_classifier_latest.pkl` symlink → current version
- **AC-4.2**: Update symlink on each save (always points to newest version)
- **AC-4.3**: Symlink target validation (error if target file missing)
- **AC-4.4**: Load with version="latest" follows symlink (production default)

#### Component 5: Security

- **AC-5.1**: File permissions 0600 (owner-only read/write) via `os.chmod(path, 0o600)`
- **AC-5.2**: Validate symlink target (no directory traversal attacks)
- **AC-5.3**: Sanitize version strings (alphanumeric + dots only, no path separators)

### Non-Functional Requirements

#### Performance

- **AC-P.1**: Model save time <2s for 30MB model (joblib.dump with compress=3)
- **AC-P.2**: Model load time <1s from disk (joblib.load, cold cache)
- **AC-P.3**: Metadata load time <10ms (JSON parsing)

#### Quality

- **AC-Q.1**: Result<T,E> pattern for all methods (no exceptions leaked)
- **AC-Q.2**: Type safety: All Pydantic models fully typed (mypy passes)
- **AC-Q.3**: Load/save roundtrip: Model predictions identical after serialize/deserialize

#### Reliability

- **AC-R.1**: Atomic saves (write to temp file, rename on success)
- **AC-R.2**: Rollback on failure (delete partial files, keep previous version)
- **AC-R.3**: Graceful degradation (if symlink broken, error with helpful message)

### Constitutional Compliance

#### Article I: Complete Context Before Action

- **AC-CI.1**: Validate model directory exists before save (create if missing)
- **AC-CI.2**: Load metadata before model (validate schema compatibility)
- **AC-CI.3**: Retry on transient errors (e.g., disk full, permission denied)

#### Article II: 100% Verification and Stability

- **AC-CII.1**: Unit tests: 10+ tests (save, load, versioning, security)
- **AC-CII.2**: Integration tests: 5+ tests (roundtrip, symlink, rollback)
- **AC-CII.3**: Performance tests: Save <2s, load <1s (measured with real 30MB model)

#### Article IV: Continuous Learning

- **AC-CIV.1**: Store model versioning history in VectorStore (for learning extraction)
- **AC-CIV.2**: Log save/load events to telemetry (performance tracking)

#### Article V: Spec-Driven Development

- **AC-CV.1**: Implementation traces to Spec-006 (this document)
- **AC-CV.2**: References Plan-005 Phase 2, Task 2.2 (Model Serialization)

---

## Technical Design

### 5.1 File Structure

**Model Directory**: `~/.agency/models/`

```
~/.agency/models/
├── routing_classifier_v1.0.pkl          # Model binary (30MB)
├── routing_classifier_v1.0.json         # Metadata
├── routing_classifier_v1.1.pkl
├── routing_classifier_v1.1.json
├── routing_classifier_v1.2.pkl
├── routing_classifier_v1.2.json
├── routing_classifier_latest.pkl → routing_classifier_v1.2.pkl  # Symlink
└── tfidf_vocabulary_v1.json             # Shared TF-IDF vocab
```

### 5.2 Data Models

```python
from pydantic import BaseModel, Field
from pathlib import Path
from datetime import datetime

class ModelMetadata(BaseModel):
    """
    Metadata for serialized ML model.

    Stored as JSON alongside .pkl file for fast validation.
    """
    version: str = Field(
        ...,
        pattern=r"^v\d+\.\d+$",
        description="Semantic version (e.g., v1.0, v2.3)"
    )

    training_date: str = Field(
        ...,
        description="ISO 8601 timestamp (e.g., 2025-10-10T14:30:00Z)"
    )

    validation_accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Validation set accuracy (target >98%)"
    )

    false_negative_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Complex tasks misclassified (target <2%)"
    )

    feature_count: int = Field(
        ...,
        eq=1644,
        description="Feature vector dimension (1644 for Leap 5)"
    )

    model_size_mb: float = Field(
        ...,
        ge=0.0,
        le=50.0,
        description="Model file size in MB (target <50MB)"
    )

    sklearn_version: str = Field(
        ...,
        description="Scikit-learn version used for training"
    )

    file_path: Path = Field(
        ...,
        description="Absolute path to .pkl file"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "version": "v1.0",
                "training_date": "2025-10-10T14:30:00Z",
                "validation_accuracy": 0.984,
                "false_negative_rate": 0.018,
                "feature_count": 1644,
                "model_size_mb": 32.4,
                "sklearn_version": "1.3.0",
                "file_path": "/Users/am/.agency/models/routing_classifier_v1.0.pkl"
            }
        }
```

### 5.3 Class Interface

```python
from pathlib import Path
from typing import Optional
from shared.type_definitions.result import Result, Ok, Err
import joblib
import os
import json
import time
import sklearn

class ModelStorage:
    """
    Manage ML model persistence with semantic versioning.

    Features:
    - Semantic versioning (major.minor)
    - Metadata tracking (accuracy, feature schema)
    - Symlink routing (latest → current version)
    - Security (0600 file permissions)

    Constitutional Compliance:
    - Article I: Complete context (metadata validation)
    - Article II: 100% verification (save/load roundtrip)
    - Article IV: Store versioning history
    - Article V: Trace to Spec-006
    """

    MODEL_DIR = Path.home() / ".agency" / "models"
    MODEL_PREFIX = "routing_classifier"
    LATEST_SYMLINK = "routing_classifier_latest.pkl"

    def __init__(self):
        """Initialize ModelStorage with directory creation."""
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)

    def save_model(
        self,
        model: EnsembleModel,
        version: Optional[str] = None,
        breaking_change: bool = False
    ) -> Result[Path, str]:
        """
        Save ensemble model with semantic versioning.

        Args:
            model: Trained EnsembleModel to serialize
            version: Explicit version string (e.g., "v1.0"), or None for auto-increment
            breaking_change: If True, increment major version (feature schema change)

        Returns:
            Result[Path, str]: Path to saved model file, or error message

        Workflow:
        1. Generate version number (auto-increment if version=None)
           - First save: v1.0
           - Retraining (breaking_change=False): v1.0 → v1.1
           - Breaking change (breaking_change=True): v1.5 → v2.0
        2. Serialize model to temp file (atomic write)
        3. Save metadata JSON
        4. Update "latest" symlink
        5. Set file permissions 0600
        6. Return model path

        Performance:
        - Save time: <2s for 30MB model
        - Atomic write: rename on success

        Example:
            >>> storage = ModelStorage()
            >>> result = storage.save_model(ensemble_model)
            >>> result.unwrap()
            Path('/Users/am/.agency/models/routing_classifier_v1.0.pkl')
        """
        try:
            # Step 1: Generate version number
            if version is None:
                version = self._generate_version_number(breaking_change)

            # Validate version format
            if not self._is_valid_version(version):
                return Err(f"Invalid version format: {version}. Expected v{major}.{minor}")

            # Step 2: Create file paths
            model_path = self.MODEL_DIR / f"{self.MODEL_PREFIX}_{version}.pkl"
            metadata_path = self.MODEL_DIR / f"{self.MODEL_PREFIX}_{version}.json"
            temp_model_path = model_path.with_suffix(".pkl.tmp")

            # Step 3: Serialize model to temp file (atomic write)
            start_time = time.perf_counter()
            joblib.dump(
                model.ensemble,
                temp_model_path,
                compress=3,      # gzip compression (level 3)
                protocol=4       # pickle protocol 4 (Python 3.4+)
            )
            save_time = time.perf_counter() - start_time

            # Check save time (Article II: Performance)
            if save_time > 2.0:
                os.remove(temp_model_path)  # Cleanup temp file
                return Err(f"Save time {save_time:.2f}s exceeds 2s target")

            # Step 4: Calculate model size
            model_size_mb = temp_model_path.stat().st_size / (1024 ** 2)

            # Check model size (Article II: Quality)
            if model_size_mb > 50.0:
                os.remove(temp_model_path)  # Cleanup temp file
                return Err(f"Model size {model_size_mb:.1f}MB exceeds 50MB target")

            # Step 5: Create metadata
            metadata = ModelMetadata(
                version=version,
                training_date=model.training_date,
                validation_accuracy=model.validation_accuracy,
                false_negative_rate=model.false_negative_rate,
                feature_count=len(model.feature_names),
                model_size_mb=model_size_mb,
                sklearn_version=sklearn.__version__,
                file_path=model_path
            )

            # Step 6: Save metadata JSON
            with metadata_path.open('w') as f:
                f.write(metadata.json(indent=2))

            # Step 7: Atomic rename (temp → final)
            temp_model_path.rename(model_path)

            # Step 8: Update "latest" symlink
            latest_symlink = self.MODEL_DIR / self.LATEST_SYMLINK
            if latest_symlink.exists() or latest_symlink.is_symlink():
                latest_symlink.unlink()  # Remove old symlink
            latest_symlink.symlink_to(model_path.name)  # Relative symlink

            # Step 9: Set file permissions (0600, owner-only)
            os.chmod(model_path, 0o600)
            os.chmod(metadata_path, 0o600)

            return Ok(model_path)

        except Exception as e:
            # Cleanup temp files on error
            if temp_model_path.exists():
                os.remove(temp_model_path)
            return Err(f"Model save failed: {e}")

    def load_model(
        self,
        version: str = "latest"
    ) -> Result[EnsembleModel, str]:
        """
        Load ensemble model from disk.

        Args:
            version: Model version to load ("latest" or "v1.0")

        Returns:
            Result[EnsembleModel, str]: Loaded model, or error message

        Workflow:
        1. Resolve version ("latest" → follow symlink)
        2. Load metadata JSON (validate schema)
        3. Deserialize model via joblib.load()
        4. Validate feature count (must match current extractor)
        5. Measure load time (<1s requirement)
        6. Return EnsembleModel

        Performance:
        - Load time: <1s from disk
        - Metadata validation: <10ms

        Example:
            >>> storage = ModelStorage()
            >>> result = storage.load_model("latest")
            >>> model = result.unwrap()
            >>> model.validation_accuracy
            0.984
        """
        try:
            # Step 1: Resolve version
            if version == "latest":
                model_path = self._resolve_latest_symlink()
                if model_path.is_err():
                    return model_path  # Propagate error
                model_path = model_path.unwrap()
            else:
                if not self._is_valid_version(version):
                    return Err(f"Invalid version format: {version}")
                model_path = self.MODEL_DIR / f"{self.MODEL_PREFIX}_{version}.pkl"

            # Validate model file exists
            if not model_path.exists():
                return Err(f"Model file not found: {model_path}")

            # Step 2: Load metadata
            metadata_path = model_path.with_suffix(".json")
            if not metadata_path.exists():
                return Err(f"Metadata file not found: {metadata_path}")

            with metadata_path.open('r') as f:
                metadata = ModelMetadata.parse_raw(f.read())

            # Validate feature count (Article II: Schema validation)
            if metadata.feature_count != 1644:
                return Err(
                    f"Feature count mismatch: expected 1644, got {metadata.feature_count}. "
                    "Model was trained with different feature extractor."
                )

            # Step 3: Deserialize model
            start_time = time.perf_counter()
            ensemble = joblib.load(model_path)
            load_time = time.perf_counter() - start_time

            # Check load time (Article II: Performance)
            if load_time > 1.0:
                return Err(f"Load time {load_time:.2f}s exceeds 1s target")

            # Step 4: Reconstruct EnsembleModel
            model = EnsembleModel(
                ensemble=ensemble,
                rf_model=ensemble.estimators_[0],  # Extract RandomForest
                gb_model=ensemble.estimators_[1],  # Extract GradientBoosting
                validation_accuracy=metadata.validation_accuracy,
                false_negative_rate=metadata.false_negative_rate,
                training_date=metadata.training_date,
                feature_names=["feature_" + str(i) for i in range(metadata.feature_count)]  # Reconstruct
            )

            return Ok(model)

        except Exception as e:
            return Err(f"Model load failed: {e}")

    def list_models(self) -> list[ModelMetadata]:
        """
        List all saved models with metadata.

        Returns:
            List of ModelMetadata sorted by version (newest first)

        Example:
            >>> storage = ModelStorage()
            >>> models = storage.list_models()
            >>> models[0].version
            'v1.2'
            >>> models[0].validation_accuracy
            0.984
        """
        metadata_files = self.MODEL_DIR.glob(f"{self.MODEL_PREFIX}_v*.json")
        models = []

        for metadata_path in metadata_files:
            try:
                with metadata_path.open('r') as f:
                    metadata = ModelMetadata.parse_raw(f.read())
                models.append(metadata)
            except Exception as e:
                # Skip invalid metadata files
                continue

        # Sort by version (descending)
        models.sort(key=lambda m: self._parse_version(m.version), reverse=True)
        return models

    def _generate_version_number(self, breaking_change: bool) -> str:
        """
        Generate next semantic version number.

        Logic:
        - First save: v1.0
        - Retraining (breaking_change=False): v1.0 → v1.1
        - Breaking change (breaking_change=True): v1.5 → v2.0

        Args:
            breaking_change: If True, increment major version

        Returns:
            Version string (e.g., "v1.0")
        """
        models = self.list_models()

        if not models:
            return "v1.0"  # First save

        latest_version = models[0].version
        major, minor = self._parse_version(latest_version)

        if breaking_change:
            return f"v{major + 1}.0"  # Increment major, reset minor
        else:
            return f"v{major}.{minor + 1}"  # Increment minor

    def _parse_version(self, version: str) -> tuple[int, int]:
        """Parse version string to (major, minor) tuple."""
        if not version.startswith("v"):
            raise ValueError(f"Invalid version: {version}")
        parts = version[1:].split(".")
        return int(parts[0]), int(parts[1])

    def _is_valid_version(self, version: str) -> bool:
        """Validate version string format (v{major}.{minor})."""
        try:
            self._parse_version(version)
            return True
        except Exception:
            return False

    def _resolve_latest_symlink(self) -> Result[Path, str]:
        """
        Follow "latest" symlink to actual model file.

        Returns:
            Result[Path, str]: Model path, or error if symlink broken
        """
        latest_symlink = self.MODEL_DIR / self.LATEST_SYMLINK

        if not latest_symlink.exists() and not latest_symlink.is_symlink():
            return Err(
                f"Latest symlink not found: {latest_symlink}. "
                "No models have been saved yet."
            )

        if not latest_symlink.exists() and latest_symlink.is_symlink():
            return Err(
                f"Latest symlink is broken: {latest_symlink} → {latest_symlink.readlink()}. "
                "Run 'list_models()' and manually fix symlink."
            )

        return Ok(latest_symlink.resolve())
```

---

## Dependencies & Constraints

### System Dependencies

- **Dependency 1**: `joblib>=1.2.0` - Model serialization (dump/load)
- **Dependency 2**: `scikit-learn>=1.3.0` - Ensemble model (version tracking)
- **Dependency 3**: `pydantic>=2.0.0` - ModelMetadata validation
- **Dependency 4**: Python 3.9+ - pathlib, type hints

### Technical Constraints

- **Constraint 1**: Model size <50MB (fast loading, fits in memory)
- **Constraint 2**: Save time <2s (not blocking training pipeline)
- **Constraint 3**: Load time <1s (production cold start)
- **Constraint 4**: File system: POSIX-compliant (symlinks, 0600 permissions)

### Business Constraints

- **Constraint 1**: Local disk storage only (no cloud costs for Leap 5)
- **Constraint 2**: Semantic versioning immutable (no version overwrite)

---

## Risk Assessment

### High Risk Items

- **Risk 1**: **Symlink not supported on Windows** - *Mitigation*: Document POSIX requirement, provide workaround (copy "latest" instead of symlink)
- **Risk 2**: **Model size exceeds 50MB** - *Mitigation*: Alert on save, suggest feature reduction or increased compression

### Medium Risk Items

- **Risk 3**: **Disk full during save** - *Mitigation*: Atomic write (temp file + rename), cleanup on failure
- **Risk 4**: **Version numbering conflict** (manual intervention) - *Mitigation*: File system lock during save, retry on conflict

### Low Risk Items

- **Risk 5**: **Metadata drift** (JSON out of sync with .pkl) - *Mitigation*: Validate metadata on load, error if mismatch

### Constitutional Risks

- **Constitutional Risk 1**: **Article II violation** (incomplete save) - *Mitigation*: Atomic write, rollback on failure, save time verification

---

## Integration Points

### Component Integration

- **MLModelTrainer** (Phase 2, Task 2.1): Calls `save_model()` after training
- **MLClassifier** (Phase 3, Task 3.1): Calls `load_model("latest")` at startup
- **OnlineLearningPipeline** (Phase 4, Task 4.1): Calls `save_model()` after retraining

### System Integration

- **VectorStore**: Store versioning history for learning extraction (Article IV)
- **Telemetry**: Log save/load events (performance tracking)

---

## Testing Strategy

### Test Categories

- **Unit Tests** (10+ tests): save_model(), load_model(), versioning logic
- **Integration Tests** (5+ tests): save/load roundtrip, symlink routing, rollback
- **Performance Tests** (3+ tests): save <2s, load <1s, metadata <10ms

### Test Data Requirements

- **Test Data 1**: Mock EnsembleModel (30MB serialized size)
- **Test Data 2**: Metadata fixtures (v1.0, v1.1, v2.0)
- **Test Data 3**: Broken symlink scenarios (missing target, permission denied)

### Test Environment Requirements

- **Environment 1**: POSIX file system (symlink support)
- **Environment 2**: Write permissions to ~/.agency/models/
- **Environment 3**: Scikit-learn>=1.3.0, joblib>=1.2.0

---

## Implementation Phases

This specification is part of **Leap 5, Phase 2, Task 2.2** (see Plan-005).

### Phase 2, Task 2.2: Model Serialization & Versioning (4 hours)

**Implementation Checklist**:

- [ ] Create `ModelStorage` class with `save_model()` and `load_model()`
- [ ] Implement semantic versioning logic (`_generate_version_number()`)
- [ ] Add symlink routing (`_resolve_latest_symlink()`)
- [ ] Save metadata JSON alongside .pkl files
- [ ] Set file permissions 0600 (security)
- [ ] Write 10+ unit tests (save, load, versioning, security)
- [ ] Write 5+ integration tests (roundtrip, symlink, rollback)
- [ ] Performance validation (save <2s, load <1s)

**Deliverables**:
- `tools/ml_routing/model_storage.py` (~250 lines)
- `shared/models/ml_routing.py` (+50 lines, ModelMetadata)
- `tests/test_model_storage.py` (15 tests)

**Success Criteria**:
- ✅ Save time <2s for 30MB model
- ✅ Load time <1s from disk
- ✅ Model size <50MB (verified)
- ✅ File permissions 0600 (verified)
- ✅ 15+ tests passing (100% pass rate)

---

## Review & Approval

### Stakeholders

- **Primary Stakeholder**: @am (System Designer)
- **Secondary Stakeholders**: MLModelTrainer, MLClassifier, DevOps team
- **Technical Reviewers**: ChiefArchitect (constitutional compliance), QualityEnforcer (security)

### Review Criteria

- **Completeness**: All core methods specified (save, load, list, versioning)
- **Clarity**: Code examples, docstrings, error messages documented
- **Feasibility**: Joblib serialization achievable with <2s save, <1s load
- **Security**: File permissions 0600, symlink validation
- **Constitutional Compliance**: Articles I, II, IV, V validated

### Approval Status

- [ ] **Stakeholder Approval**: Pending @am review
- [ ] **Technical Approval**: Pending ChiefArchitect constitutional audit
- [ ] **Security Approval**: Pending QualityEnforcer validation (0600 permissions)
- [ ] **Final Approval**: Pending after implementation (Phase 2, Task 2.2)

---

## Appendices

### Appendix A: Glossary

- **Semantic Versioning**: Version numbering scheme (major.minor) where major increments on breaking changes, minor on retraining
- **Symlink**: Symbolic link (file system shortcut) enabling "latest" routing without file copies
- **Atomic Write**: Write to temp file + rename (ensures no partial files on failure)
- **Joblib**: Python library for efficient serialization (especially for NumPy arrays)

### Appendix B: References

- **Parent Spec**: `spec-005-advanced-pattern-recognition.md` (Leap 5)
- **Plan**: `plan-005-advanced-pattern-recognition.md` (Phase 2, Task 2.2)
- **ADR-002**: 100% Verification and Stability (performance requirements)
- **ADR-004**: Continuous Learning (VectorStore versioning history)

### Appendix C: Related Documents

- **Spec-005**: Advanced Pattern Recognition (parent specification)
- **Plan-005**: Leap 5 Implementation Plan (Phase 2: Model Training)
- **Constitution**: Article II (100% verification, performance targets)

---

## Revision History

| Version | Date       | Author         | Changes                                                                |
|---------|------------|----------------|------------------------------------------------------------------------|
| 1.0     | 2025-10-10 | PlannerAgent   | Initial specification for ModelStorage with semantic versioning, metadata tracking, symlink routing |

---

*"From serialization to versioning, from disk to memory."*
