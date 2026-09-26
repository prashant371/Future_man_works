"""
AI Agent Module

Core conversational agent powered by Google Gemini.
Integrates tool calling, permissions, and task execution.
"""

from uuid import UUID
import logging
from sqlalchemy.ext.asyncio import AsyncSession
import google.generativeai as genai

from app.config import get_settings
from app.tools.registry import get_registry
from app.agent.executor import execute_tool
from google.generativeai.types import content_types

logger = logging.getLogger("agent")
settings = get_settings()

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


SYSTEM_PROMPT = """You are a Personal AI Action Agent — a helpful, professional assistant that helps users interact with their connected platforms (GitHub, LinkedIn, Gmail, Calendar, etc.) through natural language.

## Your Capabilities
- You help users manage their GitHub repositories, issues, branches, and pull requests.
- You understand developer workflows and can suggest efficient approaches.

## Your Behavior
1. **Be concise and clear.** Use short paragraphs, bullet points, and structured output.
2. **Be transparent.** Always tell the user exactly what action you're performing.
3. **Ask for clarification** when a request is ambiguous. Never guess critical parameters like repository names.
4. **Report results accurately.** Never claim success unless the external API confirms it.
5. **Respect confirmation requirements.** For sensitive actions (merge PR, delete resources), if the tool returns a status of 'awaiting_confirmation', inform the user they must confirm the task in the UI.

## Response Format
- Use markdown formatting for readability.
- Use ✓ for completed actions, ⏳ for in-progress or awaiting confirmation, and ✗ for failures.
- Include relevant links when available.

Remember: You are the user's trusted assistant. Be helpful, safe, and transparent."""


class Agent:
    def __init__(self):
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the Gemini model and bind registered tools."""
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set. Agent will not work.")
            return

        registry = get_registry()
        gemini_tools = []

        # Convert ToolDefinition to Gemini tool schema
        for name, tool in registry.list_tools().items():
            properties = {}
            required = []
            for arg in tool.definition.arguments:
                arg_type = arg.type
                if arg_type == "integer":
                    type_str = "integer"
                elif arg_type == "array":
                    type_str = "array"
                elif arg_type == "boolean":
                    type_str = "boolean"
                else:
                    type_str = "string"

                properties[arg.name] = {
                    "type": type_str,
                    "description": arg.description
                }
                if arg.required:
                    required.append(arg.name)

            gemini_tools.append({
                "name": name,
                "description": tool.definition.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            })

        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT,
            tools=gemini_tools if gemini_tools else None,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                max_output_tokens=2048,
            ),
        )

    async def process_message(
        self,
        db: AsyncSession,
        user_id: UUID,
        conversation_id: UUID,
        user_message: str,
        conversation_history: list[dict] | None = None,
        connected_platforms: list[str] | None = None,
    ) -> dict:
        """
        Process a user message, handle tool calls, and generate a response.
        """
        if not self.model:
            return {
                "message": "⚠️ AI agent is not configured. Please set the `GEMINI_API_KEY` in your environment.",
                "status": "error",
            }

        # Build conversation context
        chat_history = []
        if conversation_history:
            for msg in conversation_history:
                # Basic role mapping, Gemini strict about 'user' or 'model'
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})

        context_prefix = f"[Connected platforms: {', '.join(connected_platforms) if connected_platforms else 'None'}]\n\n"
        
        chat = self.model.start_chat(history=chat_history)
        
        try:
            response = chat.send_message(context_prefix + user_message)
            
            # Check if Gemini wants to call a function
            function_calls = [part.function_call for part in response.parts if part.function_call]
            
            if not function_calls:
                return {
                    "message": response.text,
                    "status": "completed",
                }

            # Handle the first function call (can be expanded for parallel calls later)
            fc = function_calls[0]
            tool_name = fc.name
            
            # Extract arguments cleanly
            args = {}
            for key, val in fc.args.items():
                args[key] = val
                
            logger.info(f"Agent requested tool: {tool_name} with args: {args}")

            # Execute tool
            exec_result = await execute_tool(
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
                tool_name=tool_name,
                arguments=args
            )

            # Pass result back to Gemini so it can answer the user
            tool_response_part = content_types.Part.from_function_response(
                name=tool_name,
                response={"result": exec_result.data, "error": exec_result.error, "success": exec_result.success, "message": exec_result.message}
            )
            
            final_response = chat.send_message(tool_response_part)
            
            return {
                "message": final_response.text,
                "status": exec_result.status,
                "task_id": exec_result.task_id,
            }
            
        except Exception as e:
            logger.error(f"Agent Error: {e}", exc_info=True)
            return {
                "message": f"I encountered an error processing your request: {str(e)}",
                "status": "error",
            }


# ── Singleton ─────────────────────────────────────────────────
_agent_instance = None


def get_agent() -> Agent:
    """Get or create the singleton Agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = Agent()
    return _agent_instance
