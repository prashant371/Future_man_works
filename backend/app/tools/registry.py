"""
Tool Registry

Central registry for all available tools.
The agent queries this registry to understand what actions are available.
New integrations register their tools here.
"""

from typing import Optional
from app.tools.base import BaseTool, ToolDefinition


class ToolRegistry:
    """
    Centralized registry for all platform tools.

    Usage:
        registry = ToolRegistry()
        registry.register(MyGitHubTool())
        tool = registry.get("github_create_issue")
        definitions = registry.get_definitions()
    """

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        name = tool.definition.name
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered.")
        self._tools[name] = tool

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry."""
        self._tools.pop(name, None)

    def get(self, name: str) -> Optional[BaseTool]:
        """Get a tool by name."""
        return self._tools.get(name)

    def get_definitions(self, platform: Optional[str] = None) -> list[ToolDefinition]:
        """
        Get definitions for all registered tools.
        Optionally filter by platform.
        """
        definitions = []
        for tool in self._tools.values():
            if platform is None or tool.definition.platform == platform:
                definitions.append(tool.definition)
        return definitions

    def get_tool_names(self, platform: Optional[str] = None) -> list[str]:
        """Get all registered tool names, optionally filtered by platform."""
        if platform:
            return [
                name for name, tool in self._tools.items()
                if tool.definition.platform == platform
            ]
        return list(self._tools.keys())

    def list_platforms(self) -> list[str]:
        """Get list of all platforms that have registered tools."""
        platforms = set()
        for tool in self._tools.values():
            platforms.add(tool.definition.platform)
        return sorted(platforms)

    @property
    def count(self) -> int:
        return len(self._tools)


# ── Global Registry Singleton ─────────────────────────────────
_registry_instance = None


def get_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ToolRegistry()
        _register_all_tools(_registry_instance)
    return _registry_instance


def _register_all_tools(registry: ToolRegistry) -> None:
    """
    Register all available tools.
    New integrations add their tools here.
    """
    from app.tools.github.tools import register_github_tools
register_github_tools(registry)
