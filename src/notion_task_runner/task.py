from abc import ABC, abstractmethod
from typing import Any


class Task(ABC):
    """
    Abstract base class for all Notion task runners.

    Implementations of this interface must provide a `run()` method that performs
    a specific task (e.g., updating a Notion page or exporting content).

    The `run()` method should encapsulate the task's full execution logic.
    """

    @abstractmethod
    def run(self) -> Any | None:
        """
        Executes the task logic.

        Returns:
            Any or None: The result of the task, or None if there is nothing to return.
        """
        pass
