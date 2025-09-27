"""
Store consolidated learnings in the VectorStore.
"""
from agency_swarm.tools import BaseTool
from pydantic import Field
from agency_memory import VectorStore
import json
from typing import Dict, Any, List
from shared.type_definitions.json import JSONValue
from datetime import datetime
from learning_agent.json_utils import (
    is_dict, is_list, is_str, is_int, is_float, is_number, is_none,
    safe_get, safe_get_dict, safe_get_list, safe_get_str, safe_get_int, safe_get_float,
    ensure_dict, ensure_list, ensure_str
)


class StoreKnowledge(BaseTool):  # type: ignore[misc]
    """
    Stores structured learnings in the agency's VectorStore for future retrieval.

    This tool takes consolidated learning objects and stores them in the VectorStore
    with appropriate embeddings and metadata for efficient similarity-based retrieval.
    """

    learning: str = Field(
        ...,
        description="JSON string of consolidated learning object from ConsolidateLearning"
    )
    storage_mode: str = Field(
        default="standard",
        description="Storage mode: 'standard' (single learning), 'batch' (multiple learnings), or 'update' (update existing)"
    )
    namespace: str = Field(
        default="learnings",
        description="Namespace in VectorStore for organizing learnings"
    )

    def run(self) -> str:
        try:
            # Parse the learning data
            parsed_learning = json.loads(self.learning)
            learning_data = ensure_dict(parsed_learning)

            # Initialize VectorStore
            vector_store = VectorStore()

            # Handle different storage modes
            if self.storage_mode == "batch":
                return self._store_batch_learnings(learning_data, vector_store)
            elif self.storage_mode == "update":
                return self._update_existing_learning(learning_data, vector_store)
            else:
                return self._store_single_learning(learning_data, vector_store)

        except Exception as e:
            return f"Error storing knowledge: {str(e)}"

    def _store_single_learning(self, learning_data: Dict[str, JSONValue], vector_store: VectorStore) -> str:
        """Store a single learning object."""
        try:
            # Extract learning objects (handle both single learning and consolidated format)
            if "learning_objects" in learning_data:
                # Consolidated format with multiple learnings
                learning_objects_raw = safe_get_list(learning_data, "learning_objects")
                learning_objects = [ensure_dict(obj) for obj in learning_objects_raw]
                stored_count = 0

                for learning_obj in learning_objects:
                    if self._store_learning_object(learning_obj, vector_store):
                        stored_count += 1

                result: Dict[str, JSONValue] = {
                    "status": "success",
                    "message": f"Stored {stored_count} learning objects",
                    "stored_count": stored_count,
                    "total_objects": len(learning_objects),
                    "namespace": self.namespace,
                    "timestamp": datetime.now().isoformat()
                }
                return json.dumps(result, indent=2)

            else:
                # Single learning object
                if self._store_learning_object(learning_data, vector_store):
                    success_result: Dict[str, JSONValue] = {
                        "status": "success",
                        "message": "Learning object stored successfully",
                        "learning_id": safe_get_str(learning_data, "learning_id", "unknown"),
                        "namespace": self.namespace,
                        "timestamp": datetime.now().isoformat()
                    }
                    return json.dumps(success_result, indent=2)
                else:
                    error_result: Dict[str, JSONValue] = {
                        "status": "error",
                        "message": "Failed to store learning object"
                    }
                    return json.dumps(error_result, indent=2)

        except Exception as e:
            return f"Error in single learning storage: {str(e)}"

    def _store_batch_learnings(self, learning_data: Dict[str, JSONValue], vector_store: VectorStore) -> str:
        """Store multiple learning objects in batch mode."""
        try:
            learning_objects_raw = safe_get_list(learning_data, "learning_objects")
            learning_objects = [ensure_dict(obj) for obj in learning_objects_raw]
            if not learning_objects:
                error_result: Dict[str, JSONValue] = {"status": "error", "message": "No learning objects found"}
                return json.dumps(error_result, indent=2)

            stored_count = 0
            failed_count = 0
            stored_ids: List[JSONValue] = []

            for learning_obj in learning_objects:
                try:
                    if self._store_learning_object(learning_obj, vector_store):
                        stored_count += 1
                        stored_ids.append(safe_get_str(learning_obj, "learning_id", "unknown"))
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    print(f"Failed to store learning {safe_get_str(learning_obj, 'learning_id', 'unknown')}: {e}")

            batch_result: Dict[str, JSONValue] = {
                "status": "success" if stored_count > 0 else "partial_failure",
                "message": f"Batch storage completed: {stored_count} stored, {failed_count} failed",
                "stored_count": stored_count,
                "failed_count": failed_count,
                "stored_ids": stored_ids,
                "namespace": self.namespace,
                "timestamp": datetime.now().isoformat()
            }
            return json.dumps(batch_result, indent=2)

        except Exception as e:
            return f"Error in batch learning storage: {str(e)}"

    def _update_existing_learning(self, learning_data: Dict[str, JSONValue], vector_store: VectorStore) -> str:
        """Update an existing learning object."""
        try:
            learning_id = safe_get_str(learning_data, "learning_id")
            if not learning_id:
                error_result: Dict[str, JSONValue] = {"status": "error", "message": "No learning_id provided for update"}
                return json.dumps(error_result, indent=2)

            # Try to find existing learning
            existing_results = vector_store.search(
                query=learning_id,
                namespace=self.namespace,
                limit=1
            )

            if existing_results:
                # Update existing learning by storing new version
                if self._store_learning_object(learning_data, vector_store, update_mode=True):
                    success_result: Dict[str, JSONValue] = {
                        "status": "success",
                        "message": f"Learning {learning_id} updated successfully",
                        "learning_id": learning_id,
                        "namespace": self.namespace,
                        "timestamp": datetime.now().isoformat()
                    }
                    return json.dumps(success_result, indent=2)
                else:
                    update_error_result: Dict[str, JSONValue] = {
                        "status": "error",
                        "message": f"Failed to update learning {learning_id}"
                    }
                    return json.dumps(update_error_result, indent=2)
            else:
                # Learning doesn't exist, store as new
                if self._store_learning_object(learning_data, vector_store):
                    new_result: Dict[str, JSONValue] = {
                        "status": "success",
                        "message": f"Learning {learning_id} stored as new (original not found)",
                        "learning_id": learning_id,
                        "namespace": self.namespace,
                        "timestamp": datetime.now().isoformat()
                    }
                    return json.dumps(new_result, indent=2)
                else:
                    fail_result: Dict[str, JSONValue] = {
                        "status": "error",
                        "message": f"Failed to store learning {learning_id}"
                    }
                    return json.dumps(fail_result, indent=2)

        except Exception as e:
            return f"Error updating learning: {str(e)}"

    def _store_learning_object(self, learning_obj: Dict[str, JSONValue], vector_store: VectorStore, update_mode: bool = False) -> bool:
        """Store a single learning object in the vector store."""
        try:
            # Generate embedding text from key fields
            embedding_text = self._create_embedding_text(learning_obj)

            # Prepare metadata
            metadata_obj = safe_get_dict(learning_obj, "metadata")
            metadata: Dict[str, JSONValue] = {
                "learning_id": safe_get_str(learning_obj, "learning_id", "unknown"),
                "type": safe_get_str(learning_obj, "type", "unknown"),
                "category": safe_get_str(learning_obj, "category", "general"),
                "confidence": safe_get_float(learning_obj, "confidence", 0.5),
                "keywords": safe_get_list(learning_obj, "keywords"),
                "created_timestamp": safe_get_str(metadata_obj, "created_timestamp", datetime.now().isoformat()),
                "stored_timestamp": datetime.now().isoformat(),
                "source_session": safe_get_str(metadata_obj, "source_session", "unknown"),
                "update_mode": update_mode,
                "namespace": self.namespace,
            }

            memory_key = safe_get_str(learning_obj, "learning_id", f"learning_{datetime.now().timestamp()}")
            namespaced_key = f"{self.namespace}:{memory_key}"
            memory_content: Dict[str, JSONValue] = {
                "key": memory_key,
                "namespaced_key": namespaced_key,
                "content": embedding_text,
                "title": safe_get_str(learning_obj, "title", "Untitled Learning"),
                "description": safe_get_str(learning_obj, "description"),
                "actionable_insight": safe_get_str(learning_obj, "actionable_insight"),
                "metadata": metadata,
                "full_learning_object": learning_obj
            }

            vector_store.add_memory(namespaced_key, memory_content)

            return True

        except Exception as e:
            print(f"Error storing learning object: {e}")
            return False

    def _create_embedding_text(self, learning_obj: Dict[str, JSONValue]) -> str:
        """Create text for embedding generation from learning object."""
        # Combine key textual fields for embedding
        text_parts = []

        # Add title and description
        title = safe_get_str(learning_obj, "title")
        if title:
            text_parts.append(f"Title: {title}")

        description = safe_get_str(learning_obj, "description")
        if description:
            text_parts.append(f"Description: {description}")

        # Add actionable insight
        actionable = safe_get_str(learning_obj, "actionable_insight")
        if actionable:
            text_parts.append(f"Actionable Insight: {actionable}")

        # Add keywords
        keywords = safe_get_list(learning_obj, "keywords")
        if keywords:
            keyword_strs = [ensure_str(kw) for kw in keywords]
            text_parts.append(f"Keywords: {', '.join(keyword_strs)}")

        # Add type and category for context
        learning_type = safe_get_str(learning_obj, "type")
        category = safe_get_str(learning_obj, "category")
        if learning_type:
            text_parts.append(f"Type: {learning_type}")
        if category:
            text_parts.append(f"Category: {category}")

        # Add pattern information if available
        patterns = safe_get_dict(learning_obj, "patterns")
        if patterns:
            triggers = safe_get_list(patterns, "triggers")
            actions = safe_get_list(patterns, "actions")
            if triggers:
                trigger_strs = [ensure_str(t) for t in triggers]
                text_parts.append(f"Triggers: {', '.join(trigger_strs)}")
            if actions:
                action_strs = [ensure_str(a) for a in actions]
                text_parts.append(f"Actions: {', '.join(action_strs)}")

        # Add application criteria
        criteria = safe_get_list(learning_obj, "application_criteria")
        if criteria:
            criteria_strs = [ensure_str(c) for c in criteria[:3]]  # Limit to first 3
            text_parts.append(f"Application Criteria: {', '.join(criteria_strs)}")

        return " | ".join(text_parts)

    def _get_storage_stats(self, vector_store: VectorStore) -> Dict[str, JSONValue]:
        """Get statistics about stored learnings."""
        try:
            # Get all learnings in the namespace
            all_learnings = vector_store.search(
                query="",
                namespace=self.namespace,
                limit=1000  # Large limit to get all
            )

            stats: Dict[str, JSONValue] = {
                "total_learnings": len(all_learnings),
                "types": {},
                "categories": {},
                "average_confidence": 0.0
            }

            if all_learnings:
                total_confidence = 0.0
                types_dict = ensure_dict(stats["types"])
                categories_dict = ensure_dict(stats["categories"])

                for learning in all_learnings:
                    learning_dict = ensure_dict(learning)
                    metadata = safe_get_dict(learning_dict, "metadata")

                    # Count types
                    learning_type = safe_get_str(metadata, "type", "unknown")
                    types_dict[learning_type] = safe_get_int(types_dict, learning_type, 0) + 1

                    # Count categories
                    category = safe_get_str(metadata, "category", "unknown")
                    categories_dict[category] = safe_get_int(categories_dict, category, 0) + 1

                    # Sum confidence
                    confidence = safe_get_float(metadata, "confidence", 0.0)
                    total_confidence += confidence

                stats["types"] = types_dict
                stats["categories"] = categories_dict
                stats["average_confidence"] = total_confidence / len(all_learnings)

            return stats

        except Exception as e:
            error_stats: Dict[str, JSONValue] = {"error": f"Failed to get storage stats: {str(e)}"}
            return error_stats