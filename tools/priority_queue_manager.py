"""
Priority queue manager for backlog parsing and task management.

Constitutional compliance:
- Article I: Complete context before action (parse all tasks)
- ADR-008: Strict typing with Pydantic models
- ADR-010: Result pattern for error handling
- Constitutional Law #8: Focused functions under 50 lines
"""
import re
from typing import Literal, cast

from shared.models.priority_task import BacklogError, PriorityTask
from shared.type_definitions.result import Err, Ok, Result


class PriorityQueueManager:
    """
    Manage TOP 20 priority backlog with status tracking.

    Provides parsing, filtering, and status update operations for
    the agency backlog file.
    """

    def parse_backlog(self, content: str) -> Result[list[PriorityTask], BacklogError]:
        """
        Parse backlog Markdown file and extract priority tasks.

        Args:
            content: Raw markdown content of backlog file

        Returns:
            Ok(list[PriorityTask]) if parsed successfully
            Err(BacklogError) if parsing failed
        """
        try:
            task_pattern = self._get_task_pattern()
            matches = task_pattern.finditer(content)

            tasks = []
            for match in matches:
                task_result = self._parse_task_match(match)
                if task_result.is_err():
                    return Err(task_result.unwrap_err())

                tasks.append(task_result.unwrap())

            return Ok(tasks)

        except ValueError as e:
            return Err(BacklogError.validation_error(str(e)))
        except Exception as e:
            return Err(BacklogError.parse_error(str(e)))

    def filter_ready_tasks(self, tasks: list[PriorityTask]) -> list[PriorityTask]:
        """
        Filter tasks by Ready status (exclude Blocked, In Progress, Done).

        Args:
            tasks: List of all priority tasks

        Returns:
            List of tasks with status == "Ready"
        """
        return [task for task in tasks if task.status == "Ready"]

    def _get_task_pattern(self) -> re.Pattern[str]:
        """
        Get compiled regex pattern for task parsing.

        Returns:
            Compiled regex pattern for task sections
        """
        return re.compile(
            r"### Priority #(\d+): (.+?)\n"
            r"- \*\*Status\*\*: (.+?)\n"
            r"- \*\*Value\*\*: (\d+)/10.+?\n"
            r"- \*\*Effort\*\*: (\d+)/10.+?\n"
            r"- \*\*ROI\*\*: ([\d.]+)\n"
            r"- \*\*Command\*\*: `(.+?)`\n"
            r"- \*\*Next Step\*\*: (.+?)(?=\n###|\n\n|$)",
            re.DOTALL,
        )

    def _parse_task_match(self, match: re.Match[str]) -> Result[PriorityTask, BacklogError]:
        """
        Parse a single task from regex match.

        Args:
            match: Regex match object

        Returns:
            Ok(PriorityTask) if valid
            Err(BacklogError) if invalid rank or validation fails
        """
        rank = int(match.group(1))
        description = match.group(2).strip()
        status_str = match.group(3).strip()
        value = int(match.group(4))
        effort = int(match.group(5))
        roi = float(match.group(6))
        command = match.group(7).strip()
        next_step = match.group(8).strip()

        # Validate rank is within 1-20
        if rank < 1 or rank > 20:
            return Err(BacklogError.parse_error(f"Rank {rank} out of range (1-20)"))

        # Create slugified ID from description
        task_id = self._slugify(description)

        # Type-safe status casting (Pydantic validates at runtime)
        status_typed = cast(
            Literal["Ready", "Blocked", "In Progress", "Done"],
            status_str
        )

        # Create PriorityTask (Pydantic validates status field)
        task = PriorityTask(
            rank=rank,
            id=task_id,
            description=description,
            value=value,
            effort=effort,
            roi=roi,
            status=status_typed,  # Type-safe: cast + Pydantic validation
            command=command,
            next_step=next_step,
        )

        return Ok(task)

    def _slugify(self, text: str) -> str:
        """
        Convert text to slug (lowercase, underscores).

        Args:
            text: Human-readable text

        Returns:
            Slugified identifier
        """
        # Convert to lowercase
        slug = text.lower()

        # Replace spaces and special chars with underscores
        slug = re.sub(r"[^a-z0-9]+", "_", slug)

        # Remove leading/trailing underscores
        slug = slug.strip("_")

        return slug
