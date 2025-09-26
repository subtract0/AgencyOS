"""
Store consolidated learnings in the VectorStore.
"""
from agency_swarm.tools import BaseTool
from pydantic import Field
from agency_memory import VectorStore
import json
from typing import Dict, Any, List
from shared.types.json import JSONValue
from datetime import datetime


class StoreKnowledge(BaseTool):
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
            learning_data = json.loads(self.learning)

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
                learning_objects = learning_data["learning_objects"]
                stored_count = 0

                for learning_obj in learning_objects:
                    if self._store_learning_object(learning_obj, vector_store):
                        stored_count += 1

                return json.dumps({
                    "status": "success",
                    "message": f"Stored {stored_count} learning objects",
                    "stored_count": stored_count,
                    "total_objects": len(learning_objects),
                    "namespace": self.namespace,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)

            else:
                # Single learning object
                if self._store_learning_object(learning_data, vector_store):
                    return json.dumps({
                        "status": "success",
                        "message": "Learning object stored successfully",
                        "learning_id": learning_data.get("learning_id", "unknown"),
                        "namespace": self.namespace,
                        "timestamp": datetime.now().isoformat()
                    }, indent=2)
                else:
                    return json.dumps({
                        "status": "error",
                        "message": "Failed to store learning object"
                    }, indent=2)

        except Exception as e:
            return f"Error in single learning storage: {str(e)}"

    def _store_batch_learnings(self, learning_data: Dict[str, JSONValue], vector_store: VectorStore) -> str:
        """Store multiple learning objects in batch mode."""
        try:
            learning_objects = learning_data.get("learning_objects", [])
            if not learning_objects:
                return json.dumps({"status": "error", "message": "No learning objects found"}, indent=2)

            stored_count = 0
            failed_count = 0
            stored_ids = []

            for learning_obj in learning_objects:
                try:
                    if self._store_learning_object(learning_obj, vector_store):
                        stored_count += 1
                        stored_ids.append(learning_obj.get("learning_id", "unknown"))
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    print(f"Failed to store learning {learning_obj.get('learning_id', 'unknown')}: {e}")

            return json.dumps({
                "status": "success" if stored_count > 0 else "partial_failure",
                "message": f"Batch storage completed: {stored_count} stored, {failed_count} failed",
                "stored_count": stored_count,
                "failed_count": failed_count,
                "stored_ids": stored_ids,
                "namespace": self.namespace,
                "timestamp": datetime.now().isoformat()
            }, indent=2)

        except Exception as e:
            return f"Error in batch learning storage: {str(e)}"

    def _update_existing_learning(self, learning_data: Dict[str, JSONValue], vector_store: VectorStore) -> str:
        """Update an existing learning object."""
        try:
            learning_id = learning_data.get("learning_id")
            if not learning_id:
                return json.dumps({"status": "error", "message": "No learning_id provided for update"}, indent=2)

            # Try to find existing learning
            existing_results = vector_store.search(
                query=learning_id,
                namespace=self.namespace,
                limit=1
            )

            if existing_results:
                # Update existing learning by storing new version
                if self._store_learning_object(learning_data, vector_store, update_mode=True):
                    return json.dumps({
                        "status": "success",
                        "message": f"Learning {learning_id} updated successfully",
                        "learning_id": learning_id,
                        "namespace": self.namespace,
                        "timestamp": datetime.now().isoformat()
                    }, indent=2)
                else:
                    return json.dumps({
                        "status": "error",
                        "message": f"Failed to update learning {learning_id}"
                    }, indent=2)
            else:
                # Learning doesn't exist, store as new
                if self._store_learning_object(learning_data, vector_store):
                    return json.dumps({
                        "status": "success",
                        "message": f"Learning {learning_id} stored as new (original not found)",
                        "learning_id": learning_id,
                        "namespace": self.namespace,
                        "timestamp": datetime.now().isoformat()
                    }, indent=2)
                else:
                    return json.dumps({
                        "status": "error",
                        "message": f"Failed to store learning {learning_id}"
                    }, indent=2)

        except Exception as e:
            return f"Error updating learning: {str(e)}"

    def _store_learning_object(self, learning_obj: Dict[str, JSONValue], vector_store: VectorStore, update_mode: bool = False) -> bool:
        """Store a single learning object in the vector store."""
        try:
            # Generate embedding text from key fields
            embedding_text = self._create_embedding_text(learning_obj)

            # Prepare metadata
            metadata = {
                "learning_id": learning_obj.get("learning_id", "unknown"),
                "type": learning_obj.get("type", "unknown"),
                "category": learning_obj.get("category", "general"),
                "confidence": learning_obj.get("confidence", 0.5),
                "keywords": learning_obj.get("keywords", []),
                "created_timestamp": learning_obj.get("metadata", {}).get("created_timestamp", datetime.now().isoformat()),
                "stored_timestamp": datetime.now().isoformat(),
                "source_session": learning_obj.get("metadata", {}).get("source_session", "unknown"),
                "update_mode": update_mode,
                "namespace": self.namespace,
            }

            memory_key = learning_obj.get("learning_id", f"learning_{datetime.now().timestamp()}")
            namespaced_key = f"{self.namespace}:{memory_key}"
            memory_content = {
                "key": memory_key,
                "namespaced_key": namespaced_key,
                "content": embedding_text,
                "title": learning_obj.get("title", "Untitled Learning"),
                "description": learning_obj.get("description", ""),
                "actionable_insight": learning_obj.get("actionable_insight", ""),
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
        title = learning_obj.get("title", "")
        if title:
            text_parts.append(f"Title: {title}")

        description = learning_obj.get("description", "")
        if description:
            text_parts.append(f"Description: {description}")

        # Add actionable insight
        actionable = learning_obj.get("actionable_insight", "")
        if actionable:
            text_parts.append(f"Actionable Insight: {actionable}")

        # Add keywords
        keywords = learning_obj.get("keywords", [])
        if keywords:
            text_parts.append(f"Keywords: {', '.join(keywords)}")

        # Add type and category for context
        learning_type = learning_obj.get("type", "")
        category = learning_obj.get("category", "")
        if learning_type:
            text_parts.append(f"Type: {learning_type}")
        if category:
            text_parts.append(f"Category: {category}")

        # Add pattern information if available
        patterns = learning_obj.get("patterns", {})
        if patterns:
            triggers = patterns.get("triggers", [])
            actions = patterns.get("actions", [])
            if triggers:
                text_parts.append(f"Triggers: {', '.join(triggers)}")
            if actions:
                text_parts.append(f"Actions: {', '.join(actions)}")

        # Add application criteria
        criteria = learning_obj.get("application_criteria", [])
        if criteria:
            text_parts.append(f"Application Criteria: {', '.join(criteria[:3])}")  # Limit to first 3

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

            stats = {
                "total_learnings": len(all_learnings),
                "types": {},
                "categories": {},
                "average_confidence": 0.0
            }

            if all_learnings:
                total_confidence = 0
                for learning in all_learnings:
                    metadata = learning.get("metadata", {})

                    # Count types
                    learning_type = metadata.get("type", "unknown")
                    stats["types"][learning_type] = stats["types"].get(learning_type, 0) + 1

                    # Count categories
                    category = metadata.get("category", "unknown")
                    stats["categories"][category] = stats["categories"].get(category, 0) + 1

                    # Sum confidence
                    confidence = metadata.get("confidence", 0)
                    total_confidence += confidence

                stats["average_confidence"] = total_confidence / len(all_learnings)

            return stats

        except Exception as e:
            return {"error": f"Failed to get storage stats: {str(e)}"}