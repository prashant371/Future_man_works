"""
Base Tool Definition

All platform tools (GitHub, LinkedIn, etc.) inherit from BaseTool.
This provides a consistent interface for the agent executor.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel


class RiskLevel(str, Enum):
    """Risk classification for tool actions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolArgument(BaseModel):
    """Definition of a single tool argument."""
    name: str
    description: str
    type: str = "string"
    required: bool = True
    default: Any = None


class ToolDefinition(BaseModel):
    """
    Complete definition of a tool.
    This is what the agent sees when choosing which tool to call.
    """
    name: str
    description: str
    platform: str
    risk_level: RiskLevel
    confirmation_required: bool = False
    arguments: list[ToolArgument] = []
    required_scopes: list[str] = []


class ToolResult(BaseModel):
    """Result returned after a tool executes."""
    success: bool
    data: Optional[dict] = None
    message: str = ""
    error: Optional[str] = None
    url: Optional[str] = None  # Link to the created/modified resource


class BaseTool(ABC):
    """
    Abstract base class for all platform tools.

    Every tool must define:
    - definition: ToolDefinition with metadata
    - execute(): The actual API call logic
    """

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Return the tool's definition (name, args, risk, etc.)."""
        ...

    @abstractmethod
    async def execute(self, arguments: dict, access_token: str) -> ToolResult:
        """
        Execute the tool action.

        Args:
            arguments: Validated arguments dict.
            access_token: The user's OAuth token for the platform.

        Returns:
            ToolResult with success/failure and data.
        """
        ...

    def validate_arguments(self, arguments: dict) -> tuple[bool, str]:
        """
        Validate that all required arguments are present.
        Returns (is_valid, error_message).
        """
        for arg in self.definition.arguments:
            if arg.required and arg.name not in arguments:
                return False, f"Missing required argument: {arg.name}"
        return True, ""
